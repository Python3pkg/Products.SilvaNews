# Copyright (c) 2002-2006 Infrae. All rights reserved.
# See also LICENSE.txt
# $Revision: 1.34 $

from zope.interface import implements

from AccessControl import ClassSecurityInfo
from Globals import InitializeClass
from Products.PageTemplates.PageTemplateFile import PageTemplateFile
from OFS import Folder

from Products.Silva.interfaces import IContent
from Products.Silva import SilvaPermissions
from Products.Silva.Content import Content
from Products.SilvaDocument.Document import Document
from Products.Silva.helpers import add_and_edit
from Products.Silva import mangle

from Products.SilvaNews.interfaces import INewsViewer

try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO

icon = 'www/news_viewer.png'
addable_priority = 3.1

class XMLBuffer:
    """Small file-like object for XML output.
    
    Implicitly converts unicode to UTF-8 and replaces characters to 
    entities when required
    """

    def __init__(self):
        self._buffer = []

    def write(self, data):
        if type(data) != type(u''):
            data = unicode(str(data))
        self._buffer.append(data)
        
    def read(self):
        """The semantics are different from the plain file interface's read!
            
        This will return the full buffer always, and won't move the 
        pointer
        """
        ret = ''.join(self._buffer)
        ret = self._convert(ret)
        return ret

    def _convert(self, data):
        """Convert data to UTF-8.
        """
        data = data.encode('UTF-8')
        return data

def quote_xml ( data ):
    """Quote string for XML usage.
    """
    if not data:
        return data
    data = data.replace('&', '&amp;')
    data = data.replace('"', '&quot;')
    data = data.replace('<', '&lt;')
    data = data.replace('>', '&gt;')
    return data


RDF_HEADER = ('<?xml version="1.0" encoding="UTF-8" ?>\n' 
              '<rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#" '
              'xmlns:silvanews="http://infrae.com/namespaces/silvanews" '
              'xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns="http://purl.org/rss/1.0/">\n')

class NewsViewer(Content, Folder.Folder):
    """Used to show news items on a Silva site.

    When setting up a newsviewer you can choose which news- or
    agendafilters it should use to retrieve the items, and how far
    back in time it should go. The items will then be automatically
    fetched via the filter for each page request.
    """

    meta_type = 'Silva News Viewer'

    security = ClassSecurityInfo()

    implements(IContent, INewsViewer)

    def __init__(self, id):
        NewsViewer.inheritedAttribute('__init__')(self, id, 'dummy')
        self._number_to_show = 25
        self._number_to_show_archive = 10
        self._number_is_days = 0
        self._filters = []

    # ACCESSORS

    security.declareProtected(SilvaPermissions.AccessContentsInformation,
                              'number_to_show')
    def number_to_show(self):
        """Returns number of items to show
        """
        return self._number_to_show

    security.declareProtected(SilvaPermissions.AccessContentsInformation,
                                'number_to_show_archive')
    def number_to_show_archive(self):
        """returns the number of items to show per page in the archive"""
        return self._number_to_show_archive

    security.declareProtected(SilvaPermissions.AccessContentsInformation,
                              'is_published')
    def is_published(self):
        """Returns 1 so the object will be shown in TOCs and such"""
        return 1

    security.declareProtected(SilvaPermissions.AccessContentsInformation,
                              'is_deletable')
    def is_deletable(self):
        """return 1 so this object can always be deleted"""
        return 1

    security.declareProtected(SilvaPermissions.AccessContentsInformation,
                              'can_set_title')
    def can_set_title(self):
        """return 1 so the title can be set"""
        return 1
        
    security.declareProtected(SilvaPermissions.AccessContentsInformation,
                              'number_is_days')
    def number_is_days(self):
        """
        Returns the value of number_is_days (which controls whether
        the filter should show <n> items or items of <n> days back)
        """
        return self._number_is_days

    security.declareProtected(SilvaPermissions.AccessContentsInformation,
                              'filters')
    def filters(self):
        """Returns a list of (the path to) all filters of this object
        """
        self.verify_filters()
        return self._filters

    security.declareProtected(SilvaPermissions.AccessContentsInformation,
                              'findfilters')
    def findfilters(self):
        """Returns a list of paths to all filters
        """
        # Happened through searching in the catalog, but must happen through aquisition now...
        #query = {'meta_type': 'Silva NewsFilter', 'path': '/'.join(self.aq_inner.aq_parent.getPhysicalPath())}
        #results = self.service_catalog(query)
        filters = [str(pair[1]) for pair in self.findfilters_pairs()]
        return filters

    security.declareProtected(SilvaPermissions.AccessContentsInformation,
                              'findfilters_pairs')
    def findfilters_pairs(self):
        """Returns a list of tuples (title (path), path) for all filters
        from catalog for rendering formulator-items
        """
        # IS THIS THE MOST EFFICIENT WAY?
        pairs = []
        obj = self.aq_inner
        while 1:
            parent = obj.aq_parent
            parentpath = parent.getPhysicalPath()
            for item in parent.objectValues(['Silva News Filter',
                                             'Silva Agenda Filter']):
                joinedpath = '/'.join(item.getPhysicalPath())
                pairs.append(('%s (<a href="%s/edit">%s</a>)' %
                              (item.get_title(), joinedpath, joinedpath),
                              joinedpath))
            if parent.meta_type == 'Silva Root':
                break
            obj = parent

        return pairs

    def verify_filters(self):
        allowed_filters = self.findfilters()
        for newsfilter in self._filters:
            if newsfilter not in allowed_filters:
                self._filters.remove(newsfilter)
                self._p_changed = 1

    security.declareProtected(SilvaPermissions.AccessContentsInformation,
                              'get_items')
    def get_items(self):
        """Gets the items from the filters
        """
        self.verify_filters()
        results = []
        for newsfilter in self._filters:
            obj = self.aq_inner.restrictedTraverse(newsfilter)
            res = obj.get_last_items(self._number_to_show,
                                     self._number_is_days)
            results += res

        results = self._remove_doubles(results)
        if not self._number_is_days:
            return results[:self._number_to_show]
        return results

    security.declareProtected(SilvaPermissions.AccessContentsInformation,
                              'get_items_by_date')
    def get_items_by_date(self, month, year):
        """Gets the items from the filters
        """
        self.verify_filters()
        results = []
        for newsfilter in self._filters:
            obj = self.aq_inner.restrictedTraverse(newsfilter)
            res = obj.get_items_by_date(month, year)
            results += res

        results = self._remove_doubles(results)
        return results

    security.declareProtected(SilvaPermissions.AccessContentsInformation,
                              'search_items')
    def search_items(self, keywords):
        """Search the items in the filters
        """
        self.verify_filters()
        results = []
        for newsfilter in self._filters:
            obj = self.aq_inner.restrictedTraverse(newsfilter)
            res = obj.search_items(keywords)
            results += res

        results = self._remove_doubles(results)
        return results

    def _remove_doubles(self, resultlist):
        """Removes double items from a resultset from a ZCatalog-query
        (useful when the resultset is built out of more than 1 query)
        """
        retval = []
        paths = []
        for item in resultlist:
            if not item.getPath() in paths:
                paths.append(item.getPath())
                retval.append(item)
        return retval

    security.declareProtected(SilvaPermissions.AccessContentsInformation,
                              'rss')
    def rss(self, REQUEST=None):
        """Return the contents of this viewer as an RSS/RDF (RSS 1.0) feed"""
        if REQUEST is not None:
            REQUEST.RESPONSE.setHeader('Content-Type', 'text/xml;charset=UTF-8')
        # get the newest items
        items = self.get_items()
        
        # create RDF/XML for the channel
        xml = XMLBuffer()
        xml.write(RDF_HEADER)

        # get the metadata binding to get the metadata for this viewer
        mdbinding = self.service_metadata.getMetadata(self)
        creationdate = mdbinding.get('silva-extra', 'creationtime')
        
        # create RDF/XML frame
        xml.write('<channel rdf:about="%s">\n' % self.absolute_url())
        xml.write('<title>%s</title>\n' % quote_xml(self.get_title()))
        xml.write('<link>%s</link>\n' % self.absolute_url())
        xml.write('<description>%s</description>\n' %
            quote_xml(mdbinding.get('silva-extra', 'content_description')))
        xml.write('<dc:creator>%s</dc:creator>\n' %
            quote_xml(mdbinding.get('silva-extra', 'creator')))
        date = creationdate.HTML4()
        xml.write('<dc:date>%s</dc:date>\n' % quote_xml(date))

        # output <items> list
        # and store items in a list for later use
        itemlist = []
        xml.write('<items>\n<rdf:Seq>\n')
        for item in items:
            item = item.getObject()
	    itemlist.append(item)
	    url = item.object().absolute_url()
	    xml.write('<rdf:li rdf:resource="%s" />\n' % url)
        xml.write('</rdf:Seq>\n</items>\n')
        xml.write('</channel>\n\n')
        # loop over the itemslist and create the RSS/RDF item elements
        for item in itemlist:
            self._rss_item_helper(item, xml)
        # DONE return XML
        xml.write('</rdf:RDF>\n')
        return xml.read()

    def _rss_item_helper(self, item, xml):
        """convert a single Silva object to an RSS/RDF 'hasitem' element"""
        version_container = item.object()
        xml.write('<item rdf:about="%s">\n' % version_container.absolute_url())
        mdbinding = self.service_metadata.getMetadata(item)
        # RSS elements
        xml.write('<title>%s</title>\n' % quote_xml(item.get_title()))
        xml.write('<link>%s</link>\n' % quote_xml(version_container.absolute_url()))
        # an ugly hack to make sure 'model' is available when get_intro()
        # is called. Apparently it looks for this somewhere..
        self.REQUEST.model = item
        xml.write('<description>%s</description>\n' %
                  quote_xml(item.get_intro()))
        # DC elements
        xml.write('<dc:subject>%s</dc:subject>\n' % 
                  quote_xml(mdbinding.get('silva-extra', 'subject')))
        xml.write('<dc:creator>%s</dc:creator>\n' %
                  quote_xml(mdbinding.get('silva-extra', 'creator')))
        xml.write('<dc:date>%s</dc:date>\n' %
                  quote_xml(mdbinding.get('silva-extra', 'creationtime').HTML4()))
                  
        # SilvaNews specific elements
        if hasattr(item, 'location'):
            xml.write('<silvanews:location>%s</silvanews:location>\n' %
                  quote_xml(item.location()))

        if hasattr(item, 'start_datetime'):
            xml.write('<silvanews:startdt>%s</silvanews:startdt>\n' %
                  quote_xml(item.start_datetime().HTML4()))

        if hasattr(item, 'end_datetime'):
            edt = item.end_datetime()
            if edt:
                xml.write('<silvanews:enddt>%s</silvanews:enddt>\n' %
                    quote_xml(item.end_datetime().HTML4()))

        xml.write('</item>\n')
        return


    # MANIPULATORS

    security.declareProtected(SilvaPermissions.ChangeSilvaContent,
                              'set_number_to_show')
    def set_number_to_show(self, number):
        """Sets the number of items to show
        """
        self._number_to_show = number

    security.declareProtected(SilvaPermissions.ChangeSilvaContent,
                                'set_number_to_show_archive')
    def set_number_to_show_archive(self, number):
        """set self._number_to_show_archive"""
        self._number_to_show_archive = number

    security.declareProtected(SilvaPermissions.ChangeSilvaContent,
                              'set_number_is_days')
    def set_number_is_days(self, onoff):
        """Sets the number of items to show
        """
        self._number_is_days = int(onoff)

    security.declareProtected(SilvaPermissions.ChangeSilvaContent,
                              'set_filter')
    def set_filter(self, newsfilter, on_or_off):
        """Adds or removes a filter from the list of filters
        """
        self.verify_filters()
        if on_or_off:
            if not newsfilter in self._filters:
                self._filters.append(newsfilter)
        else:
            if newsfilter in self._filters:
                self._filters.remove(newsfilter)

InitializeClass(NewsViewer)

manage_addNewsViewerForm = PageTemplateFile(
    "www/newsViewerAdd", globals(),
    __name__='manage_addNewsViewerForm')

def manage_addNewsViewer(self, id, title, REQUEST=None):
    """Add a News NewsViewer."""
    if not mangle.Id(self, id).isValid():
        return
    object = NewsViewer(id)
    self._setObject(id, object)
    object = getattr(self, id)
    object.set_title(title)
    add_and_edit(self, id, REQUEST)
    return ''

# Copyright (c) 2002 Infrae. All rights reserved.
# See also LICENSE.txt
# $Revision: 1.12.2.4 $

from AccessControl import ClassSecurityInfo
from Globals import InitializeClass
from Products.PageTemplates.PageTemplateFile import PageTemplateFile
from DateTime import DateTime
import Acquisition

from Products.Silva.interfaces import IContent
from Products.Silva import SilvaPermissions
from Products.Silva.Content import Content
from Products.SilvaDocument.Document import Document
from Products.Silva.helpers import add_and_edit
from Products.Silva import mangle

from Products.SilvaNews.NewsViewer import NewsViewer
from Products.SilvaNews.NewsViewer import XMLBuffer, quote_xml, RDF_HEADER

import feedparser

icon = 'www/rss_viewer.png'
addable_priority = 3.6

class RSSViewer(NewsViewer):
    """A viewer for (external) RSS streams. 
    """

    security = ClassSecurityInfo()

    __implements__ = IContent

    meta_type = 'Silva RSS Viewer'

    def __init__(self, id):
        RSSViewer.inheritedAttribute('__init__')(self, id)
        self._rss_feed = ''
        self._rss_last_modified = ''
        self._caching_period = 30 # in seconds, 0 means don't cache


    # MANIPULATORS

    security.declareProtected(SilvaPermissions.ChangeSilvaContent,
                              'set_rss_feed')
    def set_rss_feed(self, url):
        """Sets the URL for the RSS feed to use"""
        self._rss_feed = url
        self._rss_last_modified = ''



    # ACCESSORS

    security.declareProtected(SilvaPermissions.AccessContentsInformation,
                              'get_channel')
    def get_channel(self):
        """Gets the data from the RSS feed
        """
        if self._rss_feed:
            res = feedparser.parse(self._rss_feed)
        else:
            raise Exception, 'Please choose a feed first!'

        return res

    security.declareProtected(SilvaPermissions.AccessContentsInformation,
                              'rss_feed')
    def rss_feed(self):
        """Returns the URL of the RSS feed"""
        return self._rss_feed


    def rss(self, REQUEST=None):
        """return the contents of this viewer as an RSS/RDF (RSS 1.0) feed"""
        if REQUEST is not None:
            REQUEST.RESPONSE.setHeader('Content-Type', 'text/xml;charset=UTF-8')
        
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
	# and store items in a list
	itemlist = self.get_channel()['items']
	xml.write('<items>\n<rdf:Seq>\n')
        for item in itemlist:
	    url = quote_xml(item['link'])
	    xml.write('<rdf:li rdf:resource="%s" />\n' % url)
	xml.write('</rdf:Seq>\n</items>\n')
        xml.write('</channel>\n\n')
        # loop over the itemslist and create a RSS/RDF item elements
        for item in itemlist:
            self._rss_item_helper(item, xml)
        # DONE
        xml.write('</rdf:RDF>\n')
        # return XML
        return xml.read()

    def _rss_item_helper(self, item, xml):
        """convert a single item (dict) to an RSS/RDF 'item' element"""
        url = quote_xml(item['link'])
        xml.write('<item rdf:about="%s">\n' % url)
        # RSS elements
        xml.write('<title>%s</title>\n' % quote_xml(item['title']))
        xml.write('<link>%s</link>\n' % url)
        try:
            xml.write('<description>%s</description>\n' %
                      quote_xml(item['description']))
        except KeyError:
            pass
        xml.write('</item>\n')

InitializeClass(RSSViewer)

manage_addRSSViewerForm = PageTemplateFile(
    "www/rssViewerAdd", globals(),
    __name__='manage_addRSSViewerForm')

def manage_addRSSViewer(self, id, title, REQUEST=None):
    """Add a News RSSViewer."""
    if not mangle.Id(self, id).isValid():
        return
    object = RSSViewer(id)
    self._setObject(id, object)
    object = getattr(self, id)
    object.set_title(title)
    add_and_edit(self, id, REQUEST)
    return ''

# Copyright (c) 2002 Infrae. All rights reserved.
# See also LICENSE.txt
# $Revision: 1.26.2.2 $

from OFS import SimpleItem
from AccessControl import ClassSecurityInfo
from Globals import InitializeClass
from Products.PageTemplates.PageTemplateFile import PageTemplateFile
from DateTime import DateTime
import OFS
# Silva
import Products.Silva.SilvaPermissions as SilvaPermissions
from Products.SilvaViews.ViewRegistry import ViewAttribute
# misc
from Products.Silva.helpers import add_and_edit
from Products.Silva import mangle

from Filter import Filter, MetaTypeException
from interfaces import INewsItemVersion, INewsFilter, IAgendaItemVersion

icon = 'www/news_filter.png'
addable_priority = 3.2

class NewsFilter(Filter):
    """To enable editors to channel newsitems on a site, all items
        are passed from NewsFolder to NewsViewer through filters. On a filter
        you can choose which NewsFolders you want to channel items for and
        filter the items on several criteria (as well as individually). Also
        NewsFilters can be set up to forward their items to other systems
        as an RSS stream (RSS version 0.91).
    """
    security = ClassSecurityInfo()

    meta_type = "Silva News Filter"

    search = ViewAttribute('public', 'index_html')

    #__implements__ = INewsFilter

    def __init__(self, id):
        NewsFilter.inheritedAttribute('__init__')(self, id)
        self._show_agenda_items = 0
        self._rss_description = ''
        self._allow_rss_export = 0
        self._rss_link = ''
        self._rss_copyright = ''
        self._allow_rss_search = 0
        self._rss_search_description = ''
        self._rss_image = ''

    # ACCESSORS

    def _prepare_query ( self, meta_types ):
        """private method preparing the common fields for a catalog query.

        Return: dict holding the query parameters
        """
        self.verify_sources()
        self.verify_excluded_items()
        query = {}
        query['path'] = self._sources
        query['version_status'] = 'public'
        query['subjects'] = {'query': self._subjects,
                                'operator': 'or'}
        query['target_audiences'] = {'query': self._target_audiences,
                                        'operator': 'or'}
        if meta_types:
            # query meta_type only if it was set initially
            query['meta_type'] = meta_types
        # Workaround for ProxyIndex bug
        query['sort_on'] = 'silva-extrapublicationtime'
        query['sort_order'] = 'descending'
        return query

    security.declareProtected(SilvaPermissions.AccessContentsInformation,
                              'get_all_items')
    def get_all_items(self, meta_types=None):
        """
        Returns all items available to this filter. This function will
        probably only be used in the back-end, but nevertheless has
        AccessContentsInformation-security because it does not reveal
        any 'secret' information...
        """
        query = self._prepare_query(meta_types)
        if not self._sources:
            return []
        results = self.service_catalog(query)
        return results

    security.declareProtected(SilvaPermissions.AccessContentsInformation,
                              'get_last_items')
    def get_last_items(self, number, number_is_days=0, meta_types=None):
        """Returns the last self._number_to_show published items
        """
        query = self._prepare_query(meta_types)
        if not self._sources:
            return []
        if number_is_days:
            # the number specified must be used to restrict the on number of days instead of the number of items
            now = DateTime()
            last_night = DateTime(now.strftime("%Y/%m/%d"))
            query['silva-extrapublicationtime'] = {'query': [last_night - number, now],
                                                    'range': 'minmax'}
        result = self.service_catalog(query)
        filtered_result = [r for r in result if not r.object_path in self._excluded_items]
        if not number_is_days:
            # ouch...
##             for i in range(len(filtered_result)):
##                 if i < number:
##                     output.append(filtered_result[i])
##                 else:
##                     break
            # did you mean:
            output = filtered_result[:number]
        else:
            output = filtered_result
        return output

    security.declareProtected(SilvaPermissions.AccessContentsInformation,
                              'get_next_items')
    def get_next_items(self, numdays, meta_types=None):
        """
        Returns the next <number> AGENDAitems, called by AgendaViewer
        only and should return items that conform to the
        AgendaItem-interface (IAgendaItemVersion), although it will in
        any way because it requres start_datetime to be set. The
        NewsViewer uses only get_last_items.
        """
        date = DateTime()
        lastnight = DateTime(date.year(), date.month(), date.day(), 0, 0, 0)
        enddate = lastnight + numdays
        query = self._prepare_query(meta_types)
        if not self._sources:
            return []
        query['start_datetime'] = (lastnight, enddate)
        query['start_datetime_usage'] = 'range:min:max'
        result = self.service_catalog(query)

        return [r for r in result if not r.object_path in self._excluded_items]

    security.declareProtected(SilvaPermissions.AccessContentsInformation,
                              'get_items_by_date')
    def get_items_by_date(self, month, year, meta_types=None):
        """Returns the last self._number_to_show published items
        """
        month = int(month)
        year = int(year)
        startdate = DateTime(year, month, 1)
        endmonth = month + 1
        if month == 12:
            endmonth = 1
            year = year + 1
        enddate = DateTime(year, endmonth, 1)
        query = self._prepare_query(meta_types)
        if not self._sources:
            return []
        query['silva-extrapublicationtime'] = {'query': (startdate, enddate),
                                               'range': 'minmax'}
        result = self.service_catalog(query)

        return [r for r in result if not r.object_path in
                self._excluded_items]

    security.declareProtected(SilvaPermissions.AccessContentsInformation,
                              'get_agenda_items_by_date')
    def get_agenda_items_by_date(self, month, year, meta_types=None):
        """
        Returns non-excluded published AGENDA-items for a particular
        month. This method is for exclusive use by AgendaViewers only,
        NewsViewers should use get_items_by_date instead (which
        filters on silva-extrapublicationtime instead of start_datetime and
        returns all objects instead of only IAgendaItem-
        implementations)
        """
        month = int(month)
        year = int(year)
        startdate = DateTime(year, month, 1)
        endmonth = month + 1
        if month >= 12:
            endmonth = 1
            year = year + 1
        enddate = DateTime(year, endmonth, 1)

        query = self._prepare_query(meta_types)
        if not self._sources:
            return []
        query['start_datetime'] = [startdate, enddate]
        query['start_datetime_usage'] = 'range:min:max'
        result = self.service_catalog(query)

        return [r for r in result if not r.object_path in self._excluded_items]

    security.declareProtected(SilvaPermissions.AccessContentsInformation,
                              'show_agenda_items')
    def show_agenda_items(self):
        return self._show_agenda_items

    security.declareProtected(SilvaPermissions.AccessContentsInformation,
                              'rss_description')
    def rss_description(self):
        """Returns the description"""
        return self._rss_description

    security.declareProtected(SilvaPermissions.AccessContentsInformation,
                              'allow_rss_export')
    def allow_rss_export(self):
        """Returns true if the filter allows RSS export"""
        return self._allow_rss_export

    security.declareProtected(SilvaPermissions.AccessContentsInformation,
                              'allow_rss_search')
    def allow_rss_search(self):
        """Returns true if searching through RSS is allowed"""
        return self._allow_rss_search

    security.declareProtected(SilvaPermissions.AccessContentsInformation,
                              'rss_search_description')
    def rss_search_description(self):
        """Returns RSS search description"""
        return self._rss_search_description

    security.declareProtected(SilvaPermissions.AccessContentsInformation,
                              'rss_link')
    def rss_link(self):
        """Returns the link to be used as the 'link' tag value for the
        RSS feed"""

        return self._rss_link

    security.declareProtected(SilvaPermissions.AccessContentsInformation,
                              'rss_copyright')
    def rss_copyright(self):
        """Returns the copyright notice to be used for the RSS feed"""
        return self._rss_copyright

    security.declareProtected(SilvaPermissions.AccessContentsInformation,
                              'rss_image')
    def rss_image(self):
        """Returns the image to be used for the RSS feed"""
        return self._rss_image

    security.declarePrivate('get_allowed_meta_types')
    def get_allowed_meta_types(self):
        """Returns the allowed meta_types for this filter"""
        allowed = []
        mts = self.get_root().filtered_meta_types()
        for mt in mts:
            if mt.has_key('instance'):
                if ((self._show_agenda_items and 
                            IAgendaItemVersion.isImplementedByInstancesOf(mt['instance'])) 
                        or (INewsItemVersion.isImplementedByInstancesOf(mt['instance']) and not
                            IAgendaItemVersion.isImplementedByInstancesOf(mt['instance']))):
                    allowed.append(mt['name'])
        return allowed

    security.declarePublic('rss_feed')
    def rss_feed(self):
        """Returns the top 15 records as an RSS feed (RSS version 0.91)"""
        if not self.allow_rss_export():
            raise Exception, 'RSS export not allowed!'
        feed = '<?xml version="1.0" encoding="UTF-8" ?>\n'\
                '<!DOCTYPE rss PUBLIC "-//Netscape Communications//DTD RSS 0.91//EN" "http://my.netscape.com/publish/ formats/rss-0.91.dtd">\n'\
                '<rss version="0.91" encoding="UTF-8">\n'\
                '<channel>\n'\
                '<title>' + self._xml_preformat(self.get_title()) + '</title>\n'\
                '<description>' + self._xml_preformat(self.rss_description()) + '</description>\n'\
                '<link>' + (self._xml_preformat(self.rss_link()) or self._xml_preformat(self.get_publication().absolute_url())) + '</link>\n'\
                '<language>en-us</language>\n'

        if self.rss_copyright():
            feed += '<copyright>' + self._xml_preformat(self.rss_copyright()) + '</copyright>\n'

        feed += '\n'

        if self.rss_image():
            imageobj = self.restrictedTraverse(self.rss_image())
            feed += '<image>\n'\
                    '<title>' + self._xml_preformat(imageobj.get_title()) + '</title>\n'\
                    '<url>' + self._xml_preformat(imageobj.absolute_url()) + '/image</url>\n'\
                    '<link>' + self._xml_preformat(self.rss_image()) + '</link>\n'\
                    '</image>\n\n'

        last = self.get_last_items(15, 0)
        for item in last:
            item = item.getObject()
            # add the start date to the title if the item is an agendaitem
            title = item.get_title()
            if IAgendaItemVersion.isImplementedBy(item):
                title += ' (will take place %s)' % item.start_datetime().toZone('GMT').rfc822()
            # chop the last bit off lead if it's too large
            lead = item.lead()
            if len(lead) > 256:
                lead = lead[:256]
                if lead.find(' ') > -1:
                    lead = lead[:lead.rfind(' ')]
                lead += '...'
            feed += '<item>\n'\
                    '<title>' + self._xml_preformat(title) + '</title>\n'\
                    '<link>' + self._xml_preformat(item.absolute_url()) + '</link>\n'\
                    '<description>' + self._xml_preformat(lead) + '</description>\n'\
                    '</item>\n\n'

        if self.allow_rss_search():
            feed += '<textinput>\n'\
                    '<title>Search</title>\n'\
                    '<name>query</name>\n'\
                    '<description>' + self._xml_preformat(self.rss_search_description()) + '</description>\n'\
                    '<link>' + self._xml_preformat(self.aq_inner.absolute_url()) + '/search</link>\n'\
                    '</textinput>\n\n'

        feed += '</channel>\n'\
                '</rss>\n'

        return feed

    def _xml_preformat(self, text):
        text = text.encode('UTF-8')
        text = text.replace('&', '&amp;')
        text = text.replace('"', '&quot;')
        text = text.replace('<', '&lt;')
        text = text.replace('>', '&gt;')

        return text


    # MANIPULATORS

    security.declareProtected(SilvaPermissions.ChangeSilvaContent,
                              'set_rss_description')
    def set_rss_description(self, value):
        """Sets the RSS description"""
        self._rss_description = value

    security.declareProtected(SilvaPermissions.ChangeSilvaContent,
                              'set_show_agenda_items')
    def set_show_agenda_items(self, value):
        self._show_agenda_items = not not int(value)

    security.declareProtected(SilvaPermissions.ChangeSilvaContent,
                              'set_allow_rss_export')
    def set_allow_rss_export(self, yesorno):
        """Sets whether it is allowed to export to RSS"""
        self._allow_rss_export = not not yesorno

    security.declareProtected(SilvaPermissions.ChangeSilvaContent,
                              'set_allow_rss_search')
    def set_allow_rss_search(self, yesorno):
        """Sets allow_rss_search"""
        self._allow_rss_search = not not yesorno

    security.declareProtected(SilvaPermissions.ChangeSilvaContent,
                              'set_rss_search_description')
    def set_rss_search_description(self, value):
        """Sets the description"""
        self._rss_search_description = value

    security.declareProtected(SilvaPermissions.ChangeSilvaContent,
                              'set_rss_link')
    def set_rss_link(self, value):
        """Sets the RSS link"""
        self._rss_link = value

    security.declareProtected(SilvaPermissions.ChangeSilvaContent,
                              'set_rss_image')
    def set_rss_image(self, value):
        """Sets the RSS image"""
        self._rss_image = value

    security.declareProtected(SilvaPermissions.ChangeSilvaContent,
                              'set_rss_copyright')
    def set_rss_copyright(self, value):
        """Sets the RSS copyright notice"""
        self._rss_copyright = value

InitializeClass(NewsFilter)

manage_addNewsFilterForm = PageTemplateFile("www/newsFilterAdd", globals(),
                                       __name__='manage_addNewsFilterForm')

def manage_addNewsFilter(self, id, title, REQUEST=None):
    """Add an NewsFilter."""
    if not mangle.Id(self, id).isValid():
        return
    object = NewsFilter(id)
    self._setObject(id, object)
    object = getattr(self, id)
    object.set_title(title)
    add_and_edit(self, id, REQUEST)
    return ''

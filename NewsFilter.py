# Copyright (c) 2002-2005 Infrae. All rights reserved.
# See also LICENSE.txt
# $Revision: 1.31.2.1 $

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
        filter the items on several criteria (as well as individually).
    """
    security = ClassSecurityInfo()

    meta_type = "Silva News Filter"

    search = ViewAttribute('public', 'index_html')

    #__implements__ = INewsFilter

    _article_meta_types = ['Silva Article Version']
    _agenda_item_meta_types = ['Silva Agenda Item Version']

    def __init__(self, id):
        NewsFilter.inheritedAttribute('__init__')(self, id)
        self._show_agenda_items = 0

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
        query['idx_subjects'] = {'query': self._subjects,
                                'operator': 'or'}
        query['idx_target_audiences'] = {'query': self._target_audiences,
                                        'operator': 'or'}
        if not meta_types:
            meta_types = self.get_allowed_meta_types()
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
            last_night = DateTime(now.strftime("%Y/%m/%d 01:00am"))
            query['silva-extrapublicationtime'] = {'query': [last_night - number, now],
                                                    'range': 'minmax'}
        result = self.service_catalog(query)
        filtered_result = [r for r in result if not r.object_path in self._excluded_items]
        if not number_is_days:
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
        query['idx_start_datetime'] = (lastnight, enddate)
        query['idx_start_datetime_usage'] = 'range:min:max'
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
        query['idx_start_datetime'] = [startdate, enddate]
        query['idx_start_datetime_usage'] = 'range:min:max'
        result = self.service_catalog(query)

        return [r for r in result if not r.object_path in self._excluded_items]

    security.declareProtected(SilvaPermissions.AccessContentsInformation,
                              'show_agenda_items')
    def show_agenda_items(self):
        return self._show_agenda_items

    security.declarePrivate('get_allowed_meta_types')
    def get_allowed_meta_types(self):
        """Returns the allowed meta_types for this filter"""
        allowed = self._article_meta_types[:]
        if self.show_agenda_items():
            allowed += self._agenda_item_meta_types[:]
        return allowed

    # MANIPULATORS

    security.declareProtected(SilvaPermissions.ChangeSilvaContent,
                              'set_show_agenda_items')
    def set_show_agenda_items(self, value):
        self._show_agenda_items = not not int(value)

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

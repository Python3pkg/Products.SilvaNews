# Copyright (c) 2002-2007 Infrae. All rights reserved.
# See also LICENSE.txt
# $Revision: 1.25 $

from zope.interface import implements

# Zope
from AccessControl import ClassSecurityInfo
from Globals import InitializeClass
from DateTime import DateTime

# Silva/News interfaces
from interfaces import IAgendaFilter

# Silva/News
from Products.Silva import SilvaPermissions
from Filter import Filter,brainsorter

class AgendaFilter(Filter):
    """To enable editors to channel newsitems on a site, all items
       are passed from NewsFolder to NewsViewer through filters. On a filter
       you can choose which NewsFolders you want to channel items for and
       filter the items on several criteria (as well as individually). 
    """
    security = ClassSecurityInfo()

    meta_type = "Silva Agenda Filter"

    implements(IAgendaFilter)

    _allowed_meta_types = ['Silva Agenda Item Version']

    def __init__(self, id):
        AgendaFilter.inheritedAttribute('__init__')(self, id)

    security.declareProtected(SilvaPermissions.AccessContentsInformation,
                              'get_items_by_date')
    def get_items_by_date(self, month, year, meta_types=None):
        """
        Returns non-excluded published items for a particular
        publication month
        """
        self.verify_sources()
        if not self._sources:
            return []
        if not meta_types:
            meta_types = self.get_allowed_meta_types()
        self.verify_excluded_items()
        month = int(month)
        year = int(year)
        startdate = DateTime(year, month, 1).earliestTime()
        endmonth = month + 1
        if month == 12:
            endmonth = 1
            year = year + 1
        enddate = DateTime(year, endmonth, 1).earliestTime()

        result = []

        # end_datetime items first
        query = self._prepare_query()
        query['idx_end_datetime'] = {'query':[startdate, enddate],
                                     'range':'minmax'}
        query['sort_on'] = 'idx_end_datetime'
        query['sort_order'] = 'ascending'
        result_enddt = self._query(**query)

        for item in result_enddt:
            if item.object_path not in self._excluded_items:
                result.append(item)


        del query['idx_end_datetime']
        query['idx_start_datetime'] = {'query': [startdate, enddate],
                                                'range': 'minmax'}
        query['sort_on'] = 'idx_start_datetime'
        result_startdt = self._query(**query)

        result = [r for r in result]

        for item in result_startdt:
            edt = item.end_datetime
            if (item.object_path not in self._excluded_items and
                    (not edt or edt.month() != month or edt.year() != year)):
                result.append(item)
        result.sort(brainsorter)
        return result

    security.declareProtected(SilvaPermissions.AccessContentsInformation,
                              'backend_get_items_by_date')
    def backend_get_items_by_date(self, month, year, meta_types=None):
        """Returns all published items for a particular month
        """
        self.verify_sources()
        if not self._sources:
            return []

        month = int(month)
        year = int(year)
        startdate = DateTime(year, month, 1).earliestTime()
        endmonth = month + 1
        if month == 12:
            endmonth = 1
            year = year + 1
        enddate = DateTime(year, endmonth, 1).earliestTime()
        
        # end dt first
        query = self._prepare_query()
        query['sort_order'] = 'ascending'
        query['sort_on'] = 'idx_end_datetime'
        query['idx_end_datetime'] = {'query': [startdate, enddate],
                                     'range': 'minmax' }
        result = self._query(**query)

        del query['idx_end_datetime']
        query['idx_start_datetime'] = {'query': [startdate, enddate],
                                       'range': 'minmax'}
        query['sort_on'] = 'idx_start_datetime'
        result_startdt = self._query(**query)

        result = [r for r in result]
        result_items = [ r.object_path for r in result ]

        for item in result_startdt:
            edt = item.end_datetime
            if not edt or edt.month() != month or edt.year() != year \
               and item.object_path not in result_items:
                result.append(item)
        result.sort(brainsorter)
        return result

    def _is_agenda_addable(self, addable_dict):
        return (
            addable_dict.has_key('instance') and
            IAgendaItem.isImplementedByInstancesOf(
            addable_dict['instance']))

    security.declarePrivate('get_allowed_meta_types')
    def get_allowed_meta_types(self):
        """Returns the allowed meta_types for this filter"""
        return self._allowed_meta_types

InitializeClass(AgendaFilter)

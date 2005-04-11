# Copyright (c) 2002-2005 Infrae. All rights reserved.
# See also LICENSE.txt
# $Revision: 1.19.2.3 $

from OFS import SimpleItem
from AccessControl import ClassSecurityInfo
from Globals import InitializeClass
from Products.PageTemplates.PageTemplateFile import PageTemplateFile
from DateTime import DateTime
import OFS
# Silva
from Products.Silva import SilvaPermissions
# misc
from Products.Silva.helpers import add_and_edit
from Products.Silva import mangle

from Filter import Filter, MetaTypeException
from interfaces import IAgendaItemVersion

icon = 'www/agenda_filter.png'
addable_priority = 3.4

def brainsorter(a, b):
    aobj = a.getObject()
    atime = aobj.start_datetime()
    bobj = b.getObject()
    btime = bobj.start_datetime()
    return cmp(atime, btime)

class AgendaFilter(Filter):
    """To enable editors to channel newsitems on a site, all items
       are passed from NewsFolder to NewsViewer through filters. On a filter
       you can choose which NewsFolders you want to channel items for and
       filter the items on several criteria (as well as individually). 
    """
    security = ClassSecurityInfo()

    meta_type = "Silva Agenda Filter"

    _allowed_meta_types = ['Silva Agenda Item Version']

    def __init__(self, id):
        AgendaFilter.inheritedAttribute('__init__')(self, id)

    security.declareProtected(SilvaPermissions.AccessContentsInformation,
                              'get_next_items')
    def get_next_items(self, numdays, meta_types=None):
        """Returns published items from now up to a number of days
        """
        self.verify_sources()
        if not self._sources:
            return []
        if not meta_types:
            meta_types = self.get_allowed_meta_types()
            
        self.verify_excluded_items()

        result = []
        
        date = DateTime()
        lastnight = DateTime(date.year(), date.month(), date.day(), 0, 0, 0)
        enddate = lastnight + numdays
        result_enddt = self._query(
            idx_end_datetime = (lastnight, enddate),
            idx_end_datetime_usage = 'range:min:max',
            version_status = 'public',
            path = self._sources,
            subjects = {'query': self._subjects,
                        'operator': 'or'},
            target_audiences = {'query': self._target_audiences,
                                'operator': 'or'},
            meta_type = meta_types,
            sort_on = 'idx_end_datetime',
            sort_order = 'ascending')

        for item in result_enddt:
            if not item.object_path in self._excluded_items:
                result.append(item)

        result_startdt = self._query(
            idx_start_datetime = (lastnight, enddate),
            idx_start_datetime_usage = 'range:min:max',
            version_status = 'public',
            path = self._sources,
            subjects = {'query': self._subjects,
                        'operator': 'or'},
            target_audiences = {'query': self._target_audiences,
                                'operator': 'or'},
            meta_type = meta_types,
            sort_on = 'idx_start_datetime',
            sort_order = 'ascending')

        # remove all objects from result_startdt for which an end datetime is 
        # set (since they're retrieved above)
        for item in result_startdt:
            if (not item.object_path in self._excluded_items and 
                    not hasattr(item, 'end_datetime') or not
                        item.getObject().end_datetime()):
                result.append(item)

        result = [r for r in result]
        result.sort(brainsorter)

        return result

    security.declareProtected(SilvaPermissions.AccessContentsInformation,
                              'get_last_items')
    def get_last_items(self, number, dummy=0, meta_types=None):
        """Returns the last self._number_to_show published items
        """
        self.verify_sources()
        if not self._sources:
            return []
        if not meta_types:
            meta_types = self.get_allowed_meta_types()
        self.verify_excluded_items()

        result = self._query(
            path=self._sources,
            version_status='public',
            subjects={'query': self._subjects,
                        'operator': 'or'},
            target_audiences={'query': self._target_audiences,
                                'operator': 'or'},
            meta_type=meta_types,
            )
        
        filtered_result = [r for r in result
                           if not r.object_path in self._excluded_items]

        output = []
        for i in range(len(filtered_result)):
            if i < number:
                output.append(filtered_result[i])
            else:
                break
        output = [r for r in output]
        output.sort(brainsorter)
        return output

    security.declareProtected(SilvaPermissions.AccessContentsInformation,
                              'get_agenda_items_by_date')
    def get_agenda_items_by_date(self, month, year, meta_types=None):
        """Returns non-excluded published items for a particular start month
        """
        self.verify_sources()
        if not self._sources:
            return []
        if not meta_types:
            meta_types = self.get_allowed_meta_types()
        self.verify_excluded_items()
        month = int(month)
        year = int(year)
        startdate = DateTime(year, month, 1)
        endmonth = month + 1
        if month == 12:
            endmonth = 1
            year = year + 1
        enddate = DateTime(year, endmonth, 1)

        result = []
    
        # first query for objects that do have an end datetime defined
        query = {}
        query['idx_end_datetime'] = [startdate, enddate]
        query['idx_end_datetime_usage'] = 'range:min:max'
        query['version_status'] = 'public'
        query['path'] = self._sources
        query['idx_subjects'] = {'query': self._subjects,
                                'operator': 'or'}
        query['idx_target_audiences'] = {'query': self._target_audiences,
                                        'operator': 'or'}
        query['meta_type'] = meta_types
        query['sort_on'] = 'idx_end_datetime'
        query['sort_order'] = 'ascending'
        result_enddt = self.service_catalog(query)

        for item in result_enddt:
            if item.object_path not in self._excluded_items:
                result.append(item)
        
        # now those that don't have end_datetime
        query = {}
        query['idx_start_datetime'] = [startdate, enddate]
        query['idx_start_datetime_usage'] = 'range:min:max'
        query['version_status'] = 'public'
        query['path'] = self._sources
        query['idx_subjects'] = {'query': self._subjects,
                                'operator': 'or'}
        query['idx_target_audiences'] = {'query': self._target_audiences,
                                        'operator': 'or'}
        query['meta_type'] = meta_types
        query['sort_on'] = 'idx_start_datetime'
        query['sort_order'] = 'ascending'
        result_startdt = self.service_catalog(query)

        # remove the items with an end_dt from the result_startdt
        for item in result_startdt:
            if (item.object_path not in self._excluded_items and
                    not item.getObject().end_datetime()):
                result.append(item)

        result = [r for r in result]
        result.sort(brainsorter)

        return result

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
        startdate = DateTime(year, month, 1)
        endmonth = month + 1
        if month == 12:
            endmonth = 1
            year = year + 1
        enddate = DateTime(year, endmonth, 1)

        result = []

        # end_datetime items first
        query = {}
        query['idx_end_datetime'] = {'query': [startdate, enddate],
                                                'range': 'minmax'}
        query['version_status'] = 'public'
        query['path'] = self._sources
        query['idx_subjects'] = {'query': self._subjects,
                                'operator': 'or'}
        query['idx_target_audiences'] = {'query': self._target_audiences,
                                        'operator': 'or'}
        query['meta_type'] = meta_types
        query['sort_on'] = 'idx_end_datetime'
        query['sort_order'] = 'ascending'
        result_enddt = self.service_catalog(query)

        for item in result_enddt:
            if item.object_path not in self._excluded_items:
                result.append(item)

        query = {}
        query['idx_start_datetime'] = {'query': [startdate, enddate],
                                                'range': 'minmax'}
        query['version_status'] = 'public'
        query['path'] = self._sources
        query['idx_subjects'] = {'query': self._subjects,
                                'operator': 'or'}
        query['idx_target_audiences'] = {'query': self._target_audiences,
                                        'operator': 'or'}
        query['meta_type'] = meta_types
        query['sort_on'] = 'idx_start_datetime'
        query['sort_order'] = 'ascending'
        result_startdt = self.service_catalog(query)

        for item in result_startdt:
            if (item.object_path not in self._excluded_items and
                    not item.getObject().end_datetime()):
                result.append(item)

        result = [r for r in result]
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
        if not meta_types:
            meta_types = self.get_allowed_meta_types()
        self.verify_excluded_items()
        month = int(month)
        year = int(year)
        startdate = DateTime(year, month, 1)
        endmonth = month + 1
        if month == 12:
            endmonth = 1
            year = year + 1
        enddate = DateTime(year, endmonth, 1)
        
        # end dt first
        query = {}
        query['idx_end_datetime'] = [startdate, enddate]
        query['idx_end_datetime_usage'] = 'range:min:max'
        query['version_status'] = 'public'
        query['path'] = self._sources
        query['idx_subjects'] = self._subjects
        query['idx_target_audiences'] = self._target_audiences
        query['meta_type'] = meta_types
        query['sort_on'] = 'idx_end_datetime'
        query['sort_order'] = 'ascending'
        result = self.service_catalog(query)

        query = {}
        query['idx_start_datetime'] = [startdate, enddate]
        query['idx_start_datetime_usage'] = 'range:min:max'
        query['version_status'] = 'public'
        query['path'] = self._sources
        query['idx_subjects'] = self._subjects
        query['idx_target_audiences'] = self._target_audiences
        query['meta_type'] = meta_types
        query['sort_on'] = 'idx_start_datetime'
        query['sort_order'] = 'ascending'
        result_startdt = self.service_catalog(query)

        result = [r for r in result]

        for item in result_startdt:
            if not item.getObject().end_datetime():
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

manage_addAgendaFilterForm = PageTemplateFile("www/agendaFilterAdd", globals(),
                                       __name__='manage_addAgendaFilterForm')

def manage_addAgendaFilter(self, id, title, REQUEST=None):
    """Add an AgendaFilter."""
    if not mangle.Id(self, id).isValid():
        return
    object = AgendaFilter(id)
    self._setObject(id, object)
    object = getattr(self, id)
    object.set_title(title)
    add_and_edit(self, id, REQUEST)
    return ''

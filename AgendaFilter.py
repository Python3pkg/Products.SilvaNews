# Copyright (c) 2002 Infrae. All rights reserved.
# See also LICENSE.txt
# $Revision: 1.17.2.1 $

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

class AgendaFilter(Filter):
    """To enable editors to channel newsitems on a site, all items
       are passed from NewsFolder to NewsViewer through filters. On a filter
       you can choose which NewsFolders you want to channel items for and
       filter the items on several criteria (as well as individually). 
    """
    security = ClassSecurityInfo()

    meta_type = "Silva Agenda Filter"

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
        date = DateTime()
        lastnight = DateTime(date.year(), date.month(), date.day(), 0, 0, 0)
        enddate = lastnight + numdays
        result = self._query(
            start_datetime = (lastnight, enddate),
            start_datetime_usage = 'range:min:max',
            version_status = 'public',
            path = self._sources,
            subjects = {'query': self._subjects,
                        'operator': 'or'},
            target_audiences = {'query': self._target_audiences,
                                'operator': 'or'},
            meta_type = meta_types,
            sort_on = 'start_datetime',
            sort_order = 'ascending')

        return [r for r in result if not r.object_path in self._excluded_items]

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
            sort_on='silva-extrapublicationtime',
            sort_order='ascending',
            )
        
        filtered_result = [r for r in result
                           if not r.object_path in self._excluded_items]
        output = []
        for i in range(len(filtered_result)):
            if i < number:
                output.append(filtered_result[i])
            else:
                break
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
    
        query = {}
        query['start_datetime'] = [startdate, enddate]
        query['start_datetime_usage'] = 'range:min:max'
        query['version_status'] = 'public'
        query['path'] = self._sources
        query['subjects'] = {'query': self._subjects,
                                'operator': 'or'}
        query['target_audiences'] = {'query': self._target_audiences,
                                        'operator': 'or'}
        query['meta_type'] = meta_types
        query['sort_on'] = 'start_datetime'
        query['sort_order'] = 'ascending'
        result = self.service_catalog(query)
        return [r for r in result if not r.object_path in self._excluded_items]

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
        query = {}
        query['silva-extrapublicationtime'] = {'query': [startdate, enddate],
                                                'range': 'minmax'}
        query['version_status'] = 'public'
        query['path'] = self._sources
        query['subjects'] = {'query': self._subjects,
                                'operator': 'or'}
        query['target_audiences'] = {'query': self._target_audiences,
                                        'operator': 'or'}
        query['meta_type'] = meta_types
        query['sort_on'] = 'silva-extrapublicationtime'
        query['sort_order'] = 'ascending'
        result = self.service_catalog(query)

        return [r for r in result if not r.object_path in self._excluded_items]

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
        query = {}
        query['start_datetime'] = [startdate, enddate]
        query['start_datetime_usage'] = 'range:min:max'
        query['version_status'] = 'public'
        query['path'] = self._sources
        query['subjects'] = self._subjects
        query['target_audiences'] = self._target_audiences
        query['meta_type'] = meta_types
        query['sort_on'] = 'start_datetime'
        query['sort_order'] = 'ascending'
        result = self.service_catalog(query)

        return result

    def _is_agenda_addable(self, addable_dict):
        return (
            addable_dict.has_key('instance') and
            IAgendaItem.isImplementedByInstancesOf(
            addable_dict['instance']))

    security.declarePrivate('get_allowed_meta_types')
    def get_allowed_meta_types(self):
        """Returns the allowed meta_types for this filter"""
        allowed = []
        mts = self.get_root().filtered_meta_types()
        for mt in mts:
            if (mt.has_key('instance') and
                IAgendaItemVersion.isImplementedByInstancesOf(mt['instance'])):
                allowed.append(mt['name'])
        return allowed

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

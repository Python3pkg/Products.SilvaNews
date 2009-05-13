# Copyright (c) 2002-2008 Infrae. All rights reserved.
# See also LICENSE.txt
# $Revision: 1.34 $

from types import StringType
from zope.interface import implements

# Zope
from AccessControl import ClassSecurityInfo
from Globals import InitializeClass
#XXX Why do newsViewers inherit/extend OFS.Folder.Folder???
from OFS import Folder

# Silva/News interfaces
from Products.Silva.interfaces import IContent
from Products.SilvaNews.interfaces import INewsViewer

# Silva/News
from Products.Silva import SilvaPermissions
from Products.Silva.Content import Content

class NewsViewer(Content, Folder.Folder):
    """Used to show news items on a Silva site.

    When setting up a newsviewer you can choose which news- or
    agendafilters it should use to retrieve the items, and how far
    back in time it should go. The items will then be automatically
    fetched via the filter for each page request.
    """

    meta_type = 'Silva News Viewer'

    security = ClassSecurityInfo()

    implements(INewsViewer)

    def __init__(self, id):
        NewsViewer.inheritedAttribute('__init__')(self, id)
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
        for item in obj.superValues(['Silva News Filter',
                                  'Silva Agenda Filter']):
            joinedpath = '/'.join(item.getPhysicalPath())
            pairs.append(('%s (<a href="%s/edit">%s</a>)' %
                          (item.get_title(), joinedpath, joinedpath),
                          joinedpath))
        return pairs

    def verify_filters(self):
        allowed_filters = self.findfilters()
        for newsfilter in self._filters:
            if newsfilter not in allowed_filters:
                self._filters.remove(newsfilter)
                self._p_changed = 1

    def _get_items_helper(self, func, sortattr=None, reverse=True):
        #1) helper function for get_items...this was the same
        #code in NV and AV.  Now this helper contains that code
        #and calls func(obj) for each filter to actually
        #get the items.  Func can be a simple lamba: function
        #2) sortattr is an attribute of the CatalogBraings objects
        #   i.e. a result item.  It's a catalog metadata column
        #   use it for fast sort / merging of multiple filters
        #   e.g. on display_datetime or start_datetime
        self.verify_filters()
        results = []
        for newsfilter in self._filters:
            obj = self.aq_inner.restrictedTraverse(newsfilter)
            res = func(obj)
            results += res

        results = self._remove_doubles(results)

        if sortattr:
            sorted_results = []
            if type(sortattr) is StringType:
                sortattr = [sortattr]
            for r in results:
                r_t = None
                for s in sortattr:
                    attr = getattr(r,s,None)
                    if attr:
                        r_t = (attr,getattr(r,'object_path',None),r)
                        break
                if not r_t:
                    r_t = (None,getattr(r,'object_path',None), r)
                sorted_results.append(r_t)
            sorted_results.sort()
            results = [ r[-1] for r in sorted_results ]
            if reverse:
                results.reverse()
        return results
        
    security.declareProtected(SilvaPermissions.AccessContentsInformation,
                              'get_items')
    def get_items(self):
        """Gets the items from the filters
        """
        func = lambda x: x.get_last_items(self._number_to_show,self._number_is_days)
        #some news filters include agenda items, and
        # some filters are agenda filters, so sort first
        # by start_datetime, then by display_datetime
        sortattr = ['start_datetime','display_datetime']
        results = self._get_items_helper(func,sortattr)
        if not self._number_is_days:
            return results[:self._number_to_show]
            
        return results

    security.declareProtected(SilvaPermissions.AccessContentsInformation,
                              'get_items_by_date')
    def get_items_by_date(self, month, year):
        """Gets the items from the filters
        """
        func = lambda x: x.get_items_by_date(month,year)
        #some news filters include agenda items, and
        # some filters are agenda filters, so sort first
        # by start_datetime, then by display_datetime
        sortattr = ['start_datetime','display_datetime']
        return self._get_items_helper(func,sortattr)

    security.declareProtected(SilvaPermissions.AccessContentsInformation,
                              'search_items')
    def search_items(self, keywords):
        """Search the items in the filters
        """
        func = lambda x: x.search_items(keywords)
        #some news filters include agenda items, and
        # some filters are agenda filters, so sort first
        # by start_datetime, then by display_datetime
        sortattr = ['start_datetime','display_datetime']
        return self._get_items_helper(func,sortattr)

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
                self._p_changed = 1
        else:
            if newsfilter in self._filters:
                self._filters.remove(newsfilter)
                self._p_changed = 1
InitializeClass(NewsViewer)

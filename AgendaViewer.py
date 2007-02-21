# Copyright (c) 2002-2006 Infrae. All rights reserved.
# See also LICENSE.txt
# $Revision: 1.17 $

from zope.interface import implements

from AccessControl import ClassSecurityInfo
from Globals import InitializeClass
from Products.PageTemplates.PageTemplateFile import PageTemplateFile
from OFS import Folder

from Products.Silva import SilvaPermissions
from Products.Silva.helpers import add_and_edit
from Products.Silva.interfaces import IContent
from Products.Silva import mangle

from NewsViewer import NewsViewer
from Products.SilvaNews.interfaces import IAgendaItemVersion

from Products.SilvaNews.interfaces import IAgendaViewer

icon = 'www/agenda_viewer.png'
addable_priority = 3.3

class AgendaViewer(NewsViewer):
    """
    Used to show agendaitems on a Silva site. When setting up an
    agendaviewer you can choose which agendafilters it should use to
    get the items from and how long in advance you want the items
    shown. The items will then automatically be retrieved from the
    agendafilter for each request.
    """

    security = ClassSecurityInfo()

    implements(IContent, IAgendaViewer)

    meta_type = "Silva Agenda Viewer"

    show_in_tocs = 1

    def __init__(self, id):
        AgendaViewer.inheritedAttribute('__init__')(self, id)
        self._days_to_show = 31
        self._number_to_show_archive = 10
        self._filters = []

    security.declareProtected(SilvaPermissions.AccessContentsInformation,
                              'findfilters_pairs')
    def findfilters_pairs(self):
        """Returns a list of tuples (title, path) for all filters
        from catalog for rendering formulator-items
        """
        # IS THIS THE MOST EFFICIENT WAY?
        pairs = []
        obj = self.aq_inner
        while 1:
            parent = obj.aq_parent
            parentpath = parent.getPhysicalPath()
            for item in parent.objectValues(['Silva Agenda Filter',
                                             'Silva News Filter']):
                joinedpath = '/'.join(item.getPhysicalPath())
                pairs.append(('%s (<a href="%s/edit">%s</a>)' %
                              (item.get_title(), joinedpath, joinedpath),
                              joinedpath))
            if parentpath == ('',):
                break
            obj = parent

        return pairs

    security.declareProtected(SilvaPermissions.AccessContentsInformation,
                              'days_to_show')
    def days_to_show(self):
        """Returns number of days to show
        """
        return self._days_to_show

    security.declareProtected(SilvaPermissions.AccessContentsInformation,
                              'get_items')
    def get_items(self):
        """Gets the items from the filters
        """
        results = []
        for newsfilter in self._filters:
            obj = self.aq_inner.restrictedTraverse(newsfilter)
            res = obj.get_next_items(self._days_to_show)
            results += res

        results = self._remove_doubles(results)
        results.sort(self._sortresults)
        return results

    security.declareProtected(SilvaPermissions.AccessContentsInformation,
                              'get_items_by_date')
    def get_items_by_date(self, month, year):
        """Gets the items from the filters
        """
        results = []
        for newsfilter in self._filters:
            obj = self.aq_inner.restrictedTraverse(newsfilter)
            res = obj.get_agenda_items_by_date(month, year)
            results += res

        results = self._remove_doubles(results)
        results.sort(self._sortresults)
        return results

    security.declareProtected(SilvaPermissions.AccessContentsInformation,
                              'search_items')
    def search_items(self, keywords):
        """Search the items in the filters
        """
        self.verify_filters()
        results = []
        allowed_meta_types = self.get_allowed_meta_types()
        for newsfilter in self._filters:
            obj = self.aq_inner.restrictedTraverse(newsfilter)
            res = obj.search_items(keywords, allowed_meta_types)
            results += res

        results = self._remove_doubles(results)
        results.sort(self._sortresults)
        if not self._number_is_days:
            return results[:self._number_to_show]
        else:
            return results

    security.declareProtected(SilvaPermissions.ChangeSilvaContent,
                              'set_days_to_show')
    def set_days_to_show(self, number):
        """Sets the number of days to show in the agenda
        """
        self._days_to_show = number
        self._p_changed = 1

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

    def _sortresults(self, item1, item2):
        return cmp(item1.getObject().start_datetime(), item2.getObject().start_datetime())

InitializeClass(AgendaViewer)

manage_addAgendaViewerForm = PageTemplateFile(
    "www/agendaViewerAdd", globals(),
    __name__='manage_addAgendaViewerForm')

def manage_addAgendaViewer(self, id, title, REQUEST=None):
    """Add a News AgendaViewer."""
    if not mangle.Id(self, id).isValid():
        return
    object = AgendaViewer(id)
    self._setObject(id, object)
    object = getattr(self, id)
    object.set_title(title)
    add_and_edit(self, id, REQUEST)
    return ''

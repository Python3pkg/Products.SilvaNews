# Copyright (c) 2002-2008 Infrae. All rights reserved.
# See also LICENSE.txt
# $Revision: 1.17 $

from zope.interface import implements

# Zope
import Products
from AccessControl import ClassSecurityInfo
from Globals import InitializeClass
from Products.PageTemplates.PageTemplateFile import PageTemplateFile
from OFS import Folder

# Silva/News interfaces
from Products.SilvaNews.interfaces import IAgendaItemVersion, IAgendaViewer

# Silva/News interfaces
from Products.Silva import SilvaPermissions
from NewsViewer import NewsViewer

class AgendaViewer(NewsViewer):
    """
    Used to show agendaitems on a Silva site. When setting up an
    agendaviewer you can choose which agendafilters it should use to
    get the items from and how long in advance you want the items
    shown. The items will then automatically be retrieved from the
    agendafilter for each request.
    """

    security = ClassSecurityInfo()

    implements(IAgendaViewer)

    meta_type = "Silva Agenda Viewer"

    show_in_tocs = 1

    def __init__(self, id):
        AgendaViewer.inheritedAttribute('__init__')(self, id)
        self._days_to_show = 31

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
        func = lambda x: x.get_next_items(self._days_to_show)
        return self._get_items_helper(func,'start_datetime',reverse=False)

    security.declareProtected(SilvaPermissions.AccessContentsInformation,
                              'get_items_by_date')
    def get_items_by_date(self, month, year):
        """Gets the items from the filters
        """
        func = lambda x: x.get_agenda_items_by_date(month,year)
        return self._get_items_helper(func,'start_datetime',reverse=False)

    security.declareProtected(SilvaPermissions.AccessContentsInformation,
                              'search_items')
    def search_items(self, keywords):
        """Search the items in the filters
        """
        allowed_meta_types = self.get_allowed_meta_types()
        func = lambda x: x.search_items(keywords,allowed_meta_types)
        return self._get_items_helper(func,'start_datetime',reverse=False)

    security.declarePrivate('get_allowed_meta_types')
    def get_allowed_meta_types(self):
        """Returns the allowed meta_types for this Viewer"""
        """results are passed to the filters, some of which may be
           news filters -- don't want to return PlainNewsItems"""
        allowed = []
        mts = Products.meta_types
        for mt in mts:
            if (mt.has_key('instance') and
                IAgendaItemVersion.implementedBy(mt['instance'])):
                allowed.append(mt['name'])
        return allowed

    security.declareProtected(SilvaPermissions.ChangeSilvaContent,
                              'set_days_to_show')
    def set_days_to_show(self, number):
        """Sets the number of days to show in the agenda
        """
        self._days_to_show = number

InitializeClass(AgendaViewer)

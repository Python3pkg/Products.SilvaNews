# Copyright (c) 2002-2008 Infrae. All rights reserved.
# See also LICENSE.txt
# $Id$

# ztk
from five import grok
from zope.interface import implements

# Zope
from AccessControl import ClassSecurityInfo
from App.class_init import InitializeClass

# Silva
from silva.core import conf as silvaconf
from Products.Silva import SilvaPermissions

# SilvaNews
from Products.SilvaNews.interfaces import IAgendaItem, IAgendaItemVersion
from Products.SilvaNews.NewsItem import NewsItem, NewsItemVersion
from silva.app.news.datetimeutils import datetime_to_unixtimestamp
from silva.app.news.AgendaItem.content import AgendaItemOccurrence

_marker = object()


class AgendaItemVersion(NewsItemVersion):
    """Silva News AgendaItemVersion
    """
    grok.implements(IAgendaItemVersion)

    security = ClassSecurityInfo()
    meta_type = "Silva Agenda Item Version"

    _occurrences = []

    security.declareProtected(
        SilvaPermissions.ChangeSilvaContent, 'set_occurrences')
    def set_occurrences(self, occurrences):
        self._occurrences = occurrences

    security.declareProtected(
        SilvaPermissions.AccessContentsInformation, 'get_occurrences')
    def get_occurrences(self):
        # Secuity check in ZODB
        return map(lambda o: o.__of__(self), self._occurrences)

    security.declareProtected(SilvaPermissions.AccessContentsInformation,
                              'fulltext')
    def fulltext(self):
        """Deliver the contents as plain text, for full-text search
        """
        parenttext = AgendaItemVersion.inheritedAttribute('fulltext')(self)
        return "%s %s" % (parenttext, self._location)

    security.declareProtected(SilvaPermissions.AccessContentsInformation,
                              'sort_index')
    def sort_index(self):
        dt = self.get_start_datetime()
        if dt:
            return datetime_to_unixtimestamp(dt)
        return None

    security.declareProtected(SilvaPermissions.AccessContentsInformation,
                              'get_timestamp_ranges')
    def get_timestamp_ranges(self):
        return self.get_calendar_datetime().\
            get_unixtimestamp_ranges()


InitializeClass(AgendaItemVersion)


class AgendaItem(NewsItem):
    """A News item for events. Includes date and location
       metadata, as well settings for subjects and audiences.
    """
    security = ClassSecurityInfo()
    implements(IAgendaItem)
    meta_type = "Obsolete Agenda Item"
    silvaconf.icon("www/agenda_item.png")
    silvaconf.priority(3.8)
    silvaconf.versionClass(AgendaItemVersion)


InitializeClass(AgendaItem)



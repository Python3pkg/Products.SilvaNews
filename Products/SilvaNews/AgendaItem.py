# Copyright (c) 2002-2008 Infrae. All rights reserved.
# See also LICENSE.txt
# $Id$

from icalendar import vDatetime
from dateutil.rrule import rrulestr

# ztk
from five import grok
from zope.component import getUtility
from zope.i18nmessageid import MessageFactory
from zope.interface import implements

# Zope
from AccessControl import ClassSecurityInfo
from App.class_init import InitializeClass

# Silva
from silva.core import conf as silvaconf
from Products.Silva import SilvaPermissions

# SilvaNews
from Products.SilvaNews.interfaces import IAgendaItem, IAgendaItemVersion
from silva.app.news.interfaces import IServiceNews
from Products.SilvaNews.NewsItem import NewsItem, NewsItemVersion

from Products.SilvaNews.datetimeutils import (datetime_with_timezone,
    CalendarDatetime, datetime_to_unixtimestamp, get_timezone, RRuleData, UTC)


_marker = object()
_ = MessageFactory('silva_news')

class AgendaItemVersion(NewsItemVersion):
    """Silva News AgendaItemVersion
    """
    grok.implements(IAgendaItemVersion)

    security = ClassSecurityInfo()
    meta_type = "Silva Agenda Item Version"

    _start_datetime = None
    _end_datetime = None
    _display_time = True
    _location = ''
    _recurrence = None
    _all_day = False
    _timezone_name = None

    security.declareProtected(SilvaPermissions.ChangeSilvaContent,
                              'set_timezone_name')
    def set_timezone_name(self, name):
        self._timezone_name = name

    security.declareProtected(SilvaPermissions.AccessContentsInformation,
                              'get_timezone_name')
    def get_timezone_name(self):
        timezone_name = getattr(self, '_timezone_name', None)
        if timezone_name is None:
            timezone_name = getUtility(IServiceNews).get_timezone_name()
        return timezone_name

    security.declareProtected(SilvaPermissions.AccessContentsInformation,
                              'get_timezone')
    def get_timezone(self):
        if not hasattr(self, '_v_timezone'):
            self._v_timezone = get_timezone(self.get_timezone_name())
        return self._v_timezone

    security.declareProtected(SilvaPermissions.AccessContentsInformation,
                              'get_rrule')
    def get_rrule(self):
        if self._recurrence is not None:
            return rrulestr(str(self._recurrence),
                            dtstart=self._start_datetime)
        return None

    security.declareProtected(SilvaPermissions.AccessContentsInformation,
                              'get_calendar_datetime')
    def get_calendar_datetime(self):
        if not self._start_datetime:
            return None
        return CalendarDatetime(self._start_datetime,
                                self._end_datetime,
                                recurrence=self.get_rrule())

    security.declareProtected(SilvaPermissions.ChangeSilvaContent,
                              'set_display_time')
    def set_display_time(self, display_time):
        self._display_time = display_time

    security.declareProtected(SilvaPermissions.ChangeSilvaContent,
                              'set_start_datetime')
    def set_start_datetime(self, value):
        self._start_datetime = datetime_with_timezone(
            value, self.get_timezone())

    security.declareProtected(SilvaPermissions.ChangeSilvaContent,
                              'set_end_datetime')
    def set_end_datetime(self, value):
        self._end_datetime = datetime_with_timezone(
            value, self.get_timezone())

    security.declareProtected(SilvaPermissions.ChangeSilvaContent,
                              'set_recurrence')
    def set_recurrence(self, recurrence):
        self._recurrence = recurrence

    security.declareProtected(SilvaPermissions.ChangeSilvaContent,
                              'set_location')
    def set_location(self, value):
        self._location = value

    security.declareProtected(SilvaPermissions.ChangeSilvaContent,
                              'set_all_day')
    def set_all_day(self, value):
        self._all_day = bool(value)

    security.declareProtected(SilvaPermissions.AccessContentsInformation,
                              'display_time')
    def display_time(self):
        """returns True if the time parts of the datetimes should be displayed
        """
        return self._display_time

    security.declareProtected(SilvaPermissions.AccessContentsInformation,
                              'get_start_datetime')
    def get_start_datetime(self, tz=_marker):
        """Returns the start date/time
        """
        if tz is _marker:
            tz = self.get_timezone()
        cd = self.get_calendar_datetime()
        if cd:
            return cd.get_start_datetime(tz)
        return None

    security.declareProtected(SilvaPermissions.AccessContentsInformation,
                              'get_end_datetime')
    def get_end_datetime(self, tz=_marker):
        """Returns the start date/time
        """
        if tz is _marker:
            tz = self.get_timezone()
        cd = self.get_calendar_datetime()
        if cd:
            return cd.get_end_datetime(tz)
        return None

    security.declareProtected(SilvaPermissions.AccessContentsInformation,
                              'get_recurrence')
    def get_recurrence(self):
        if self._recurrence is not None:
            return str(self._recurrence)

    security.declareProtected(SilvaPermissions.AccessContentsInformation,
                              'get_recurrence')
    def get_end_recurrence_datetime(self):
        if self._recurrence is not None:
            dt_string = RRuleData(self.get_recurrence()).get('UNTIL')
            if dt_string:
                return vDatetime.from_ical(dt_string).\
                    replace(tzinfo=UTC).astimezone(self.get_timezone())

    security.declareProtected(SilvaPermissions.AccessContentsInformation,
                              'get_location')
    def get_location(self):
        """Returns location manual
        """
        return self._location

    security.declareProtected(SilvaPermissions.AccessContentsInformation,
                              'is_all_day')
    def is_all_day(self):
        return self._all_day

    security.declareProtected(SilvaPermissions.AccessContentsInformation,
                              'get_all_day')
    get_all_day = is_all_day

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



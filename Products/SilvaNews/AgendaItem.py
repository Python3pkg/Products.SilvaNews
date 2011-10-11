# Copyright (c) 2002-2011 Infrae. All rights reserved.
# See also LICENSE.txt
# $Id$

from icalendar import vDatetime, Calendar
from icalendar.interfaces import IEvent
from dateutil.rrule import rrulestr

from five import grok
from zope.component import getUtility, getMultiAdapter
from zope.traversing.browser import absoluteURL

# Zope
from AccessControl import ClassSecurityInfo
from Acquisition import Explicit
from App.class_init import InitializeClass # Zope 2.12

# Silva
from silva.core.views import views as silvaviews
from Products.Silva import SilvaPermissions

# SilvaNews
from Products.SilvaNews.interfaces import IAgendaItem, IAgendaItemVersion
from Products.SilvaNews.interfaces import INewsViewer
from Products.SilvaNews.interfaces import IServiceNews
from Products.SilvaNews.NewsItem import NewsItemView, NewsItemListItemView
from Products.SilvaNews.NewsItem import IntroHTML
from Products.SilvaNews.NewsItem import NewsItem, NewsItemVersion
from Products.SilvaNews.NewsItem import NewsItemVersionCatalogingAttributes
from Products.SilvaNews.datetimeutils import (datetime_with_timezone,
    CalendarDatetime, datetime_to_unixtimestamp, get_timezone, RRuleData, UTC)

_marker = object()


class AgendaItem(NewsItem):
    """Base class for agenda items.
    """
    security = ClassSecurityInfo()
    grok.implements(IAgendaItem)
    grok.baseclass()

InitializeClass(AgendaItem)


class AgendaItemOccurrence(Explicit):
    security = ClassSecurityInfo()

    _start_datetime = None
    _end_datetime = None
    _display_time = True
    _location = ''
    _recurrence = None
    _all_day = False
    _timezone_name = None

    def __init__(self,
                 start_datetime=_marker,
                 end_datetime=_marker,
                 display_time=_marker,
                 location=_marker,
                 all_day=_marker,
                 timezone_name=_marker,
                 recurrence=_marker,
                 end_recurrence_datetime=_marker):

        if timezone_name is not _marker:
            self.set_timezone_name(timezone_name)
            timezone = get_timezone(timezone_name)
        else:
            timezone = get_timezone(None)

        if start_datetime is not _marker:
            start_datetime = start_datetime.replace(tzinfo=timezone)
            self.set_start_datetime(start_datetime)
        if end_datetime is not _marker:
            end_datetime = end_datetime.replace(tzinfo=timezone)
            self.set_end_datetime(end_datetime)
        if display_time is not _marker:
            self.set_display_time(display_time)
        if location is not _marker:
            self.set_location(location)
        if recurrence is not _marker:
            recurrence = RRuleData(recurrence)
            if end_recurrence_datetime is not _marker:
                recurrence['UNTIL'] = vDatetime(
                    end_recurrence_datetime.replace(
                        tzinfo=timezone).astimezone(UTC))
            self.set_recurrence(str(recurrence))
        if all_day is not _marker:
            self.set_all_day(all_day)

    def set_timezone_name(self, name):
        self._timezone_name = name

    security.declareProtected(
        SilvaPermissions.AccessContentsInformation, 'get_timezone_name')
    def get_timezone_name(self):
        timezone_name = self._timezone_name
        if timezone_name is None:
            return getUtility(IServiceNews).get_timezone_name()
        return timezone_name

    def get_timezone(self):
        if not hasattr(self, '_v_timezone'):
            self._v_timezone = get_timezone(self.get_timezone_name())
        return self._v_timezone

    def set_start_datetime(self, value):
        self._start_datetime = datetime_with_timezone(
            value, self.get_timezone())

    security.declareProtected(
        SilvaPermissions.AccessContentsInformation, 'get_start_datetime')
    def get_start_datetime(self, tz=_marker):
        if tz is _marker:
            tz = self.get_timezone()
        cd = self.get_calendar_datetime()
        if cd:
            return cd.get_start_datetime(tz)
        return None

    def get_calendar_datetime(self):
        if not self._start_datetime:
            return None
        return CalendarDatetime(
            self._start_datetime,
            self._end_datetime,
            recurrence=self.get_rrule())

    def set_end_datetime(self, value):
        self._end_datetime = datetime_with_timezone(
            value, self.get_timezone())

    security.declareProtected(
        SilvaPermissions.AccessContentsInformation, 'get_end_datetime')
    def get_end_datetime(self, tz=_marker):
        if tz is _marker:
            tz = self.get_timezone()
        cd = self.get_calendar_datetime()
        if cd:
            return cd.get_end_datetime(tz)
        return None

    def set_recurrence(self, recurrence):
        self._recurrence = recurrence

    def get_recurrence(self):
        if self._recurrence is not None:
            return str(self._recurrence)

    def get_end_recurrence_datetime(self):
        if self._recurrence is not None:
            dt_string = RRuleData(self.get_recurrence()).get('UNTIL')
            if dt_string:
                return vDatetime.from_ical(dt_string).\
                    replace(tzinfo=UTC).astimezone(self.get_timezone())

    def get_rrule(self):
        if self._recurrence is not None:
            return rrulestr(str(self._recurrence), dtstart=self._start_datetime)
        return None

    def set_location(self, value):
        self._location = value

    security.declareProtected(
        SilvaPermissions.AccessContentsInformation, 'get_location')
    def get_location(self):
        return self._location

    def set_all_day(self, value):
        self._all_day = bool(value)

    security.declareProtected(
        SilvaPermissions.AccessContentsInformation, 'is_all_day')
    def is_all_day(self):
        return self._all_day

    security.declareProtected(
        SilvaPermissions.AccessContentsInformation, 'get_all_day')
    get_all_day = is_all_day


InitializeClass(AgendaItemOccurrence)


class AgendaItemVersion(NewsItemVersion):
    """Base class for agenda item versions.
    """
    security = ClassSecurityInfo()
    grok.implements(IAgendaItemVersion)
    grok.baseclass()

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

    security.declareProtected(
        SilvaPermissions.AccessContentsInformation, 'fulltext')
    def fulltext(self):
        """Deliver the contents as plain text, for full-text search
        """
        fulltext = [super(AgendaItemVersion, self).fulltext()]
        for occurrence in self.get_occurrences():
            fulltext.append(occurrence.get_location())
        return " ".join(fulltext)


InitializeClass(AgendaItemVersion)


class AgendaItemVersionCatalogingAttributes(
    NewsItemVersionCatalogingAttributes):
    grok.context(IAgendaItemVersion)

    def sort_index(self):
        occurrences = self.context.get_occurrences()
        if len(occurrences):
            dt = occurrences[0].get_start_datetime()
            if dt:
                return datetime_to_unixtimestamp(dt)
        return None

    def idx_timestamp_ranges(self):
        ranges = []
        for occurrence in self.context.get_occurrences():
            ranges.extend(
                occurrence.get_calendar_datetime().get_unixtimestamp_ranges())
        return ranges


class AgendaViewMixin(object):

    def event_img_url(self):
        return '%s/++resource++Products.SilvaNews/date.png' % \
            absoluteURL(self.context, self.request)

    def event_url(self):
        return "%s/event.ics" % absoluteURL(self.context, self.request)

    def occurrences(self):
        format = getUtility(IServiceNews).format_date
        for occurrence in self.content.get_occurrences():
            timezone = occurrence.get_timezone()
            yield {'start': format(occurrence.get_start_datetime(timezone),
                                   occurrence.is_all_day()),
                   'end': format(occurrence.get_end_datetime(timezone),
                                 occurrence.is_all_day()),
                   'location': occurrence.get_location()}



class AgendaItemView(NewsItemView, AgendaViewMixin):
    """ Index view for agenda items """
    grok.context(IAgendaItem)


class AgendaItemInlineView(silvaviews.View):
    """ Inline rendering for calendar event tooltip """
    grok.context(IAgendaItem)
    grok.name('tooltip.html')

    def update(self):
        self.intro = IntroHTML.transform(self.content, self.request)

    def render(self):
        return u'<div>' + self.intro + u"</div>"


class AgendaItemListItemView(NewsItemListItemView, AgendaViewMixin):
    """ Render as a list items (search results)
    """
    grok.context(IAgendaItem)


class AgendaItemICS(silvaviews.View):
    """Render an ics event.
    """
    grok.context(IAgendaItem)
    grok.require('zope2.View')
    grok.name('event.ics')

    def update(self):
        self.viewer = INewsViewer(self.context, None)
        self.factory = getMultiAdapter((self.content, self.request), IEvent)

    def render(self):
        cal = Calendar()
        cal.add('prodid', '-//Silva News Calendaring//lonely event//')
        cal.add('version', '2.0')
        for event in self.factory(self.viewer):
            cal.add_component(event)
        self.response.setHeader('Content-Type', 'text/calendar')
        return cal.as_string()


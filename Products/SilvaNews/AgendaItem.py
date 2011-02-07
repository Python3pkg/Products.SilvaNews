# Copyright (c) 2002-2011 Infrae. All rights reserved.
# See also LICENSE.txt
# $Revision: 1.21 $
from icalendar import vDatetime, Calendar
from zope.interface import implements
from zope.component import getAdapter, getUtility
from zope.traversing.browser import absoluteURL
from zope.cachedescriptors.property import CachedProperty
from five import grok

# Zope
from AccessControl import ClassSecurityInfo
from App.class_init import InitializeClass # Zope 2.12

# Silva interfaces
from Products.SilvaNews.interfaces import IAgendaItem, IAgendaItemVersion
from Products.SilvaNews.interfaces import INewsViewer

# Silva
from silva.core import conf as silvaconf
from silva.core.views import views as silvaviews
from Products.Silva import SilvaPermissions

# SilvaNews
from Products.SilvaNews.interfaces import IServiceNews
from Products.SilvaNews.NewsItem import (NewsItemView, NewsItemListItemView,
    IntroHTML)
from Products.SilvaNews.NewsItem import NewsItem, NewsItemVersion

from Products.SilvaNews.datetimeutils import (datetime_with_timezone,
    CalendarDatetime, datetime_to_unixtimestamp, get_timezone, RRuleData, UTC)
from icalendar.interfaces import IEvent
from dateutil.rrule import rrulestr

_marker = object()


class AgendaItem(NewsItem):
    """Base class for agenda items.
    """
    security = ClassSecurityInfo()
    implements(IAgendaItem)
    silvaconf.baseclass()

InitializeClass(AgendaItem)


class AgendaItemVersion(NewsItemVersion):
    """Base class for agenda item versions.
    """

    security = ClassSecurityInfo()

    _start_datetime = None
    _end_datetime = None
    _display_time = True
    _location = ''
    _recurrence = None
    _all_day = False
    _timezone_name = None

    implements(IAgendaItemVersion)
    silvaconf.baseclass()

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

    # indexes
    security.declareProtected(SilvaPermissions.AccessContentsInformation,
                              'idx_timestamp_ranges')
    def idx_timestamp_ranges(self):
        return self.get_calendar_datetime().\
            get_unixtimestamp_ranges()

    security.declareProtected(SilvaPermissions.AccessContentsInformation,
                              'idx_start_datetime')
    idx_start_datetime = get_start_datetime


InitializeClass(AgendaItemVersion)


class AgendaViewMixin(object):

    def event_img_url(self):
        return '%s/++resource++Products.SilvaNews/date.png' % \
            absoluteURL(self.context, self.request)

    def event_url(self):
        return "%s/event.ics" % absoluteURL(self.context, self.request)

    @CachedProperty
    def timezone(self):
        timezone = getattr(self.request, 'timezone', None)
        if not timezone:
            timezone = self.content.get_timezone()
        return timezone

    @CachedProperty
    def formatted_start_date(self):
        dt = self.content.get_start_datetime(self.timezone)
        if dt:
            service_news = getUtility(IServiceNews)
            return service_news.format_date(dt, not self.content.is_all_day())

    @CachedProperty
    def formatted_end_date(self):
        dt = self.content.get_end_datetime(self.timezone)
        if dt:
            service_news = getUtility(IServiceNews)
            return service_news.format_date(dt, not self.content.is_all_day())


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
    """ render an ics event
    """
    grok.context(IAgendaItem)
    grok.require('zope2.View')
    grok.name('event.ics')

    def update(self):
        self.viewer = INewsViewer(self.context, None)
        self.request.response.setHeader('Content-Type', 'text/calendar')
        self.content = self.context.get_viewable()
        self.event_factory = getAdapter(self.content, IEvent)

    def render(self):
        cal = Calendar()
        cal.add('prodid', '-//Silva News Calendaring//lonely event//')
        cal.add('version', '2.0')
        cal.add_component(self.event_factory(self.viewer, self.request))
        return cal.as_string()


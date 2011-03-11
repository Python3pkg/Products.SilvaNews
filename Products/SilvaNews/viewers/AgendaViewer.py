# Copyright (c) 2002-2011 Infrae. All rights reserved.
# See also LICENSE.txt
# $Id$

from datetime import datetime, date
from icalendar.interfaces import ICalendar
import calendar

from five import grok
from zope.component import getMultiAdapter, getUtility
from zope.traversing.browser import absoluteURL
from zope.intid.interfaces import IIntIds
from zope.interface import alsoProvides
from zope.cachedescriptors.property import CachedProperty
from zope.i18nmessageid import MessageFactory

# Zope
import Products
from AccessControl import ClassSecurityInfo
from App.class_init import InitializeClass

# Silva
from Products.Silva import SilvaPermissions
from silva.core import conf as silvaconf
from silva.core.layout.jquery.interfaces import IJQueryResources
from silva.core.views import views as silvaviews
from zeam.form import silva as silvaforms
from zope.publisher.interfaces.browser import IDefaultBrowserLayer

# SilvaNews
from Products.SilvaNews import datetimeutils
from Products.SilvaNews.interfaces import IAgendaItemVersion, IAgendaViewer
from Products.SilvaNews.interfaces import IServiceNews
from Products.SilvaNews.viewers.NewsViewer import NewsViewer
from Products.SilvaNews.htmlcalendar import HTMLCalendar
from Products.SilvaExternalSources.ExternalSource import ExternalSource

from zExceptions import BadRequest


_ = MessageFactory('silva_news')


class AgendaViewer(NewsViewer, ExternalSource):
    """
    Used to show agendaitems on a Silva site. When setting up an
    agendaviewer you can choose which agendafilters it should use to
    get the items from and how long in advance you want the items
    shown. The items will then automatically be retrieved from the
    agendafilter for each request.
    """
    security = ClassSecurityInfo()

    meta_type = "Silva Agenda Viewer"
    grok.implements(IAgendaViewer)
    silvaconf.icon("www/agenda_viewer.png")
    silvaconf.priority(3.3)

    show_in_tocs = 1

    def __init__(self, id):
        AgendaViewer.inheritedAttribute('__init__')(self, id)
        self._days_to_show = 31
        self._number_is_days = True
        self._starting_date = None

    security.declareProtected(SilvaPermissions.AccessContentsInformation,
                              'days_to_show')
    def days_to_show(self):
        """Returns number of days to show
        """
        return self._days_to_show

    
    security.declareProtected(SilvaPermissions.AccessContentsInformation,
                                'starting_date')
    def starting_date(self):
        """returns the starting date, if specified, for the day range"""
        return self._starting_date

    security.declareProtected(SilvaPermissions.AccessContentsInformation,
                              'get_items')
    def get_items(self):
        """Gets the items from the filters
        """
        func = lambda x: x.get_next_items(self._days_to_show,
                                          starting_date=self._starting_date)
        sortattr = None
        if len(self.get_filters()) > 1:
            sortattr = 'start_datetime'
        return self._get_items_helper(func,sortattr)

    security.declareProtected(SilvaPermissions.AccessContentsInformation,
                              'get_items_from_date')
    def get_items_from_date(self,date=None, sortattr='start_datetime'):
        return super(AgendaViewer, self).get_items_from_date(self, date, sortattr)

    security.declareProtected(SilvaPermissions.AccessContentsInformation,
                              'get_items_by_date')
    def get_items_by_date(self, month, year):
        """Gets the items from the filters
        """
        func = lambda x: x.get_agenda_items_by_date(month,year,
            timezone=self.get_timezone())
        sortattr = None
        if len(self.get_filters()) > 1:
            sortattr = 'start_datetime'
        results = self._get_items_helper(func,sortattr)
        return results

    security.declareProtected(SilvaPermissions.AccessContentsInformation,
                              'search_items')
    def search_items(self, keywords):
        """Search the items in the filters
        """
        allowed_meta_types = self.get_allowed_meta_types()
        func = lambda x: x.search_items(keywords,allowed_meta_types)
        sortattr = None
        if len(self.get_filters()) > 1:
            sortattr = 'start_datetime'
        results = self._get_items_helper(func,sortattr)
        return results

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

    security.declareProtected(SilvaPermissions.AccessContentsInformation,
                              'to_html')
    def to_html(self, content, request, **parameters):
        """ External Source rendering """
        view = getMultiAdapter((self, request), name='external_source')
        view.document = content.get_content()
        view.parameters = parameters
        return view()

    security.declareProtected(SilvaPermissions.ChangeSilvaContent,
                                'set_starting_date')
    def set_starting_date(self, date):
        """set self._starting_date"""
        self._starting_date = date

InitializeClass(AgendaViewer)


class ICalendarResources(IDefaultBrowserLayer):
    silvaconf.resource('calendar.css')


class AgendaViewerAddForm(silvaforms.SMIAddForm):
    grok.context(IAgendaViewer)
    grok.name(u"Silva Agenda Viewer")


def wrap_event_brains(viewer, iterable):
    for brain in iterable:
        item = brain.getObject()
        yield viewer.set_proxy(item)


class CalendarView(object):
    """Mixin for AgendaViewer view to help building HTML calendars

    The mixin provides a `build_calendar` method that fetches events
    from `start` to `end` and index them to help the rendering of a particular
    day in the calendar.

    Each time the calendar try to render a day, it calls `_render_day_callback`
    that allows to customize the rendering of a particular day. Events for that
    day are available in the index.
    """

    _events_index = {}

    @staticmethod
    def serialize_date(date):
        return date.strftime('%Y-%m-%d')

    def build_calendar(self, current_day, start, end,
                       today=None, store_events_in_index=False):
        """ Build a HTMLCalendar where :

        - `current_day` (date) is the selected day
        - `today` (date) defaults to today
        - `start` (datetime) and `end` (datetime)
           is the range for loading the events
        - `store_events_in_index` determine if event are stored in index
        or just the fact that a event is present.
        """
        self._store_events_in_index = store_events_in_index
        today = today or datetime.now(self.context.get_timezone()).date()

        events = wrap_event_brains(
            self.context,
            self.context.get_items_by_date_range(start, end))
        acalendar = HTMLCalendar(
            self.context.get_first_weekday(),
            today=today,
            current_day=current_day or today,
            day_render_callback=self._render_day_callback)
        for event in events:
            self._register_event(acalendar, event, start, end)
        return acalendar

    def _register_event(self, acalendar, event, start, end):
        """ index all the days for which the event has an occurrence between
        start and end.
        """
        cd = event.get_calendar_datetime()
        for datetime_range in cd.get_datetime_ranges(start, end):
            for occurence in datetimeutils.DayWalk(datetime_range[0],
                                                   datetime_range[1],
                                                   self.context.get_timezone()):
                self._index_event(occurence, event)

    def _index_event(self, adate, event):
        """ (internal) actual indexing of an event.
        """
        serial = self.serialize_date(adate)
        if self._store_events_in_index:
            day_events = self._events_index.get(serial, [])
            day_events.append(event)
            self._events_index[serial] = day_events
        else:
            self._events_index[serial] = True

    def _render_day_callback(self, day, weekday, week, year, month):
        """Callback for the html calendar to render every day"""
        try:
            event_date = date(year, month, day)
            events = self._events_index.get(self.serialize_date(event_date))
            if events:
                return self._render_events(event_date, events)
        except ValueError:
            pass
        return u'', unicode(day)

    def _render_events(self, date, events):
        """render a day for which there is events in the index"""
        cal_url = absoluteURL(self.context, self.request)
        return ('event',
                '<a href="%s?day=%d&amp;month=%d&amp;year=%d">%d</a>' % \
            (cal_url, date.day, date.month, date.year, date.day))


class AgendaViewerExternalSourceView(silvaviews.View, CalendarView):
    """
    Month calendar to be rendered as external source inside a
    Silva Document
    """
    grok.context(IAgendaViewer)
    grok.name('external_source')

    document = None
    parameters = {}

    def update(self):
        timezone = self.context.get_timezone()
        today = datetime.now(timezone).date()

        self.year = today.year
        self.month = today.month

        firstweekday, lastday = calendar.monthrange(
            self.year, self.month)

        self.start = datetime(self.year, self.month, 1, tzinfo=timezone)
        self.end = datetime(self.year, self.month, lastday, 23, 59, 59,
                       tzinfo=timezone)

        self.calendar = self.build_calendar(
            today, self.start, self.end, today=today)

    def render(self):
        return self.calendar.formatmonth(self.year, self.month)


class AgendaViewerMonthCalendar(silvaviews.View, CalendarView):
    """ View with month calendar and listing of event registered of the
    selected day"""
    grok.context(IAgendaViewer)

    @CachedProperty
    def context_absolute_url(self):
        return absoluteURL(self.context, self.request)

    def item_calevent_url(self, newsitem):
        return str(absoluteURL(newsitem, self.request)) + '/event.ics'

    def item_id(self, news_item):
        util = getUtility(IIntIds)
        return "event_%s" % util.register(self.context)

    @property
    def archive_url(self):
        return self.context_absolute_url + '/archives'

    def update(self):
        alsoProvides(self.request, ICalendarResources)
        now = datetime.now(self.context.get_timezone())
        self.month = int(self.request.get('month', now.month))
        self.year = int(self.request.get('year', now.year))

        now_year = now.year
        years = self.context.get_year_range()
        year_range = range(now_year - years, now_year + years + 1)
        if self.year not in year_range:
            raise BadRequest('year out of range')

        (first_weekday, lastday,) = calendar.monthrange(
            self.year, self.month)
        self.day = int(self.request.get('day', now.day)) or 1
        self.day_datetime = datetime(self.year, self.month, self.day,
                                     tzinfo=self.context.get_timezone())

        self.start = datetimeutils.start_of_month(self.day_datetime)
        self.end = datetimeutils.end_of_month(self.day_datetime)

        self._day_events = self._selected_day_events()
        self.calendar = self.build_calendar(
            self.day_datetime.date(), self.start, self.end, now.date())

        self._set_calendar_nav()

    def next_month_url(self):
        year = self.start.year
        month = self.start.month + 1
        if month == 13:
            month = 1
            year = year + 1
        return "%s?month=%d&amp;year=%d&amp;day=1" % (
            self.context_absolute_url, month, year)

    def prev_month_url(self):
        year = self.start.year
        month = self.start.month - 1
        if month == 0:
            month = 12
            year = year - 1
        return "%s?month=%d&amp;year=%d&amp;day=1" % (
                self.context_absolute_url, month, year)

    def intro(self):
        service = getUtility(IServiceNews)
        day = service.format_date(
            self.day_datetime, display_time=False, size="full")
        if self._day_events:
            return _(u"Events on ${day}", mapping={'day': day})
        return _(u"No events on ${day}", mapping={'day': day})

    def subscribe_url(self):
        return "%s/subscribe.html" % self.context_absolute_url

    def day_events(self):
        return self._day_events

    def render_calendar(self):
        return self.calendar.formatmonth(self.year, self.month)

    def _selected_day_events(self):
        items = self.context.get_items_by_date_range(
                    datetimeutils.start_of_day(self.day_datetime),
                    datetimeutils.end_of_day(self.day_datetime))
        return map(lambda x: x.get_content(),
                    wrap_event_brains(self.context, items))

    def can_prev(self):
        year_range = self.context.get_year_range()
        prev_year = self.year
        cur_year = datetime.now().year
        if self.month == 1:
            prev_year = self.year - 1
        if cur_year > prev_year and (cur_year - prev_year) > year_range:
            return False
        return True

    def can_next(self):
        year_range = self.context.get_year_range()
        cur_year = datetime.now().year
        next_year = self.year
        if self.month == 12:
            next_year = self.year + 1
        if cur_year < next_year and (next_year - cur_year) > year_range:
            return False
        return True

    def _set_calendar_nav(self):
        self.calendar.prev_link = self.can_prev() and \
            '<a class="prevmonth caljump" href="%s">&lt;</a>' % \
                self.prev_month_url()
        self.calendar.next_link = self.can_next() and \
            '<a class="nextmonth caljump" href="%s">&gt</a>' % \
                self.next_month_url()


class AgendaViewerYearCalendar(silvaviews.Page, CalendarView):
    """ Year Calendar representation
    """
    grok.context(IAgendaViewer)
    grok.name('year')

    def update(self):
        alsoProvides(self.request, ICalendarResources)
        timezone = self.context.get_timezone()
        now = datetime.now()
        self.year = int(self.request.get('year', now.year))

        now_year = now.year
        years = self.context.get_year_range()
        year_range = range(now_year - years, now_year + years + 1)
        if self.year not in year_range:
            raise BadRequest('year out of range')

        self.start = datetime(self.year, 1, 1, tzinfo=timezone)
        self.end = datetimeutils.end_of_year(self.start)
        self.calendar = self.build_calendar(
            self.start.date(), self.start, self.end, now.date())

    def render(self):
        return self.calendar.formatyear(self.year)


class IViewResources(IJQueryResources):
    silvaconf.resource('fullcalendar/fullcalendar.js')
    silvaconf.resource('calendar.js')
    silvaconf.resource('qtip.js')
    silvaconf.resource('fullcalendar/fullcalendar.css')
    silvaconf.resource('qtip.css')


class AgendaViewerJSCalendar(silvaviews.Page):
    """ Agenda view advanced javascript calendar """
    grok.context(IAgendaViewer)
    grok.name('fullcalendar')

    def update(self):
        alsoProvides(self.request, IViewResources)

    @property
    def events_json_url(self):
        return absoluteURL(self.context, self.request) + '/++rest++events'


class AgendaViewerICSCalendar(silvaviews.View):
    """ Agenda viewer ics format """
    grok.context(IAgendaViewer)
    grok.name('calendar.ics')

    def update(self):
        self.request.timezone = self.context.get_timezone()
        self.request.response.setHeader('Content-Type', 'text/calendar')
        self.calendar = getMultiAdapter(
            (self.context, self.request,), ICalendar)

    def render(self):
        return self.calendar.as_string()


class AgendaViewerSubscribeView(silvaviews.Page):
    """ View that display the Subcribe url to the calendar """
    grok.context(IAgendaViewer)
    grok.name('subscribe.html')

    def update(self):
        self.request.timezone = self.context.get_timezone()

    def calendar_url(self):
        return "%s/calendar.ics" % absoluteURL(self.context, self.request)

from five import grok
from zope.component import getUtility
from zope.intid.interfaces import IIntIds
from icalendar import Calendar, Event, vText, vDatetime, vDate
from icalendar.interfaces import ICalendar, IEvent
from Products.SilvaNews.interfaces import IAgendaItemVersion, IAgendaViewer
from Products.SilvaNews.datetimeutils import UTC
from datetime import date, datetime
from dateutil.relativedelta import relativedelta
from zope.interface import Interface
from zope.traversing.browser import absoluteURL


class AgendaFactoryEvent(grok.Adapter):
    grok.context(IAgendaItemVersion)
    grok.implements(IEvent)
    grok.provides(IEvent)

    def __call__(self, viewer, request):
        return AgendaEvent(self.context, request, viewer)


class AgendaEvent(Event):

    def __init__(self, context, request, viewer=None):
        super(AgendaEvent, self).__init__()
        intid = getUtility(IIntIds)
        timezone = (viewer and viewer.get_timezone()) or context.get_timezone()
        cdate = context.get_calendar_datetime()
        start_dt = cdate.get_start_datetime(timezone)
        end_dt = cdate.get_end_datetime(timezone)
        if context.is_all_day():
            start_date = date(start_dt.year, start_dt.month, start_dt.day)
            # end date is exclusive
            end_date = date(end_dt.year, end_dt.month, end_dt.day) + \
                relativedelta(days=+1)
            self['DTSTART'] = vDate(start_date)
            if end_date != start_date:
                self['DTEND'] = vDate(end_date)
        else:
            self['DTSTART'] = vDatetime(start_dt.astimezone(UTC))
            self['DTEND'] = vDatetime(end_dt.astimezone(UTC))

        rrule_string = context.get_recurrence()
        if rrule_string is not None:
            self['RRULE'] = rrule_string

        self['UID'] = "%d@silvanews" % intid.register(context.get_content())
        if context.get_location():
            self['LOCATION'] = vText(context.get_location())
        self['SUMMARY'] = vText(context.get_title())
        self['URL'] = absoluteURL(context, request)


class AgendaCalendar(Calendar, grok.MultiAdapter):
    grok.adapts(IAgendaViewer, Interface)
    grok.implements(ICalendar)
    grok.provides(ICalendar)

    def __init__(self, context, request):
        super(AgendaCalendar, self).__init__()
        self.context = context
        self.request = request
        self['PRODID'] = \
            vText('-//Infrae SilvaNews Calendaring//NONSGML Calendar//EN')
        self['VERSION'] = '2.0'
        self['X-WR-CALNAME'] = vText(self.context.get_title())
        self['X-WR-TIMEZONE'] = vText(self.context.get_timezone_name())
        now = datetime.now(UTC)
        for brain in self.context.get_items_by_date_range(
                now + relativedelta(years=-1), now + relativedelta(years=+1)):
            agenda_item_version = brain.getObject()
            content = agenda_item_version.get_content()
            self.context.set_proxy(content)
            event_factory = AgendaFactoryEvent(agenda_item_version)
            event = event_factory(self.context, self.request)
            if event is not None:
                self.add_component(event)


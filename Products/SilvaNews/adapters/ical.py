# Copyright (c) 2002-2011 Infrae. All rights reserved.
# See also LICENSE.txt
# $Id$

from icalendar import Calendar, Event, vText, vDatetime, vDate
from icalendar.interfaces import ICalendar, IEvent
from datetime import date, datetime
from dateutil.relativedelta import relativedelta

from five import grok
from zope.component import getUtility, getMultiAdapter
from zope.intid.interfaces import IIntIds
from zope.publisher.interfaces.browser import IBrowserRequest
from zope.traversing.browser import absoluteURL

from Products.SilvaNews.datetimeutils import UTC
from Products.SilvaNews.interfaces import IAgendaItemVersion, IAgendaViewer


class AgendaFactoryEvent(grok.MultiAdapter):
    grok.adapts(IAgendaItemVersion, IBrowserRequest)
    grok.implements(IEvent)
    grok.provides(IEvent)

    def __init__(self, context, request):
        self.context = context
        self.request = request

    def __call__(self, viewer):
        title = self.context.get_title()
        url = absoluteURL(self.context, self.request)
        base = getUtility(IIntIds).register(self.context)
        for index, occurrence in enumerate(self.context.get_occurrences()):
            uid = "%d@%d@silvanews" % (base, index)
            yield AgendaEvent(title, url, uid, occurrence, viewer)


class AgendaEvent(Event):

    def __init__(self, title, url, uid, occurrence, viewer=None):
        super(AgendaEvent, self).__init__()
        if viewer is not None:
            timezone = viewer.get_timezone()
        else:
            timezone = occurrence.get_timezone()
        cdate = occurrence.get_calendar_datetime()
        start_dt = cdate.get_start_datetime(timezone)
        end_dt = cdate.get_end_datetime(timezone)
        if occurrence.is_all_day():
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

        rrule_string = occurrence.get_recurrence()
        if rrule_string is not None:
            self['RRULE'] = rrule_string
        location = occurrence.get_location()
        if location:
            self['LOCATION'] = vText(location)

        self['UID'] = uid
        self['SUMMARY'] = vText(title)
        self['URL'] = url


class AgendaCalendar(Calendar, grok.MultiAdapter):
    grok.adapts(IAgendaViewer, IBrowserRequest)
    grok.implements(ICalendar)
    grok.provides(ICalendar)

    def __init__(self, context, request):
        super(AgendaCalendar, self).__init__()
        self['PRODID'] = \
            vText('-//Infrae SilvaNews Calendaring//NONSGML Calendar//EN')
        self['VERSION'] = '2.0'
        self['X-WR-CALNAME'] = vText(context.get_title())
        self['X-WR-TIMEZONE'] = vText(context.get_timezone_name())
        now = datetime.now(UTC)
        for brain in context.get_items_by_date_range(
                now + relativedelta(years=-1), now + relativedelta(years=+1)):

            factory = getMultiAdapter((brain.getObject(), request), IEvent)
            for event in factory(context):
                self.add_component(event)


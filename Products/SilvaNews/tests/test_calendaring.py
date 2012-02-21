# coding=utf-8

from difflib import unified_diff
from os import linesep
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta

from zope.component import getUtility
from zope.intid.interfaces import IIntIds

from silva.core.services.interfaces import ICatalogingAttributes
from Products.SilvaNews.tests.SilvaNewsTestCase import (SilvaNewsTestCase,
    NewsBaseTestCase)
from Products.SilvaNews.datetimeutils import (local_timezone,
    datetime_to_unixtimestamp, get_timezone)


def format_date(date):
    if date is None:
        return ''
    return date.utcdatetime().strftime('%Y%m%dT%H%M%SZ')


class TestEvent(SilvaNewsTestCase):

    def test_event_indexing(self):
        start = datetime.now(local_timezone)
        event = self.add_published_agenda_item(self.root, 'ai1',
            'Agenda Item', start, start + timedelta(60))

        version = event.get_viewable()
        # make sure it does not raise
        self.assertNotEquals(
            ICatalogingAttributes(version).idx_timestamp_ranges(), [])

        start_index = datetime_to_unixtimestamp(start)
        end_index = datetime_to_unixtimestamp(start + timedelta(30))
        brains = self.root.service_catalog(
            {'idx_timestamp_ranges': {'query': [start_index, end_index]}})
        l = [brain.getObject() for brain in brains]
        self.assertEqual(l, [version])

        start_index = datetime_to_unixtimestamp(start - timedelta(30))
        end_index = datetime_to_unixtimestamp(start - timedelta(20))
        brains = self.root.service_catalog(
            {'idx_timestamp_ranges': {'query': [start_index, end_index]}})
        self.assertFalse(brains)


class TestAgendaViewerLookup(NewsBaseTestCase):

    def setUp(self):
        super(TestAgendaViewerLookup, self).setUp()
        self.tz = get_timezone('Europe/Amsterdam')
        root = self.layer.get_application()
        factory = root.manage_addProduct['SilvaNews']
        factory.manage_addAgendaFilter('agenda_filter', 'Agenda Filter')
        factory.manage_addAgendaViewer('agenda_viewer', 'Agenda Viewer')
        self.root.agenda_viewer.set_timezone_name('Europe/Amsterdam')
        factory.manage_addNewsPublication(
            'news_publication', 'News Publication')

        self.root.agenda_filter.set_sources([self.root.news_publication])
        self.root.agenda_filter.set_subjects(['sub'])
        self.root.agenda_filter.set_target_audiences(['ta'])

        self.root.agenda_viewer.set_filters([self.root.agenda_filter])

        self.news_pub_factory = \
            self.root.news_publication.manage_addProduct['SilvaNews']

    def test_month_lookup(self):
        self.add_published_agenda_item(
            self.root.news_publication,
            'start_before_month',
            'This agenda item starts before the month and ends at the'
            'beginning of the month',
            datetime(2010, 10, 23, 12, 20, tzinfo=self.tz),
            datetime(2010, 11, 2, 12, 00, tzinfo=self.tz))

        self.add_published_agenda_item(
            self.root.news_publication,
            'end_after_month',
            'This agenda item ends before after the month ends',
            datetime(2010, 11, 23, 12, 20, tzinfo=self.tz),
            datetime(2010, 12, 2, 12, 00, tzinfo=self.tz))

        self.add_published_agenda_item(
            self.root.news_publication,
            'out_of_range',
            'This agenda item is not found it is out of range',
            datetime(2010, 10, 23, 12, 20, tzinfo=self.tz),
            datetime(2010, 10, 30, 12, 00, tzinfo=self.tz))

        self.add_published_agenda_item(
            self.root.news_publication,
            'over_month',
            'This agenda item starts before month starts'
            'and ends after month ends',
            datetime(2010, 10, 23, 12, 20, tzinfo=self.tz),
            datetime(2010, 12, 3, 02, 00, tzinfo=self.tz))

        self.add_published_agenda_item(
            self.root.news_publication,
            'within_month',
            'This agenda item starts after month starts'
            'and ends before month ends',
            datetime(2010, 11, 23, 12, 20, tzinfo=self.tz),
            datetime(2010, 11, 23, 22, 00, tzinfo=self.tz))

        versions = set([
            self.root.news_publication.start_before_month.get_viewable(),
            self.root.news_publication.end_after_month.get_viewable(),
            self.root.news_publication.over_month.get_viewable(),
            self.root.news_publication.within_month.get_viewable(),
            ])

        agenda = self.root.agenda_viewer

        def normalize(results):
            return set(map(lambda x: x.getObject(), items))

        items = agenda.get_items_by_date(11, 2010)
        self.assertEquals(versions, normalize(items))

        items = agenda.get_items_by_date_range(
            datetime(2010, 11, 1, 00, 00, tzinfo=self.tz),
            datetime(2010, 11, 30, 23, 59, 59, tzinfo=self.tz))
        self.assertEquals(versions, normalize(items))


class TestCalendar(NewsBaseTestCase):

    def setUp(self):
        super(TestCalendar, self).setUp()
        self.browser = self.layer.get_browser()
        self.browser.options.handle_errors = False
        self.filter = self.add_agenda_filter(
            self.root, 'afilter', 'Agenda Filter')
        self.filter.set_subjects(['sub'])
        self.filter.set_target_audiences(['ta'])
        self.filter.set_sources([self.source1])
        self.agenda = self.add_agenda_viewer(self.root, 'agenda', 'Agenda')
        self.agenda.set_filters([self.root.afilter])
        self.agenda.set_timezone_name('Europe/Amsterdam')

        sdt = datetime(2012, 6, 4, 10, 20, tzinfo=self.agenda.get_timezone())
        self.event1 = self.add_published_agenda_item(
            self.source1, 'event1', u'Event héhé“π”',
            sdt, sdt + relativedelta(hours=+1))

        sdt = datetime(2012, 6, 10, 10, 20, tzinfo=self.agenda.get_timezone())
        self.event2 = self.add_published_agenda_item(
            self.source1, 'event2', u'Event2',
            sdt, sdt + relativedelta(days=+1), all_day=True)

    def get_intid(self, obj):
        return getUtility(IIntIds).getId(obj)

    def test_calendar_view(self):
        status = self.browser.open('http://localhost/root/agenda')
        self.assertEquals(200, status)

    def test_calendar_view_for_event(self):
        status = self.browser.open('http://localhost/root/agenda',
                                   query={'year' : '2012',
                                          'month': '6',
                                          'day'  : '4'})
        self.assertEquals(200, status)

        xpath = '//div[@id="event_%s"]' % self.get_intid(
            self.event1.get_viewable())
        nodes = self.browser.html.xpath(xpath)
        self.assertTrue(1, len(nodes))

    def test_external_source_view(self):
        status = self.browser.open(
            'http://localhost/root/agenda/external_source')
        self.assertEquals(200, status)

    def test_subscribe_view(self):
        status = self.browser.open(
            'http://localhost/root/agenda/subscribe.html')
        self.assertEquals(200, status)

    def test_ics_view(self):
        status = self.browser.open(
            'http://localhost/root/agenda/calendar.ics')
        self.assertEquals(200, status)
        get_id = getUtility(IIntIds).register
        v1 = self.event2.get_viewable()
        v2 = self.event1.get_viewable()
        data = """BEGIN:VCALENDAR
PRODID:-//Infrae SilvaNews Calendaring//NONSGML Calendar//EN
VERSION:2.0
X-WR-CALNAME:Agenda
X-WR-TIMEZONE:Europe/Amsterdam
BEGIN:VEVENT
CREATED:{created1}
DTEND;VALUE=DATE:20120612
DTSTART;VALUE=DATE:20120610
LAST-MODIFIED:{modified1}
SUMMARY:Event2
UID:{id1}@0@silvanews
URL:http://localhost/root/source1/event2
END:VEVENT
BEGIN:VEVENT
CREATED:{created2}
DTEND:20120604T092000Z
DTSTART:20120604T082000Z
LAST-MODIFIED:{modified2}
SUMMARY:Event héhé“π”
UID:{id2}@0@silvanews
URL:http://localhost/root/source1/event1
END:VEVENT
END:VCALENDAR
""".replace("\n", "\r\n").format(
            id1=get_id(v1),
            created1=format_date(v1.get_creation_datetime()),
            modified1=format_date(v1.get_modification_datetime()),
            id2=get_id(v2),
            created2=format_date(v2.get_creation_datetime()),
            modified2=format_date(v2.get_modification_datetime()))
        self.assert_no_udiff(data, self.browser.contents, term="\r\n")

    def assert_no_udiff(self, s1, s2, term="\n"):
        diff = list(unified_diff(s1.split(term), s2.split(term)))
        if len(diff) > 0:
            raise AssertionError(linesep.join(diff))
        return True


import unittest
def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TestEvent))
    suite.addTest(unittest.makeSuite(TestCalendar))
    suite.addTest(unittest.makeSuite(TestAgendaViewerLookup))
    return suite

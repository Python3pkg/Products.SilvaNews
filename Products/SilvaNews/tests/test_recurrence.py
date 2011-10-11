import unittest
from icalendar import vDatetime
from DateTime import DateTime
from datetime import datetime
from dateutil.relativedelta import relativedelta

from zope.component import getUtility

from Products.SilvaNews.AgendaItem import AgendaItemOccurrence
from Products.SilvaNews.datetimeutils import (
    datetime_to_unixtimestamp, get_timezone)
from Products.SilvaNews.tests.SilvaNewsTestCase import FunctionalLayer
from silva.core.services.interfaces import ICatalogService


class TestAgendaItemRecurrence(unittest.TestCase):

    layer = FunctionalLayer

    def setUp(self):
        self.root = self.layer.get_application()

    def test_occurrence_item_without_recurrence(self):
        dt = datetime(2010, 10, 9, 10, 1)
        occurrence = AgendaItemOccurrence(
            start_datetime=dt, end_datetime=dt + relativedelta(hours=+2))
        self.assertEquals(occurrence.get_rrule(), None)

    def test_occurrence_with_recurrence(self):
        dt = datetime(2010, 9, 10, 10, 0)
        # every two weeks
        occurrence = AgendaItemOccurrence(
            timezone_name='Europe/Amsterdam',
            start_datetime=dt,
            end_datetime=dt + relativedelta(hours=+2),
            recurrence='FREQ=WEEKLY;INTERVAL=2;BYDAY=FR',
            end_recurrence_datetime=dt + relativedelta(months=+1))

        recurrence = occurrence.get_rrule()
        self.assertNotEquals(recurrence, None)
        tz = get_timezone('Europe/Amsterdam')
        self.assertEquals(
            [datetime(2010, 9, 10, 10, 0, tzinfo=tz),
             datetime(2010, 9, 24, 10, 0, tzinfo=tz),
             datetime(2010, 10, 8, 10, 0, tzinfo=tz)],
            list(recurrence))

        calendar_date = occurrence.get_calendar_datetime()
        ranges = calendar_date.get_datetime_ranges()
        self.assertEquals(
            [(datetime(2010, 9, 10, 10, 0, tzinfo=tz),
              datetime(2010, 9, 10, 12, 0, tzinfo=tz)),
             (datetime(2010, 9, 24, 10, 0, tzinfo=tz),
              datetime(2010, 9, 24, 12, 0, tzinfo=tz)),
             (datetime(2010, 10, 8, 10, 0, tzinfo=tz),
              datetime(2010, 10, 8, 12, 0, tzinfo=tz))],
            ranges)

    def test_catalog(self):
        dt = datetime(2010, 9, 10, 10, 0)

        # every two weeks
        occurrence = AgendaItemOccurrence(
            timezone_name='Europe/Amsterdam',
            start_datetime=dt,
            end_datetime=dt + relativedelta(hours=+2),
            recurrence='FREQ=WEEKLY;INTERVAL=2;BYDAY=FR',
            end_recurrence_datetime=dt + relativedelta(months=+1))

        # last for one month
        recurrence = occurrence.get_rrule()
        self.assertNotEquals(recurrence, None)

        factory = self.root.manage_addProduct['Products.SilvaNews']
        factory.manage_addPlainAgendaItem('event', 'Event')
        version = self.root.event.get_editable()
        version.set_occurrences([occurrence])
        self.root.event.set_unapproved_version_publication_datetime(DateTime())
        self.root.event.approve_version()

        catalog = getUtility(ICatalogService)
        tz = get_timezone('Europe/Amsterdam')
        start = datetime_to_unixtimestamp(
            datetime(2010, 9, 10, 0, 0, tzinfo=tz))
        end = datetime_to_unixtimestamp(
            datetime(2010, 9, 10, 23, 59, tzinfo=tz))

        def search():
            return map(lambda x: x.getObject(),
                       catalog({'idx_timestamp_ranges': [start, end]}))

        self.assertEquals([version], search())

        start = datetime_to_unixtimestamp(
            datetime(2010, 9, 24, 10, 0, tzinfo=tz))
        end = datetime_to_unixtimestamp(
            datetime(2010, 9, 24, 12, 0, tzinfo=tz))
        self.assertEquals([version], search())

        start = datetime_to_unixtimestamp(
            datetime(2010, 10, 8, 11, 0, tzinfo=tz))
        end = datetime_to_unixtimestamp(
            datetime(2010, 10, 8, 13, 0, tzinfo=tz))
        self.assertEquals([version], search())


def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TestAgendaItemRecurrence))
    return suite

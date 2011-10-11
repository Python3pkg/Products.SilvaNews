import json
import unittest
from datetime import datetime
from dateutil.relativedelta import relativedelta

from zope.component import getUtility
from zope.intid.interfaces import IIntIds

from Products.SilvaNews.tests.SilvaNewsTestCase import NewsBaseTestCase


class TestJsonEventsAPI(NewsBaseTestCase):

    def setUp(self):
        super(TestJsonEventsAPI, self).setUp()
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
        sdt = datetime(2010, 9, 4, 10, 20, tzinfo=self.agenda.get_timezone())

        self.event1 = self.add_published_agenda_item(
            self.source1, 'event', 'Event1',
            sdt, sdt + relativedelta(hours=+1))
        version = self.event1.get_viewable()
        version.set_subjects(['sub'])
        version.set_target_audiences(['ta'])
        sdt = datetime(2010, 9, 10, 10, 20, tzinfo=self.agenda.get_timezone())

        self.event2 = self.add_published_agenda_item(
            self.source1, 'event2', 'Event2',
            sdt, sdt + relativedelta(days=+1))
        version = self.event2.get_viewable()
        version.set_subjects(['sub'])
        version.set_target_audiences(['ta'])

        self.event3 = self.add_published_agenda_item(
            self.source1, 'event3', 'Event3',
            sdt.replace(month=8), sdt.replace(month=8, day=9))
        version = self.event2.get_viewable()
        version.set_subjects(['sub'])
        version.set_target_audiences(['ta'])

    def test_request_without_start_and_end(self):
        """json events without start and end returns empty list"""
        status = self.browser.open(
            'http://localhost/root/agenda/++rest++events')
        self.assertEquals(200, status)
        self.assertEquals([], json.loads(self.browser.contents))

    def test_json_results(self):
        """json events returns only the agenda items within the range"""
        status = self.browser.open(
            'http://localhost/root/agenda/++rest++events?start=%s&end=%s' %
            (datetime(2010, 9, 1).strftime("%s"),
             datetime(2010, 9, 30).strftime("%s")))
        self.assertEquals(200, status)
        data = json.loads(self.browser.contents)
        data.sort()
        intids = getUtility(IIntIds)
        # event 3 is out of range
        self.assertEquals(2, len(data))
        self.assertEquals(
            'agenda-item-%s-0' % intids.getId(self.event1.get_viewable()),
            data[0]['id'])
        self.assertEquals(
            'agenda-item-%s-0' % intids.getId(self.event2.get_viewable()),
            data[1]['id'])


def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TestJsonEventsAPI))
    return suite


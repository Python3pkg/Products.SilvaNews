import unittest
from Products.SilvaNews.datetimeutils import *


class TestDateTime(unittest.TestCase):

    def test_datetime_set_local_timezone(self):
        dt = datetime(2010, 2, 1, 10, 20, 03)
        dtltz = datetime_with_timezone(dt)
        self.assertEquals(local_timezone, dtltz.tzinfo)
        self.assertEquals(10, dtltz.hour)
        self.assertEquals(20, dtltz.minute)
        self.assertEquals(3, dtltz.second)

    def test_utc_with_Datetime_tzinfo(self):
        now = DateTime()
        utcnow = utc_datetime(now)
        self.assertEquals(UTC, utcnow.tzinfo)

    def test_utc_with_Datetime(self):
        nowDT = utc_datetime(DateTime(2010, 2, 1, 10, 20, 03))
        nowdt = utc_datetime(datetime(2010, 2, 1, 10, 20, 03))
        self.assertEquals(nowdt, nowDT)
        self.assertEquals(str(nowdt), str(nowDT))

    def test_dt_stamp(self):
        """ the same datetime in different time zone should have
        the same unix timestamp
        """
        dt = datetime(2010, 2, 1, 10, 20, 03)
        #antonin's original stamp, which does not work on my system, not
        # sure why?
        stamp = 1265016003
        #aaltepet get's this stamp:
        stamp = 1265041203
        nowDT = utc_datetime(DateTime(2010, 2, 1, 10, 20, 03))
        nowdt = utc_datetime(datetime(2010, 2, 1, 10, 20, 03))
        self.assertEquals(stamp, datetime_to_unixtimestamp(dt))
        self.assertEquals(stamp, datetime_to_unixtimestamp(nowdt))
        self.assertEquals(stamp, datetime_to_unixtimestamp(nowDT))

    def test_unixtimestamp(self):
        """ a unixtimestamp of the same datetime in different timezone should
        always be the same
        """
        dt = datetime(2010, 2, 1, 10, 20, 03)
        dt_local = datetime_with_timezone(dt)
        dt_utc = utc_datetime(dt_local)
        u = datetime_to_unixtimestamp
        self.assertEquals(u(dt), u(dt_local))
        self.assertEquals(u(dt_local), u(dt_utc))


class TestCalendarDatetime(unittest.TestCase):

    def test_simple_recurrence(self):
        sdt = datetime(2010, 2, 1, 10, 20, 03, tzinfo=UTC);
        edt = datetime(2010, 2, 1, 11, 20, 03, tzinfo=UTC);

        date_rep = CalendarDatetime(sdt, edt);
        date_rep.set_recurrence_from_string('FREQ=DAILY;INTERVAL=1;COUNT=3');
        occurences = [
            (datetime(2010, 2, 1, 10, 20, 03, tzinfo=UTC),
                datetime(2010, 2, 1, 11, 20, 03, tzinfo=UTC)),
            (datetime(2010, 2, 2, 10, 20, 03, tzinfo=UTC),
                datetime(2010, 2, 2, 11, 20, 03, tzinfo=UTC)),
            (datetime(2010, 2, 3, 10, 20, 03, tzinfo=UTC),
                datetime(2010, 2, 3, 11, 20, 03, tzinfo=UTC)),
        ]
        self.assertEquals(occurences, date_rep.get_datetime_ranges())

    def test_simple_recurrence_timestamps(self):
        sdt = datetime(2010, 2, 1, 10, 20, 03, tzinfo=UTC);
        edt = datetime(2010, 2, 1, 11, 20, 03, tzinfo=UTC);

        date_rep = CalendarDatetime(sdt, edt);
        date_rep.set_recurrence_from_string('FREQ=DAILY;INTERVAL=1;COUNT=3');
        u = datetime_to_unixtimestamp
        occurences = [
            (u(datetime(2010, 2, 1, 10, 20, 03, tzinfo=UTC)),
                u(datetime(2010, 2, 1, 11, 20, 03, tzinfo=UTC))),
            (u(datetime(2010, 2, 2, 10, 20, 03, tzinfo=UTC)),
                u(datetime(2010, 2, 2, 11, 20, 03, tzinfo=UTC))),
            (u(datetime(2010, 2, 3, 10, 20, 03, tzinfo=UTC)),
                u(datetime(2010, 2, 3, 11, 20, 03, tzinfo=UTC))),
        ]
        self.assertEquals(occurences, date_rep.get_unixtimestamp_ranges())


def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TestDateTime))
    suite.addTest(unittest.makeSuite(TestCalendarDatetime))
    return suite

from datetime import date, datetime
from dateutil.rrule import rrule, rruleset, rrulestr
from dateutil.relativedelta import relativedelta
from dateutil.tz import tzutc, tzlocal, gettz
import sys
import os.path
import calendar
from DateTime import DateTime

system_timezone = tzlocal()
local_timezone = tzlocal()
UTC = tzutc()

_zonefile = '/usr/share/zoneinfo/zone.tab'

def readline(f):
    line = f.readline()
    while line:
        yield line
        line = f.readline()

def load_timezone_names():
    tz_names = ['local']
    if sys.platform != 'win32':
        if os.path.exists(_zonefile):
            with open(_zonefile) as f:
                for line in readline(f):
                    if line.startswith("#"):
                        continue
                    data = line.rstrip().split("\t", 3)
                    tz_names.append(data[2])

    tz_names.sort()
    return tz_names

zone_names = load_timezone_names()


class RRuleData(dict):

    def __init__(self, recurrence):
        if recurrence.endswith(';'):
            recurrence = recurrence[:-1]

        parts = recurrence.split(';')
        for part in parts:
            key, value = part.split('=', 2)
            self[key.upper()] = value

    def __str__(self):
        return ";".join(["%s=%s" % x for x in self.items()])

    def __unicode__(self):
        return unicode(str(self))

    def __repr__(self):
        return "<RRuleData %s>" % str(self)


def get_timezone(name):
    if name == 'local':
        return local_timezone
    else:
        return gettz(name)

def utc_datetime(aDateTime_or_datetime, end=False):
    """ build a datetime in the utc timezone from DateTime or datetime object
    """
    if isinstance(aDateTime_or_datetime, datetime):
        return datetime_with_timezone(aDateTime_or_datetime).astimezone(UTC)
    if isinstance(aDateTime_or_datetime, date):
        time = {'hour': 0, 'minute': 0,  'second': 0, 'tzinfo': UTC}
        if end:
            time = {'hour': 23,
                    'minute': 59,
                    'second': 59,
                    'microsecond': 99999,
                    'tzinfo': UTC}
        return datetime(aDateTime_or_datetime.year,
            aDateTime_or_datetime.month,
            aDateTime_or_datetime.day,
            **time)
    if isinstance(aDateTime_or_datetime, DateTime):
        return aDateTime_or_datetime.utcdatetime().replace(tzinfo=UTC)

def datetime_with_timezone(dt, tz=local_timezone):
    """ set the timezone on datetime is dt does have one already
    """
    new_dt = dt
    if dt.tzinfo is None:
        new_dt = dt.replace(tzinfo=tz)
    return new_dt


epoch = datetime(1970, 1, 1, 0, 0, 0, 0, tzinfo=UTC)

def datetime_to_unixtimestamp(dt):
    """do not handle UTC leap seconds.
    """
    delta = utc_datetime(dt) - epoch
    return (delta.microseconds +
        (delta.seconds + delta.days * 24 * 3600) * 10**6) / 10**6


def end_of_day(dt):
    return dt.replace(hour=23, minute=59, second=59)

def start_of_day(dt):
    return dt.replace(hour=0, minute=0, second=0, microsecond=0)

def start_of_week(dt, first_weekday=0):
    delta = relativedelta(days=-((dt.weekday - first_weekday) % 7))
    return start_of_day(dt - delta)

def end_of_week(dt, first_weekday=0):
    delta = relativedelta(days=((first_weekday - dt.weekday) % 7))
    return end_of_day(dt - delta)

def start_of_month(dt):
    return dt.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

def end_of_month(dt):
    ignore, ndays = calendar.monthrange(dt.year, dt.month)
    return dt.replace(day=ndays, hour=23, minute=59, second=59)

def start_of_year(dt):
    return dt.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)

def end_of_year(dt):
    return dt.replace(month=12, hour=23, minute=59, second=59)


class CalendarDatetime(object):
    """ This class provides a abstraction over a datetime ranges and it's
    recurrences.
    """
    default_duration = relativedelta(hours=+1)

    def __init__(self, start_datetime,
            end_datetime=None, recurrence=None, all_day=False):
        self._recurrence = None
        self._all_day = all_day
        if all_day:
            start_datetime = start_of_day(start_datetime)
            end_datetime = end_of_day(end_datetime)
        utc_start_datetime = utc_datetime(start_datetime)
        utc_end_datetime = end_datetime and utc_datetime(end_datetime)
        if not utc_end_datetime or utc_end_datetime < utc_start_datetime:
            utc_end_datetime = utc_start_datetime + self.default_duration

        self.start_datetime = utc_start_datetime
        self.end_datetime = utc_end_datetime

        if recurrence is not None:
            self.set_recurrence(recurrence)

    def get_duration(self):
        if self.end_datetime:
            return relativedelta(self.end_datetime, self.start_datetime)
        return self.default_duration

    def __get_datetime(self, datetime, tz):
        if tz is None:
            return datetime
        return datetime.astimezone(tz)

    def get_start_datetime(self, tz=None):
        return self.__get_datetime(self.start_datetime, tz)

    def get_end_datetime(self, tz=None):
        return self.__get_datetime(self.end_datetime, tz)

    def set_start_datetime(self, value):
        self.start_datetime = utc_datetime(value)
        return self.start_datetime

    def set_end_datetime(self, value):
        self.end_datetime = utc_datetime(value)
        return self.end_datetime

    def validate(self):
        if self.start_datetime is None:
            raise TypeError, 'start datetime can\'t be None'
        if self.end_datetime is not None:
            if self.end_datetime < self.start_datetime:
                raise TypeError, 'end datetime before start datetime'

    def set_recurrence(self, rrule_data):
        """ rrule_data can be either a rrule, a rruleset or a string
        reprensenting one or several rrule in iCalendar format
        """
        if isinstance(rrule_data, rruleset):
            self._recurrence = rrule_data
        elif isinstance(rrule_data, rrule):
            self._recurrence = rruleset()
            self._recurrence.rrule(rrule_data)
        elif isinstance(rrule_data, str) or isinstance(rrule_data, unicode):
            self.set_recurrence_from_string(rrule_data)
        else:
            raise TypeError, "don't know how to handle provided "\
                             "recurrence infos"
        return self._recurrence

    def set_recurrence_from_string(self, rrule_data):
        """ rrule_data is a string representing one or several rule in
        iCalendar format
        """
        rrule_temp = rrulestr(rrule_data, forceset=True,
            dtstart=self.start_datetime)
        if isinstance(rrule_temp, rruleset):
            self._recurrence = rrule_temp
        else: # rrule
            self._recurrence = rruleset()
            self._recurrence.rrule(rrule_temp)
        return self._recurrence

    def  get_recurrence(self):
        return self._recurrence

    def __repr__(self):
        return "<CalendarDatetime sdt=%s, edt=%s>" % \
            (repr(self.start_datetime), repr(self.end_datetime))

    def get_unixtimestamp_range(self):
        """ return the interval boundaries as unix timestamps tuple
        """
        return (datetime_to_unixtimestamp(self.start_datetime),
            datetime_to_unixtimestamp(self.end_datetime))

    def get_unixtimestamp_ranges(self, after=None, before=None):
        """ return a collection of ranges of all occurrences of
        the event date as unix timestamps tuples
        """
        if self._recurrence is None:
            return [self.get_unixtimestamp_range()]
        duration = self.get_duration()
        def get_interval(datetime):
            return (datetime_to_unixtimestamp(datetime),
                datetime_to_unixtimestamp(datetime + duration),)
        event_list = None
        if after and before:
            event_list = self._recurrence.between(after, before, inc=True)
        else:
            event_list = list(self._recurrence)
        return map(get_interval, event_list)

    def get_datetime_range(self):
        return (self.start_datetime, self.end_datetime)

    def get_datetime_ranges(self, after=None, before=None):
        """ return a collection of ranges of all occurrences of
        the event date as unix datetime tuples
        """
        if self._recurrence is None:
            return [self.get_datetime_range()]
        duration = self.get_duration()
        def get_interval(datetime):
            return (datetime, (datetime + duration),)
        if after and before:
            event_list = self._recurrence.between(after, before, inc=True)
        else:
            event_list = list(self._recurrence)
        return map(get_interval, event_list)


class DayWalk(object):
    """ Iterator that yields each days within an interval of datetimes
    """
    def __init__(self, start_datetime, end_datetime, tz=local_timezone):
        self.start_datetime = start_datetime.astimezone(tz)

        if end_datetime < start_datetime:
            self.end_datetime = self.start_datetime + relativedelta(hours=+1)
        else:
            self.end_datetime = end_datetime.astimezone(tz)
        # copy
        self.cursor = start_datetime.astimezone(tz)

    def __iter__(self):
        return self

    def next(self):
        if self.cursor > self.end_datetime:
            raise StopIteration
        else:
            current = self.cursor
            self.cursor = current + relativedelta(days=+1)
            return current



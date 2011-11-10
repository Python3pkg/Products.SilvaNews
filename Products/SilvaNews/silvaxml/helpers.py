from dateutil.parser import parse as datetimeparse
from silva.app.news.datetimeutils import local_timezone

def set_attribute(content, name, attrs, extract=None, ns=None):
    ns_name = (ns, name)
    if attrs.has_key(ns_name):
        if extract is not None:
            value = extract(attrs[ns_name])
        else:
            value = attrs[ns_name]
        setter = getattr(content, "set_%s" % name)
        setter(value)
        return value

def set_attribute_as_list(content, name, attrs, ns=None, sep=","):
    return set_attribute(
        content, name, attrs, ns=ns, extract=lambda x: x.split(sep))

def set_attribute_as_bool(content, name, attrs, ns=None):
    return set_attribute(
        content, name, attrs, ns=ns, extract=lambda x: x == 'True' or x == '1')

def set_attribute_as_int(content, name, attrs, ns=None):
    return set_attribute(
        content, name, attrs, ns=ns, extract=lambda x: int(x))

def set_attribute_as_datetime(content, name, attrs, ns=None, tz=None):
    def extract(value):
        if value == '':
            return None
        dt = datetimeparse(value)
        if tz:
            dt = dt.astimezone(tz)
        return dt

    return set_attribute(
        content, name, attrs, ns=ns, extract=extract)

def set_attribute_as_naive_datetime(content, name, attrs, ns=None):
    def extract(value):
        if value == '':
            return None
        dt = datetimeparse(value).astimezone(
            local_timezone).replace(tzinfo=None)
        return dt
    return set_attribute(
        content, name, attrs, ns=ns, extract=extract)



from zope.schema.fieldproperty import FieldProperty
from zope.schema import getFieldNames

from five import grok
from silva.core.views.z3cforms import AddForm
from z3c.form import field

from Products.Silva.Content import Content
from OFS.SimpleItem import SimpleItem

from Products.SilvaNews.interfaces import ICalendarEvent


class CalendarEvent(Content, SimpleItem):
    meta_type = 'Silva Calendar Event'
    grok.implements(ICalendarEvent)

    start_datetime = FieldProperty(ICalendarEvent['start_datetime'])
    end_datetime = FieldProperty(ICalendarEvent['end_datetime'])
    all_day = FieldProperty(ICalendarEvent['all_day'])
    recurrence_rule = FieldProperty(ICalendarEvent['recurrence_rule'])

    def __init__(self, id, **kw):
        self.update(**kw)

    def update(self, **kw):
        field_names = getFieldNames(ICalendarEvent)
        for key, value in kw.iteritems():
            if key not in field_names:
                raise TypeError, 'Invalid field : %s' % key
            field = self.get_field(key)
            field.validate(value)
            field.set(self, value)


class CalendarEventAddForm(AddForm):
    fields = field.Fields(ICalendarEvent)
    grok.context(ICalendarEvent)
    grok.name(CalendarEvent.meta_type)



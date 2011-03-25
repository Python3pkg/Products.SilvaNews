from five import grok
from zope.interface import Interface
from zope.schema.interfaces import ITextLine
from zope.schema import TextLine
from zope.publisher.interfaces.browser import IDefaultBrowserLayer
from silva.core import conf as silvaconf
from zeam.form.base.markers import INPUT, DISPLAY
from zeam.form.ztk.fields import (SchemaField, SchemaFieldWidget,
    registerSchemaField)
from silva.core.layout.jquery.interfaces import IJQueryUIResources

class IRecurrenceResources(IJQueryUIResources):
    """pluggable layer to add the recurrence resources to any page"""
    silvaconf.resource("ui-recurrence.js")
    silvaconf.resource("ui-recurrence.css")

def register():
    registerSchemaField(RecurrenceSchemaField, IRecurrence)


class IRecurrence(ITextLine):
    """ Recurrence schema interface
    """


class Recurrence(TextLine):
    """ Recurrence Field
    """
    grok.implements(IRecurrence)


class RecurrenceSchemaField(SchemaField):
    """ zeam schema field
    """


class RecurrenceWidgetInput(SchemaFieldWidget):
    grok.adapts(RecurrenceSchemaField, Interface, Interface)
    grok.name(str(INPUT))


class RecurrenceWidgetDisplay(RecurrenceWidgetInput):
    grok.name(str(DISPLAY))

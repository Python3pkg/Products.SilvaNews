from Products.SilvaNews import schema

import zope
from z3c.form import interfaces
from z3c.form.widget import Widget, FieldWidget
from z3c.form.browser import widget as browserwidget


class IRecurrenceWidget(interfaces.IFieldWidget):
    pass


class RecurrenceWidget(browserwidget.HTMLFormElement, Widget):
    zope.interface.implementsOnly(IRecurrenceWidget)


@zope.component.adapter(schema.IRecurrenceRule, interfaces.IFormLayer)
@zope.interface.implementer(IRecurrenceWidget)
def RecurrenceFieldWidget(field, request):
    """IFieldWidget factory for ReferenceWidget.
    """
    widget =  FieldWidget(field, RecurrenceWidget(request))
    widget.title = field.title  # Set properly the title to have access to it
    return widget


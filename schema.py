# Copyright (c) 2010 Infrae. All rights reserved.
# See also LICENSE.txt
# $Id$

from zope import schema, interface


class IRecurrenceRule(schema.interfaces.IField):
    """A recurrence field is like an object.
    """


class RecurrenceRule(schema.TextLine):
    """Store a recurrence to an object.
    """
    interface.implements(IRecurrenceRule)


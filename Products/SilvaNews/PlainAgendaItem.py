# Copyright (c) 2002-2011 Infrae. All rights reserved.
# See also LICENSE.txt
# $Id$

from five import grok
from zope import interface, schema
from zope.component import IFactory
from zope.component import getUtility
from zope.i18nmessageid import MessageFactory

from silva.core import conf as silvaconf
from silva.core.conf.interfaces import ITitledContent
from zeam.form import silva as silvaforms

# Zope
from AccessControl import ClassSecurityInfo
from App.class_init import InitializeClass

from Products.SilvaNews.AgendaItem import AgendaItem, AgendaItemVersion
from Products.SilvaNews.AgendaItem import AgendaItemOccurrence
from Products.SilvaNews.interfaces import IAgendaItem, IServiceNews
from Products.SilvaNews.interfaces import (
    subjects_source, target_audiences_source, timezone_source)
from Products.SilvaNews.widgets.recurrence import Recurrence

_ = MessageFactory('silva_news')


class PlainAgendaItemVersion(AgendaItemVersion):
    """Silva News PlainAgendaItemVersion
    """
    security = ClassSecurityInfo()
    meta_type = "Silva Agenda Item Version"

InitializeClass(PlainAgendaItemVersion)


class PlainAgendaItem(AgendaItem):
    """A News item for events. Includes date and location
       metadata, as well settings for subjects and audiences.
    """
    security = ClassSecurityInfo()
    meta_type = "Silva Agenda Item"
    _event_id = None
    silvaconf.icon("www/agenda_item.png")
    silvaconf.priority(3.8)
    silvaconf.versionClass(PlainAgendaItemVersion)

InitializeClass(PlainAgendaItem)


class IAgendaItemOccurrenceSchema(interface.Interface):
    timezone_name = schema.Choice(
        source=timezone_source,
        title=_(u"timezone"),
        description=_(u"Defines the time zone for dates"),
        required=True)
    start_datetime = schema.Datetime(
        title=_(u"start date/time"),
        required=True)
    end_datetime = schema.Datetime(
        title=_(u"end date/time"),
        required=False)
    all_day = schema.Bool(
        title=_(u"all day"))
    recurrence = Recurrence(title=_("recurrence"), required=False)
    end_recurrence_datetime = schema.Datetime(
        title=_(u"recurrence end date"),
        description=_(u"Date on which the recurrence stops. Required if "
                      u"any recurrence is set"),
        required=False)
    location = schema.TextLine(
        title=_(u"location"),
        description=_(u"The location where the event is taking place."),
        required=False)

    @interface.invariant
    def enforce_end_recurrence_datetime(content):
        """ Enforce to set end_recurrence_datetime if recurrence is set
        """
        if not content.recurrence:
            # recurrence not set, bail out
            return

        if not content.end_recurrence_datetime:
            raise interface.Invalid(
                _(u"End recurrence date must be set when "
                  u"recurrence is."))

    @interface.invariant
    def enforce_start_date_before_end_date(content):
        if not content.end_datetime:
            return
        if content.start_datetime > content.end_datetime:
            raise interface.Invalid(
                _(u"End date must not is before start date."))

    @interface.invariant
    def enforce_end_recurrence_date_after_start_date(content):
        if not content.end_recurrence_datetime:
            return

        if content.start_datetime and \
                content.end_recurrence_datetime < content.start_datetime:
            raise interface.Invalid(
                _(u"End recurrence date must not be before start date."))

        if content.end_datetime and \
                content.end_recurrence_datetime < content.end_datetime:
            raise interface.Invalid(
                _(u"End recurrence date must not be before end date."))


grok.global_utility(
    AgendaItemOccurrence, provides=IFactory,
    name=IAgendaItemOccurrenceSchema.__identifier__, direct=True)


class IAgendaItemSchema(interface.Interface):
    occurrences = schema.List(
        title=_(u"occurrences"),
        description=_(u"when and where the event will happens."),
        value_type=schema.Object(schema=IAgendaItemOccurrenceSchema),
        min_length=1)
    subjects = schema.Set(
        title=_(u"subjects"),
        value_type=schema.Choice(source=subjects_source),
        required=True)
    target_audiences = schema.Set(
        title=_(u"target audiences"),
        value_type=schema.Choice(source=target_audiences_source),
        required=True)
    external_url = schema.URI(
        title=_(u"external URL"),
        description=_(u"external URL with more information about this event."),
        required=False)



def get_default_tz_name(form):
    util = getUtility(IServiceNews)
    return util.get_timezone_name()


class AgendaItemAddForm(silvaforms.SMIAddForm):
    grok.context(IAgendaItem)
    grok.name(u"Silva Agenda Item")

    fields = silvaforms.Fields(ITitledContent, IAgendaItemSchema)
    fields['occurrences'].mode = 'list'
    fields['occurrences'].allowOrdering = False
    fields['occurrences'].valueField.dataManager = silvaforms.SilvaDataManager
    fields['occurrences'].valueField.objectFields[
        'timezone_name'].defaultValue = get_default_tz_name


class AgendaEditProperties(silvaforms.RESTKupuEditProperties):
    grok.context(IAgendaItem)

    label = _(u"agenda item properties")
    fields = silvaforms.Fields(IAgendaItemSchema)
    fields['occurrences'].mode = 'list'
    fields['occurrences'].allowOrdering = False
    fields['occurrences'].valueField.dataManager = silvaforms.SilvaDataManager
    fields['occurrences'].valueField.objectFields[
        'timezone_name'].defaultValue = get_default_tz_name

    actions = silvaforms.Actions(silvaforms.EditAction())


# Prevent object validation, AgendaItemOccurrence doesn't validate
import zope.schema._field
zope.schema._field.Object._validate = zope.schema._field.Field._validate

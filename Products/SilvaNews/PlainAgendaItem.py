# Copyright (c) 2002-2011 Infrae. All rights reserved.
# See also LICENSE.txt
# $Id$

from icalendar import vDatetime

from five import grok
from silva.core import conf as silvaconf
from silva.core.conf.interfaces import ITitledContent
from zeam.form import silva as silvaforms
from zope import interface, schema
from zope.component import getUtility
from zope.i18nmessageid import MessageFactory

# Zope
from AccessControl import ClassSecurityInfo
from App.class_init import InitializeClass

from Products.SilvaNews.datetimeutils import (get_timezone,
    RRuleData, UTC)
from Products.SilvaNews.AgendaItem import AgendaItem, AgendaItemVersion
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


class IAgendaItemSchema(interface.Interface):
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
    _all_day = schema.Bool(
        title=_(u"all day"))
    recurrence = Recurrence(title=_("recurrence"), required=False)
    end_recurrence_datetime = schema.Datetime(
        title=_(u"recurrence end date"),
        description=_(u"Date on which the recurrence stops. Required if "
                      u"any recurrence is set"),
        required=False)
    _location = schema.TextLine(
        title=_(u"location"),
        description=_(u"The location where the event is taking place."),
        required=False)
    subjects = schema.Set(
        title=_(u"subjects"),
        value_type=schema.Choice(source=subjects_source),
        required=True)
    target_audiences = schema.Set(
        title=_(u"target audiences"),
        value_type=schema.Choice(source=target_audiences_source),
        required=True)

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


def get_default_tz_name(form):
    util = getUtility(IServiceNews)
    return util.get_timezone_name()


def process_data(data):
    """preprocess the data before setting the content"""
    timezone = get_timezone(data['timezone_name'])
    date_fields = ['start_datetime',
                   'end_datetime',
                   'end_recurrence_datetime']
    # set timezone on datetime fields
    for name in date_fields:
        if data.has_key(name) and data[name] is not silvaforms.NO_VALUE:
            data[name] = data[name].replace(tzinfo=timezone)

    # copy data from end recurrence datetime to the recurrence field
    if data.has_key('recurrence') and \
            data['recurrence'] is not silvaforms.NO_VALUE:
        recurrence = RRuleData(data['recurrence'])
        recurrence['UNTIL'] = vDatetime(
            data['end_recurrence_datetime'].astimezone(UTC))
        data['recurrence'] = str(recurrence)

    if data.has_key('recurrence_end_datetime'):
        del data['recurrence_end_datetime']
    return data


class AgendaItemAddForm(silvaforms.SMIAddForm):
    grok.context(IAgendaItem)
    grok.name(u"Silva Agenda Item")

    fields = silvaforms.Fields(ITitledContent, IAgendaItemSchema)
    fields['timezone_name'].defaultValue = get_default_tz_name

    def _edit(self, parent, content, data):
        data = process_data(data)
        return super(AgendaItemAddForm, self)._edit(parent, content, data)


class EditAction(silvaforms.EditAction):
    def applyData(self, form, content, data):
        data = process_data(data)
        return super(EditAction, self).applyData(form, content, data)


class AgendaEditProperties(silvaforms.RESTKupuEditProperties):
    grok.context(IAgendaItem)

    label = _(u"agenda item properties")
    fields = silvaforms.Fields(IAgendaItemSchema)
    actions = silvaforms.Actions(EditAction())

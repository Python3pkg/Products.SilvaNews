import logging
import icalendar
import DateTime

from datetime import datetime
from hashlib import sha1

from urllib2 import urlopen, URLError
from cStringIO import StringIO

from five import grok
from zope import schema
from zope.interface import Interface
from zope.component import getUtility
from silva.core.services.interfaces import ICatalogService

from App.class_init import InitializeClass
from AccessControl import ClassSecurityInfo

from zeam.form import silva as silvaforms

from Products.SilvaNews.datetimeutils import utc_datetime
from Products.SilvaNews.interfaces import INewsPublication
from Products.SilvaNews.NewsPublication import NewsPublication

from Products.SilvaNews.interfaces import (subjects_source,
    target_audiences_source)

from zope.i18nmessageid import MessageFactory
_ = MessageFactory('silva_news')

logger = logging.getLogger('silva_news')

# XXX Move this to interfaces
class IICSNewsPublication(INewsPublication):
    pass


class ICSCalendarPublication(NewsPublication):
    grok.baseclass() # disable for now
    grok.implements(IICSNewsPublication)
    security = ClassSecurityInfo()
    meta_type = "Silva News ICS Publication"

    _url = u''
    _last_update = None
    _subjects = []
    _target_audiences = []

    def __init__(self, *args, **kw):
        super(ICSCalendarPublication, self).__init__(*args, **kw)

    def sync(self):
        ical_data = self._fetch()
        self._pull(ical_data)
        self._last_update = datetime.now()

    def _fetch(self):
        try:
            handle = urlopen(self._url)
        except (URLError,) as e:
            logger.error('error while fetching calendar at %s and %s',
                         self._url, str(e))
            raise e

        io = StringIO()
        line = handle.readline()
        while line:
            if not line.startswith('CREATED:0000'):
                io.write(line)
            line = handle.readline()

        io.seek(0)
        return io.read()

    def _pull(self, ics_string):
        calendar = icalendar.cal.Calendar.from_string(ics_string)
        factory = self.manage_addProduct['SilvaNews']
        catalog = getUtility(ICatalogService)
        old_ids = set(
            map(lambda x: x.id, catalog.searchResults(
                    meta_type="Silva Agenda Item",
                    path=self.getPhysicalPath())))

        errors = []
        for event in calendar.walk('VEVENT'):
            if event.get('recurrence-id'):
                continue
#            try:
            id = unicode(event['uid'])
            hash = unicode(sha1(id).hexdigest())
            if hash in old_ids:
                old_ids.remove(hash)
                agenda_item = self[hash]
                if event.has_key('last-modified'):
                    version = agenda_item.get_viewable()
                    dt = utc_datetime(version.publication_datetime())
                    if not event.has_key('last-modified') or \
                            event['last-modified'].dt > dt:
                        self._create_new_version(id, agenda_item, event)
                # XXX what happens if they don't provide last modified date ?
            else:
                self._build_agenda_item(hash, event, factory)

#            except StandardError as e:
#                errors.append((event, e))
#                logger.error(
#                    'error during events synchronization of %s with %s : %s',
#                    "/".join(self.getPhysicalPath()),
#                    self._url,
#                    str(e))
#                raise e
#                continue

        self.manage_delObjects(old_ids)
        return errors

    def _build_agenda_item(self, id, event, factory=None):
        if factory is None:
            factory = self.manage_addProduct['SilvaNews']

        title = unicode(event['summary'])
        agenda_item = factory.manage_addPlainAgendaItem(id, title)
        self._create_new_version(agenda_item, event)

    def _create_new_version(self, agenda_item, event):
        version = agenda_item.get_editable()
        if version is None:
            version = agenda_item.create_copy()

        version.set_title(event['summary'])
        version.set_start_datetime(utc_datetime(event['dtstart'].dt))
        if event.has_key('dtend'):
            version.set_end_datetime(utc_datetime(event['dtend'].dt))
        version.set_target_audiences(self._target_audiences)
        version.set_subjects(self._subjects)
        now = DateTime.DateTime()
        agenda_item.set_unapproved_version_publication_datetime(now)
        agenda_item.approve_version()
        return version


InitializeClass(ICSCalendarPublication)


class IICSNewsPublicationSchema(Interface):
    """ Schema fields for forms
    """
    _url = schema.URI(
        title=_(u"URL"),
        description=_(u"remote URL of the ics calendar file"),
        required=True)
    _subjects = schema.Set(
        title=_(u"subjects"),
        description=_(u"select the subjects that will be set on events"),
        value_type=schema.Choice(source=subjects_source),
        required=True)
    _target_audiences = schema.Set(
        title=_(u"target audiences"),
        description=_(u"select the target audiences "
                      u"that will be set on events"),
        value_type=schema.Choice(source=target_audiences_source),
        required=True)


class ICSNewsPublicationAddForm(silvaforms.SMIAddForm):
    """ SMI add form
    """
    grok.baseclass() # disabled
    grok.context(IICSNewsPublication)
    grok.name("Silva News ICS Publication")


class SyncAction(silvaforms.Action):
    title = _(u'sync')
    description = _(u'fetch the remote calendar and synchronize data')

    def __call__(self, form):
        form.context.sync()
        return silvaforms.SUCCESS


class ICSNewsPublicationEditForm(silvaforms.SMIEditForm):
    """ SMI edit form for ICS News Publication
    """
    grok.baseclass() # disabled
    grok.context(IICSNewsPublication)
    fields = silvaforms.Fields(IICSNewsPublicationSchema)
    actions = silvaforms.SMIEditForm.actions.copy()
    actions.append(SyncAction())

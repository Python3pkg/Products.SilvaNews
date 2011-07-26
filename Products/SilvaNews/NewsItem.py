# Copyright (c) 2002-2011 Infrae. All rights reserved.
# See also LICENSE.txt

from five import grok
from zope.component import getUtility
from zope.cachedescriptors.property import CachedProperty
from zope.i18nmessageid import MessageFactory
from zope.interface import Interface
from zope import schema
from zeam.form import autofields

# Zope
from AccessControl import ClassSecurityInfo
from App.class_init import InitializeClass
from DateTime import DateTime
from datetime import datetime

# Silva
from Products.Silva import SilvaPermissions
from Products.Silva.cataloging import CatalogingAttributesPublishable
from silva.app.document import document
from silva.ui.menu import MenuItem
from silva.core.smi.content import ContentEditMenu
from silva.core import conf as silvaconf
from silva.core.conf.interfaces import ITitledContent
from silva.core.interfaces import IRoot
from silva.core.interfaces.events import IContentPublishedEvent, IPublishingEvent
from silva.core.services.interfaces import ICataloging
from silva.core.smi.content.publish import IPublicationFields, VersionPublication
from silva.core.views import views as silvaviews
from zeam.form import silva as silvaforms

from Products.SilvaNews.interfaces import INewsItem, INewsItemVersion
from Products.SilvaNews.interfaces import (INewsPublication, IServiceNews,
    INewsViewer)
from Products.SilvaNews.datetimeutils import (datetime_to_unixtimestamp,
    CalendarDatetime)
from Products.SilvaNews.NewsCategorization import NewsCategorization
from Products.SilvaNews.NewsCategorization import INewsCategorizationSchema

_ = MessageFactory('silva_news')


class NewsItemVersion(NewsCategorization, document.DocumentVersion):
    """Base class for news item versions.
    """
    security = ClassSecurityInfo()
    grok.implements(INewsItemVersion)
    meta_type = "Silva Article Version"

    def __init__(self, id):
        super(NewsItemVersion, self).__init__(id)
        self._display_datetime = None

    # XXX I would rather have this get called automatically on setting
    # the publication datetime, but that would have meant some nasty monkey-
    # patching would be required...
    security.declareProtected(SilvaPermissions.ChangeSilvaContent,
                                'set_display_datetime')
    def set_display_datetime(self, ddt):
        """set the display datetime

            this datetime is used to determine whether an item should be shown
            in the news viewer, and to determine the order in which the items
            are shown
        """
        self._display_datetime = DateTime(ddt)

    security.declareProtected(SilvaPermissions.AccessContentsInformation,
                                'get_display_datetime')
    def get_display_datetime(self):
        """returns the display datetime

            see 'set_display_datetime'
        """
        return self._display_datetime

    # ACCESSORS
    security.declareProtected(SilvaPermissions.AccessContentsInformation,
                              'get_intro')
    def get_intro(self, max_size=128, request=None):
        """Returns first bit of the news item's content

            this returns all elements up to and including the first
            paragraph, if it turns out that there are more than max_size
            characters in the data returned it will truncate (per element)
            to minimally 1 element
        """
        # XXX fix intro, remove this function.
        return u"XXX: FIXME"

    security.declareProtected(SilvaPermissions.AccessContentsInformation,
                                'get_description')
    def get_description(self):
        return self.service_metadata.getMetadataValue(
            self, 'silva-extra', 'content_description')

    def _get_source(self):
        c = self.aq_inner.aq_parent
        while True:
            if INewsPublication.providedBy(c):
                return c
            if IRoot.providedBy(c):
                return None
            c = c.aq_parent
        return None

    security.declareProtected(SilvaPermissions.AccessContentsInformation,
                              'source_path')
    def source_path(self):
        """Returns the path to the source containing this item
        """
        source = self._get_source()
        if not source:
            return None
        return source.getPhysicalPath()

    security.declareProtected(SilvaPermissions.AccessContentsInformation,
                              'is_private')
    def is_private(self):
        """Returns whether the object is in a private source
        """
        source = self._get_source()
        if not source:
            return False
        return self.service_metadata.getMetadataValue(
            source, 'snn-np-settings', 'is_private')

    security.declareProtected(SilvaPermissions.AccessContentsInformation,
                              'last_author_fullname')
    def last_author_fullname(self):
        """Returns the userid of the last author, to be used in
        combination with the ZCatalog.  The data this method returns
        can, in opposite to the sec_get_last_author_info data, be
        stored in the ZCatalog without any problems.
        """
        return self.sec_get_last_author_info().fullname()

    security.declareProtected(SilvaPermissions.AccessContentsInformation,
                              'fulltext')
    def fulltext(self):
        """Returns all data as a flat string for full text-search
        """
        keywords = list(self._subjects)
        keywords.extend(self._target_audiences)
        keywords.extend(super(NewsItemVersion, self).fulltext())
        return keywords

    security.declareProtected(SilvaPermissions.AccessContentsInformation,
                              'publication_time')
    def publication_time(self):
        binding = self.service_metadata.getMetadata(self)
        return binding.get('silva-extra', 'publicationtime')

    security.declareProtected(SilvaPermissions.AccessContentsInformation,
                              'sort_index')
    def sort_index(self):
        dt = self.get_display_datetime()
        if dt:
            return datetime_to_unixtimestamp(dt)
        return None

    security.declareProtected(SilvaPermissions.AccessContentsInformation,
                              'get_timestamp_ranges')
    def get_timestamp_ranges(self):
        if self._display_datetime:
            return CalendarDatetime(self._display_datetime, None).\
                get_unixtimestamp_ranges()


InitializeClass(NewsItemVersion)


class NewsItem(document.Document):
    """A News item that appears as an individual page. By adjusting
       settings the Author can determine which subjects, and
       for which audiences the Article should be presented.
    """
    grok.implements(INewsItem)
    security = ClassSecurityInfo()
    meta_type = "Silva Article"
    silvaconf.icon("www/news_item.png")
    silvaconf.priority(3.7)
    silvaconf.versionClass(NewsItemVersion)

    security.declareProtected(SilvaPermissions.ApproveSilvaContent,
                              'set_next_version_display_datetime')
    def set_next_version_display_datetime(self, dt):
        """Set display datetime of next version.
        """
        version = getattr(self, self.get_next_version())
        version.set_display_datetime(dt)

    security.declareProtected(SilvaPermissions.ChangeSilvaContent,
                              'set_unapproved_version_display_datetime')
    def set_unapproved_version_display_datetime(self, dt):
        """Set display datetime for unapproved
        """
        version = getattr(self, self.get_unapproved_version())
        version.set_display_datetime(dt)

    security.declareProtected(SilvaPermissions.AccessContentsInformation,
                              'get_unapproved_version_display_datetime')
    def get_unapproved_version_display_datetime(self):
        """get display datetime for unapproved
        """
        version = getattr(self, self.get_unapproved_version())
        version.get_display_datetime()

InitializeClass(NewsItem)


class NewsItemAddForm(silvaforms.SMIAddForm):
    grok.context(INewsItem)
    grok.name(u"Silva Article")

    fields = silvaforms.Fields(ITitledContent, INewsCategorizationSchema)


class NewsItemDetailsForm(silvaforms.SMIEditForm):
    grok.context(INewsItem)
    grok.name('details')

    label = _(u"Article details")
    fields = silvaforms.Fields(ITitledContent, INewsCategorizationSchema).omit('id')
    actions = silvaforms.Actions(
        silvaforms.CancelAction(),
        silvaforms.EditAction())


class NewsItemDetailsMenu(MenuItem):
    grok.adapts(ContentEditMenu, INewsItem)
    grok.require('silva.ChangeSilvaContent')
    grok.order(15)
    name = _('Details')
    screen = NewsItemDetailsForm


class NewsItemView(silvaviews.View):
    """ View on a News Item (either Article / Agenda )
    """
    grok.context(INewsItem)

    @CachedProperty
    def article_date(self):
        article_date = self.content.get_display_datetime()
        if not article_date:
            article_date = self.content.publication_time()
        if article_date:
            news_service = getUtility(IServiceNews)
            return news_service.format_date(
                article_date)
        return u''

    @CachedProperty
    def article(self):
        if self.content is not None:
            return self.content.body.render(self.content, self.request)
        return u''


class NewsItemListItemView(NewsItemView):
    """ Render as a list items (search results)
    """
    grok.context(INewsItem)
    grok.name('search_result')

    @CachedProperty
    def article(self):
        if self.content is not None:
            return self.content.body.render_intro(
                self.content, self.request,
                max_length=128)
        return u''

# Add display datetime on publish smi tab

class INewsItemPublicationFields(Interface):
    display_datetime = schema.Datetime(title=_("Display datetime"))


class NewsItemPublicationFields(autofields.AutoFields):
    autofields.context(INewsItem)
    autofields.group(IPublicationFields)
    autofields.order(20)
    fields = silvaforms.Fields(INewsItemPublicationFields)
    fields['display_datetime'].defaultValue = lambda d: datetime.now()


class NewsItemPublication(VersionPublication):
    grok.context(INewsItem)
    grok.provides(IPublicationFields)

    def set_display_datetime(self, value):
        self.context.set_unapproved_version_display_datetime(DateTime(value))

    def get_display_datetime(self):
        return self.context.get_unapproved_version_display_datetime()

    display_datetime = property(get_display_datetime, set_display_datetime)


class NewsItemCatalogingAttributes(CatalogingAttributesPublishable):
    grok.context(INewsItem)

    def __init__(self, context):
        super(NewsItemCatalogingAttributes, self).__init__(context)
        self.version = self._get_version()

    def _get_version(self):
        """ get the version the most close to public state
        """
        version_id = self.context.get_public_version()
        if version_id is None:
            version_id = self.context.get_approved_version()
        if version_id is None:
            version_id = self.context.get_unapproved_version()
        if version_id is None:
            versions = self.context.get_previous_versions()
            if versions:
                return versions[0]
        if version_id is not None:
            return getattr(self.context, version_id, None)
        return None

    @property
    def display_datetime(self):
        if self.version is not None:
            return self.version.get_display_datetime()

    @property
    def timestamp_ranges(self):
        if self.version is not None:
            return self.version.get_timestamp_ranges()

    @property
    def parent_path(self):
        if self.version is not None:
            return self.version.get_parent_path()

    @property
    def subjects(self):
        if self.version is not None:
            return self.version.get_subjects()

    @property
    def target_audiences(self):
        if self.version is not None:
            return self.version.get_target_audiences()

    @property
    def fulltext(self):
        if self.version is not None:
            return self.version.fulltext()


@grok.subscribe(INewsItemVersion, IPublishingEvent)
def reindex_content(content, event):
    ICataloging(content.get_content()).reindex()


@grok.subscribe(INewsItemVersion, IContentPublishedEvent)
def news_item_published(content, event):
    if content.get_display_datetime() is None:
        now = DateTime()
        content.set_display_datetime(now)
        ICataloging(content.get_content()).reindex()


@grok.adapter(INewsItem)
@grok.implementer(INewsViewer)
def get_default_viewer(context):
    """Adapter factory to get the contextual news viewer for a news item
    """
    parents = context.aq_chain[1:]
    for parent in parents:
        if IRoot.providedBy(parent):
            return None
        if INewsViewer.providedBy(parent):
            return parent
        if INewsPublication.providedBy(parent):
            default = parent.get_default()
            if default and INewsViewer.providedBy(default):
                return default
    return None



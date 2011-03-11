# Copyright (c) 2002-2011 Infrae. All rights reserved.
# See also LICENSE.txt
# $Revision: 1.35 $

from five import grok
from zope.component import getUtility
from zope.i18nmessageid import MessageFactory
from zope.cachedescriptors.property import CachedProperty

# Zope
from AccessControl import ClassSecurityInfo
from App.class_init import InitializeClass
from DateTime import DateTime

# Silva
from silva.core.interfaces import IRoot
from silva.core.interfaces.events import IContentPublishedEvent
from silva.core.references.interfaces import IReferenceService
from silva.core.views import views as silvaviews

from Products.Silva import SilvaPermissions
from Products.Silva.transform.renderer.xsltrendererbase import XSLTTransformer
from Products.SilvaDocument.Document import Document, DocumentVersion
from Products.SilvaNews.interfaces import INewsItem, INewsItemVersion
from Products.SilvaNews.interfaces import (INewsPublication, IServiceNews,
    INewsViewer)
from Products.SilvaNews.datetimeutils import datetime_to_unixtimestamp

_ = MessageFactory('silva_news')


class NewsItem(Document):
    """Base class for all kinds of news items.
    """
    grok.baseclass()
    grok.implements(INewsItem)

    security = ClassSecurityInfo()
    # MANIPULATORS

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


InitializeClass(NewsItem)


class NewsItemVersion(DocumentVersion):
    """Base class for news item versions.
    """
    security = ClassSecurityInfo()
    grok.baseclass()
    grok.implements(INewsItemVersion)

    def __init__(self, id):
        super(NewsItemVersion, self).__init__(id)
        self._subjects = []
        self._target_audiences = []
        self._display_datetime = None
        self._external_link = None
        self._link_method = 'article'

    # XXX I would rather have this get called automatically on setting
    # the publication datetime, but that would have meant some nasty monkey-
    # patching would be required...
    security.declareProtected(SilvaPermissions.ChangeSilvaContent,
                                'set_display_datetime')
    def set_display_datetime(self, ddt, reindex=True):
        """set the display datetime

            this datetime is used to determine whether an item should be shown
            in the news viewer, and to determine the order in which the items
            are shown
        """
        self._display_datetime = ddt
        #XXX this was in aaltepet silva 2.1, does it still work in 2.3?
        if reindex:
            self.reindex_object()

    security.declareProtected(SilvaPermissions.AccessContentsInformation,
                                'display_datetime')
    def display_datetime(self):
        """returns the display datetime

            see 'set_display_datetime'
        """
        return self._display_datetime

    security.declareProtected(SilvaPermissions.AccessContentsInformation,
                                'idx_display_datetime')
    idx_display_datetime = display_datetime

    security.declareProtected(SilvaPermissions.AccessContentsInformation,
                                'get_display_datetime')
    get_display_datetime = display_datetime

    security.declareProtected(SilvaPermissions.ChangeSilvaContent,
                              'set_subjects')
    def set_subjects(self, subjects, reindex=True):
        self._subjects = list(subjects)
        #XXX this was in aaltepet silva 2.1, does it still work in 2.3?
        if reindex:
            self.reindex_object()

     security.declareProtected(SilvaPermissions.ChangeSilvaContent,
                               'set_link_method')
     def set_link_method(self, method):
        self._link_method = method

    security.declareProtected(SilvaPermissions.ChangeSilvaContent,
                              'set_target_audiences')
    def set_target_audiences(self, target_audiences, reindex=True):
        self._target_audiences = list(target_audiences)
        #XXX this was in aaltepet silva 2.1, does it still work in 2.3?
        if reindex:
            self.reindex_object()

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
        return IntroHTML.transform(self, request or self.REQUEST)

    security.declareProtected(SilvaPermissions.AccessContentsInformation,
                                'get_thumbnail')
    def get_thumbnail(self, divclass=None):
        """returns an image tag for the tumbnail of the first image in the item

            returns '' if no image is available
        """
        image = self.get_thumbnail_image()
        if image is None:
            return u''
        tag = (u'<a class="newsitemthumbnaillink" href="%s">%s</a>' %
               (self.get_content().absolute_url(), image.tag(thumbnail=1)))
        if divclass:
            tag = u'<div class="%s">%s</div>' % (divclass, tag)
        return tag

    security.declareProtected(SilvaPermissions.AccessContentsInformation,
                                'get_thumbnail_image')
    def get_thumbnail_image(self):
        images = self.content.documentElement.getElementsByTagName('image')
        if not images:
            return None
        reference_name = images[0].getAttribute('reference')
        service = getUtility(IReferenceService)
        reference = service.get_reference(self, name=reference_name)
        if reference is None:
            return None
        return reference.target

    security.declareProtected(SilvaPermissions.AccessContentsInformation,
                                'get_description')
    def get_description(self):
        return self.service_metadata.getMetadataValue(
            self, 'syndication', 'teaser')

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
                              'idx_is_private')
    idx_is_private = is_private

    security.declareProtected(SilvaPermissions.AccessContentsInformation,
                              'get_subjects')
    def get_subjects(self):
        """Returns the subjects
        """
        return list(self._subjects or [])

    security.declareProtected(SilvaPermissions.AccessContentsInformation,
                              'subjects')
    subjects = get_subjects

    security.declareProtected(SilvaPermissions.AccessContentsInformation,
                              'idx_subjects')
    idx_subjects = get_subjects

    security.declareProtected(SilvaPermissions.AccessContentsInformation,
                              'get_target_audiences')
    def get_target_audiences(self):
        """Returns the target audiences
        """
        return list(self._target_audiences or [])
    
    security.declareProtected(SilvaPermissions.AccessContentsInformation,
                              'external_link')
    def external_link(self):
        return self._external_link
 
    security.declareProtected(SilvaPermissions.AccessContentsInformation,
                              'link_method')
    def link_method(self):
        return self._link_method
    
    security.declareProtected(SilvaPermissions.AccessContentsInformation,
                              'target_audiences')
    target_audiences = get_target_audiences

    security.declareProtected(SilvaPermissions.AccessContentsInformation,
                              'idx_target_audiences')
    idx_target_audiences = get_target_audiences

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
        return " ".join(keywords)

    security.declareProtected(SilvaPermissions.AccessContentsInformation,
                              'publication_time')
    def publication_time(self):
        binding = self.service_metadata.getMetadata(self)
        return binding.get('silva-extra', 'publicationtime')

    security.declareProtected(SilvaPermissions.AccessContentsInformation,
                              'sort_index')
    def sort_index(self):
        dt = self.display_datetime()
        if dt:
            return datetime_to_unixtimestamp(dt)
        return None


InitializeClass(NewsItemVersion)

ContentHTML = XSLTTransformer('newsitem.xslt', __file__)
IntroHTML = XSLTTransformer('newsitem_intro.xslt', __file__)

class NewsItemView(silvaviews.View):
    """ View on a News Item (either Article / Agenda )
    """
    grok.context(INewsItem)

    @CachedProperty
    def article_date(self):
        article_date = self.content.display_datetime()
        if not article_date:
            article_date = self.content.publication_time()
        if article_date:
            news_service = getUtility(IServiceNews)
            return news_service.format_date(
                article_date)
        return u''

    @CachedProperty
    def article(self):
        return ContentHTML.transform(self.content, self.request)


class NewsItemListItemView(NewsItemView):
    """ Render as a list items (search results)
    """
    grok.context(INewsItem)
    grok.name('search_result')

    @CachedProperty
    def article(self):
        return IntroHTML.transform(self.content, self.request)


@grok.subscribe(INewsItemVersion, IContentPublishedEvent)
def news_item_published(content, event):
    if content.display_datetime() is None:
        now = DateTime()
        content.set_display_datetime(now)


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

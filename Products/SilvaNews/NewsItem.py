# Copyright (c) 2002-2011 Infrae. All rights reserved.
# See also LICENSE.txt

from five import grok
from zope.i18nmessageid import MessageFactory

# Zope
from AccessControl import ClassSecurityInfo
from App.class_init import InitializeClass
from DateTime import DateTime

# Silva
from Products.Silva import SilvaPermissions
from Products.SilvaDocument import Document
from Products.SilvaDocument.rendering.xsltrendererbase import XSLTTransformer
from silva.core import conf as silvaconf
from silva.core.interfaces import IRoot
from silva.core.views import views as silvaviews

from Products.SilvaNews.interfaces import INewsItem, INewsItemVersion
from silva.app.news.interfaces import INewsPublication
from Products.SilvaNews.datetimeutils import (datetime_to_unixtimestamp,
    CalendarDatetime)
from Products.SilvaNews.NewsCategorization import NewsCategorization

_ = MessageFactory('silva_news')


class NewsItemVersion(NewsCategorization, Document.DocumentVersion):
    """Base class for news item versions.
    """
    security = ClassSecurityInfo()
    grok.implements(INewsItemVersion)
    meta_type = "Obsolete Article Version"

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


class NewsItem(Document.Document):
    """A News item that appears as an individual page. By adjusting
       settings the Author can determine which subjects, and
       for which audiences the Article should be presented.
    """
    grok.implements(INewsItem)
    security = ClassSecurityInfo()
    meta_type = "Obsolete Article"
    silvaconf.icon("www/news_item.png")
    silvaconf.priority(3.7)
    silvaconf.version_class(NewsItemVersion)

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


NewsHTML = XSLTTransformer('newsitem.xslt', __file__)


class NewsItemView(silvaviews.View):
    """ View on a News Item (either Article / Agenda )
    """
    grok.context(INewsItem)

    def render(self):
        return NewsHTML.transform(self.content, self.request)


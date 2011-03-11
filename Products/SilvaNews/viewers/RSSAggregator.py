# Copyright (c) 2002-2011 Infrae. All rights reserved.
# See also LICENSE.txt
# $Id$

import time

from zope.interface import Interface
from zope import schema
from zope.i18nmessageid import MessageFactory
_ = MessageFactory('silva_news')

# Zope
from AccessControl import ClassSecurityInfo
from App.class_init import InitializeClass

from Products.Silva import SilvaPermissions
from five import grok
from silva.core import conf as silvaconf
from silva.core.views import views as silvaviews
from zeam.form import silva as silvaforms

# SilvaNews
from Products.SilvaNews.viewers.NewsViewer import NewsViewer
from Products.SilvaNews.interfaces import IAggregator
from Products.SilvaNews import feedparser

#XXX
from bethel.core.zopecache import timed

class RSSAggregator(NewsViewer):
    """The aggregator is used to display content from RSS feeds,
       either from Silva or from extenal sites. One or more feeds are
       merged into a listing for public presentation. The titles and
       leads of items in the feeds are displayed together with a link
       to the original article.
    """
    security = ClassSecurityInfo()

    meta_type = 'Silva RSS Aggregator'
    grok.implements(IAggregator)
    silvaconf.icon("www/rss_aggregator.png")
    silvaconf.priority(3.5)

    def __init__(self, id):
        super(RSSAggregator, self).__init__(id)
        self._rss_feeds = []

    # MANIPULATORS

    security.declareProtected(
        SilvaPermissions.ChangeSilvaContent, 'set_feeds')
    def set_feeds(self, rss_feeds):
        self._rss_feeds = rss_feeds
        self._rss_feeds.sort()

    # ACCESSORS

    security.declareProtected(
        SilvaPermissions.AccessContentsInformation, 'get_feeds')
    def get_feeds(self):
        return self._rss_feeds

    security.declareProtected(
        SilvaPermissions.AccessContentsInformation, 'get_feed_contents')
    def get_feed_contents(self):
        """Return the contents of all given feeds in a dict.

        keys are the feeds set with set_feeds, values are dicts describing
        the feeds content.
        """
        return self._read_feeds()

    def _read_feeds(self):
        ret = {}
        for feed in self._rss_feeds:
            res = feedparser.parse(feed)
            ret[feed] = res
        return ret

    security.declareProtected(
        SilvaPermissions.AccessContentsInformation,
        'get_merged_feed_contents')
    #@timed.timedcache(1800,key_with_params=True,func_in_class=True) #cache for 30 minutes
    def get_merged_feed_contents(self):
        feed_data = self.get_feed_contents()
        ret = []
        for uri, channel in feed_data.items():
            for item in channel['items']:
                item['parent_channel'] = {'title':channel['feed']['title'],
                                          'uri':uri}
                ret.append((item.get('date_parsed',None),item))
        ret.sort(reverse=True)
        return [ r[1] for r in ret ]


InitializeClass(RSSAggregator)


class RSSAggregatorAddForm(silvaforms.SMIAddForm):
    grok.context(IAggregator)
    grok.name(u'Silva RSS Aggregator')


class IRSSAggregatorSchema(Interface):
    feeds = schema.List(
                value_type=schema.TextLine(),
                title=_(u'feeds'),
                description=_(u'List the URLs of RSS feeds (one per line) '
                              u'to use as sources of news items.'))


class RSSAggregatorEditForm(silvaforms.SMIEditForm):
    """ Edit form for RSS aggregators
    """
    grok.context(IAggregator)
    fields = silvaforms.Fields(IRSSAggregatorSchema)


class RSSAggregatorView(silvaviews.View):
    grok.context(IAggregator)

    def update(self):
        self.items = self.context.get_merged_feed_contents()



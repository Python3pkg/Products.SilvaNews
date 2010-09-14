# Copyright (c) 2002-2008 Infrae. All rights reserved.
# See also LICENSE.txt
# $Revision: 1.25 $

from zope.interface import implements

import time

from AccessControl import ClassSecurityInfo
try:
    from App.class_init import InitializeClass # Zope 2.12
except ImportError:
    from Globals import InitializeClass # Zope < 2.12

from silva.core import conf as silvaconf
from silva.core.services.interfaces import ICataloging
from Products.Silva import SilvaPermissions

# SilvaNews
from Products.SilvaNews.NewsViewer import NewsViewer
from Products.SilvaNews.interfaces import IAggregator
import feedparser

class RSSAggregator(NewsViewer):
    """The aggregator is used to display content from RSS feeds, either from Silva
       or from extenal sites. One or more feeds are merged into a listing for public 
       presentation. The titles and leads of items in the feeds are displayed 
       together with a link to the original article."""

    security = ClassSecurityInfo()
    implements(IAggregator)
    meta_type = 'Silva RSS Aggregator'
    silvaconf.icon("www/rss_aggregator.png")
    silvaconf.priority(3.5)

    def __init__(self, id):
        RSSAggregator.inheritedAttribute('__init__')(self, id)
        self._rss_feeds = []
        self._last_updated = 0
        self._caching_period = 360 # in seconds
        self._v_cache = None

    # MANIPULATORS

    security.declareProtected(
        SilvaPermissions.ChangeSilvaContent, 'set_feeds')
    def set_feeds(self, channels):
        """splits the channels string argument and stores it"""
        rss_feeds = []
        for channel in channels.split('\n'):
            c = channel.strip()
            if c:
                rss_feeds.append(c)
        rss_feeds.sort()
        old_feeds = self._rss_feeds[:]
        old_feeds.sort()
        if old_feeds != rss_feeds:
            self._rss_feeds = rss_feeds
            self._v_cache = None
            ICataloging(self).reindex()

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
        now = time.time()
        last = now - self._caching_period
        cache = getattr(self, '_v_cache', None)
        if cache is None or cache[0] < last:
            # cache needs to be rebuilt
            ret = self._read_feeds()
            self._v_cache = (now, ret)
        else:
            # deliver cached result
            ret = cache[1]
        return ret
    
    def _read_feeds(self):
        ret = {}
        for feed in self._rss_feeds:
            res = feedparser.parse(feed)
            ret[feed] = res
        return ret

    security.declareProtected(
        SilvaPermissions.AccessContentsInformation, 
        'get_merged_feed_contents')
    def get_merged_feed_contents(self):
        feed_data = self.get_feed_contents()
        ret = []
        for uri, channel in feed_data.items():
            for item in channel['items']:
                item['parent_channel'] = {'title':channel['feed']['title'],
                                          'link':channel['feed']['link'] or uri}
                ret.append((item.get('date_parsed',None),item))
        ret.sort(reverse=True)
        return [ r[1] for r in ret ]

InitializeClass(RSSAggregator)

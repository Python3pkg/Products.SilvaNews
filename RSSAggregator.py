import time

from AccessControl import ClassSecurityInfo
from Globals import InitializeClass
from Products.PageTemplates.PageTemplateFile import PageTemplateFile
from DateTime import DateTime

from Products.Silva.interfaces import IContent
from Products.Silva import SilvaPermissions
from Products.Silva.Content import Content
from Products.Silva.helpers import add_and_edit
from Products.Silva import mangle

from Products.SilvaNews.NewsViewer import NewsViewer

import feedparser

icon = 'www/rss_viewer.png'

class RSSAggregator(NewsViewer):
    """An RSS aggregator that merges a number of feeds into 1 public view"""

    security = ClassSecurityInfo()
    __implements__ = IContent
    meta_type = 'Silva RSS Aggregator'

    def __init__(self, id):
	RSSAggregator.inheritedAttribute('__init__')(self, id)
	self._rss_feeds = []
	self._last_updated = 0
	self._caching_period = 360 # in seconds
        self._v_cache = None
    
    security.declareProtected(SilvaPermissions.ChangeSilvaContent,
			      'set_feeds')
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
            self.reindex_object()

    security.declareProtected(SilvaPermissions.AccessContentsInformation,
			      'get_feeds')
    def get_feeds(self):
        return self._rss_feeds


    security.declareProtected(SilvaPermissions.AccessContentsInformation,
			      'get_feed_contents')
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

    security.declareProtected(SilvaPermissions.AccessContentsInformation,
			      'get_merged_feed_contents')
    def get_merged_feed_contents(self):
        feed_data = self.get_feed_contents()
        ret = []
        for uri, channel in feed_data.items():
            ret.extend(channel['items'])
##         ret.sort(lambda x,y: x['title'] > y['title'])
        return ret
#
###

InitializeClass(RSSAggregator)

manage_addRSSAggregatorForm = PageTemplateFile(
    'www/rssAggregatorAdd', globals(),
    __name__='manage_addRSSAggregatorForm')

def manage_addRSSAggregator(self, id, title, REQUEST=None):
    """Add an RSS Aggregator"""
    if not mangle.Id(self, id).isValid():
	return
    object = RSSAggregator(id)
    self._setObject(id, object)
    obj = getattr(self, id)
    obj.set_title(title)
    add_and_edit(self, id, REQUEST)
    return ''

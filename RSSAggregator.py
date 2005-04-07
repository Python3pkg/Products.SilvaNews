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

from Products.SilvaNews.NewsViewer import NewsViewer, XMLBuffer, quote_xml, RDF_HEADER

import feedparser

icon = 'www/rss_aggregator.png'
addable_priority = 3.5

class RSSAggregator(NewsViewer):
    """The aggregator is used to display content from RSS feeds, either from Silva
       or from extenal sites. One or more feeds are merged into a listing for public 
       presentation. The titles and leads of items in the feeds are displayed 
       together with a link to the original article."""

    security = ClassSecurityInfo()
    __implements__ = IContent
    meta_type = 'Silva RSS Aggregator'

    def __init__(self, id):
	RSSAggregator.inheritedAttribute('__init__')(self, id)
	self._rss_feeds = []
	self._last_updated = 0
	self._caching_period = 360 # in seconds
        self._v_cache = None

    # MANIPULATORS

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

    # ACCESSORS

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

    def rss(self, REQUEST=None):
        """return the contents of this viewer as an RSS/RDF (RSS 1.0) feed"""
        if REQUEST is not None:
            REQUEST.RESPONSE.setHeader('Content-Type', 'text/xml;charset=UTF-8')
        
        # create RDF/XML for the channel
        xml = XMLBuffer()
        xml.write(RDF_HEADER)

        # get the metadata binding to get the metadata for this viewer
        mdbinding = self.service_metadata.getMetadata(self)
        creationdate = mdbinding.get('silva-extra', 'creationtime')
        
        # create RDF/XML frame
        xml.write('<channel rdf:about="%s">\n' % self.absolute_url())
        xml.write('<title>%s</title>\n' % quote_xml(self.get_title()))
        xml.write('<link>%s</link>\n' % self.absolute_url())
        xml.write('<description>%s</description>\n' %
                  quote_xml(mdbinding.get('silva-extra', 'content_description')))
        xml.write('<dc:creator>%s</dc:creator>\n' %
                  quote_xml(mdbinding.get('silva-extra', 'creator')))
	date = creationdate.HTML4()
        xml.write('<dc:date>%s</dc:date>\n' % quote_xml(date))

	# output <items> list
	# and store items in a list
	itemlist = self.get_merged_feed_contents()
	xml.write('<items>\n<rdf:Seq>\n')
        for item in itemlist:
	    url = quote_xml(item['link'])
	    xml.write('<rdf:li rdf:resource="%s" />\n' % url)
	xml.write('</rdf:Seq>\n</items>\n')
        xml.write('</channel>\n\n')
        # loop over the itemslist and create a RSS/RDF item elements
        for item in itemlist:
            self._rss_item_helper(item, xml)
        # DONE
        xml.write('</rdf:RDF>\n')
        # return XML
        return xml.read()

    def _rss_item_helper(self, item, xml):
        """convert a single item (dict) to an RSS/RDF 'item' element"""
        url = quote_xml(item['link'])
        xml.write('<item rdf:about="%s">\n' % url)
        # RSS elements
        xml.write('<title>%s</title>\n' % quote_xml(item['title']))
        xml.write('<link>%s</link>\n' % url)
        try:
            xml.write('<description>%s</description>\n' %
                      quote_xml(item['description']))
        except KeyError:
            pass
        xml.write('</item>\n')
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

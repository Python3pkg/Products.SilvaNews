from Products.Five import BrowserView
from Products.Silva.adapters.interfaces import IFeedEntry

from DateTime import DateTime

from zope.interface import implements

from Products.Silva.adapters import interfaces as silvainterfaces
from Products.SilvaNews.interfaces import INewsItem
from Products.SilvaDocument.adapters import feedentry

class ViewerFeedView(BrowserView):
    """Base class for feed representation."""
    def __call__(self):
        self.request.RESPONSE.setHeader(
            'Content-Type', 'text/xml;charset=UTF-8')
        return super(ViewerFeedView, self).__call__(self)

    def _get_entries(self,entries,date_updated):
        items = self.context.get_items()
        
        for item in items:
            i = item.getObject().get_content()
            entry = IFeedEntry(i, None)
            if not entry is None:
                entry_updated = entry.date_updated()
                entries.append(entry)
                if entry_updated > date_updated:
                    date_updated = entry_updated
        
    def get_data(self):
        """ prepare the data needed by a feed
        """
        context = self.context

        ms = context.service_metadata
        date_updated = ms.getMetadataValue(
            self.context, 'silva-extra', 'creationtime')

        entries = []
        self._get_entries(entries,date_updated)

        url = context.absolute_url()
        return {
            'id': url,
            'title': context.get_title(),
            'description': ms.getMetadataValue(
                self.context, 'silva-extra', 'content_description'),
            'url': url,
            'authors': [ms.getMetadataValue(
                self.context, 'silva-extra', 'creator')],
            'date_updated': date_updated,
            'entries': entries
            }

class AggregatorFeedEntry(object):
    implements(silvainterfaces.IFeedEntry)

    def __init__(self, item):
        self.item = item

    def id(self):
        return quote_xml(self.item['link'])

    def title(self):
        titl = self.item['title']
        if self.item['parent_channel']['title']:
            titl += ' [%s]'%self.item['parent_channel']['title']
        return titl

    def html_description(self):
        desc = self.item['description']
        return desc

    def description(self):
        return self.html_description()

    def url(self):
        return self.id()

    def authors(self):
        return []

    def date_updated(self):
        return DateTime(self.item['modified'])

    def date_published(self):
        return DateTime(self.item['date'])

    def keywords(self):
        return []

    def subject(self):
        return None

    
class AggregatorFeedView(ViewerFeedView):
    def __call__(self):
        self.request.RESPONSE.setHeader(
            'Content-Type', 'text/xml;charset=UTF-8')
        return super(ViewerFeedView, self).__call__(self)

    def _get_entries(self,entries,date_updated):
        items = self.context.get_merged_feed_contents()
        
        for item in items:
            entry = AggregatorFeedEntry(item)
            entry_updated = entry.date_updated()
            entries.append(entry)
            if entry_updated > date_updated:
                date_updated = entry_updated


def quote_xml ( data ):
    """Quote string for XML usage.
    """
    if not data:
        return data
    data = data.replace('&', '&amp;')
    data = data.replace('"', '&quot;')
    data = data.replace('<', '&lt;')
    data = data.replace('>', '&gt;')
    return data

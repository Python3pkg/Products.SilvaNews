# Copyright (c) 2002-2011 Infrae. All rights reserved.
# See also LICENSE.txt
# $Id$

from five import grok
from Products.SilvaDocument.adapters import feedentry
from Products.SilvaNews.interfaces import INewsItem, IAgendaItem


class NewsItemFeedEntryAdapter(feedentry.DocumentFeedEntryAdapter):
    """Adapter for Silva News Items (article, agenda) to get an atom/rss feed entry 
    representation."""
    grok.context(INewsItem)

    def html_description(self):
        return self.ms.getMetadataValue(self.version, 'syndication','teaser')

    def date_published(self):
        """ This field is used for ordering.
        """
        return self.version.display_datetime()

    def url(self):
        #override the parent url method, to take into account
        # external urls -- if external url and display_method are
        # set, then the url should be to the external url
        if self.version.link_method()=='external_link':
            return self.version.external_link()
        elif self.version.link_method()=='nothing':
            return ''
        else:
            return super(NewsItemFeedEntryAdapter, self).url()


class AgendaItemFeedEntryAdapter(NewsItemFeedEntryAdapter):
    grok.context(IAgendaItem)

    def location(self):
        return self.version.get_location()

    def start_datetime(self):
        return self.version.get_start_datetime().isoformat()

    def end_datetime(self):
        edt = self.version.get_end_datetime()
        return (edt and edt.isoformat()) or edt

# Copyright (c) 2002-2011 Infrae. All rights reserved.
# See also LICENSE.txt
# $Id$

from five import grok
from Products.SilvaDocument.adapters import feedentry
from Products.SilvaNews.interfaces import INewsItem, IAgendaItem


class NewsItemFeedEntryAdapter(feedentry.DocumentFeedEntryAdapter):
    """Adapter for Silva News Items (article, agenda) to get an
    atom/rss feed entry representation.
    """
    grok.context(INewsItem)

    def html_description(self):
        return self.version.get_intro()

    def date_published(self):
        """ This field is used for ordering.
        """
        return self.version.display_datetime()


class AgendaItemFeedEntryAdapter(NewsItemFeedEntryAdapter):
    grok.context(IAgendaItem)

    def _get_occurrence(self):
        occurrences = self.version.get_occurrences()
        if len(occurrences):
            return occurrences[0]
        return None

    def location(self):
        occurrrence = self._get_occurrence()
        if occurrrence is not None:
            return occurrrence.get_location()
        return None

    def start_datetime(self):
        occurrrence = self._get_occurrence()
        if occurrrence is not None:
            return occurrrence.get_start_datetime().isoformat()
        return None

    def end_datetime(self):
        occurrrence = self._get_occurrence()
        if occurrrence is not None:
            dt = occurrrence.get_end_datetime()
            if dt:
                return dt.isoformat()
        return None


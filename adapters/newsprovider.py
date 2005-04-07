# Copyright (c) 2002-2004 Infrae. All rights reserved.
# See also LICENSE.txt
# $Id: newsprovider.py,v 1.1.2.2 2005/04/07 10:00:10 guido Exp $
#

import Globals
from AccessControl import ClassSecurityInfo
from DateTime import DateTime

from Products.Silva.adapters import adapter
from Products.SilvaNews.adapters import interfaces

from Products.Silva import SilvaPermissions

class NewsItemReference:
    """a temporary object to wrap a newsitem"""

    __allow_access_to_unprotected_subobjects__ = 1

    def __init__(self, item, context):
        self._item = item
        self._context = context

    def id(self):
        return self._item.id

    def title(self):
        return self._item.get_title()

    def description(self, maxchars=1024):
        # we can be sure there is no markup here, so just limit
        desc = self._item.get_description()
        if desc is None:
            return ''
        return desc[:maxchars]

    def link(self):
        return self._item.aq_parent.absolute_url()

    def intro(self, maxchars=1024):
        return self._item.get_intro(maxchars)
    
    def creation_datetime(self):
        creation_datetime = self._context.service_metadata.getMetadataValue(
                        self._item, 'silva-extra', 'creationtime')
        return creation_datetime

    def start_datetime(self):
        return getattr(self._item, 'start_datetime', None)

    def end_datetime(self):
        return getattr(self._item, 'end_datetime', None)

    def location(self):
        return getattr(self._item, 'location', None)

Globals.InitializeClass(NewsItemReference)

class NewsViewerNewsProvider(adapter.Adapter):

    __implements__ = interfaces.INewsProvider

    def getitems(self, number):
        context = self.context
        context.verify_filters()
        results = []
        for newsfilter in context._filters:
            filterob = context.aq_inner.restrictedTraverse(newsfilter)
            res = filterob.get_last_items(number, False)
            results += res
        results = context._remove_doubles(results)
        ret = []
        for item in results[:number]:
            obj = item.getObject()
            ref = NewsItemReference(obj, self.context)
            ret.append(ref)
        return ret

class AgendaViewerNewsProvider(adapter.Adapter):

    __implements__ = interfaces.INewsProvider

    def getitems(self, number):
        context = self.context
        results = []
        for newsfilter in context._filters:
            filterob = context.aq_inner.restrictedTraverse(newsfilter)
            query = newfilter._prepare_query(['Silva Plain AgendaItem'])
            query['sort_on'] = 'idx_start_datetime'
            query['sort_order'] = 'ascending'
            now = DateTime()
            # request everything until 100 years after now
            end = DateTime() + (100 * 365.25)
            query['idx_start_datetime'] = (now, end)
            query['idx_start_datetime_usage'] = 'range:min:max'
            res = filterob._query(query)
            results += res
        ret = []
        for item in results[:number]:
            obj = item.getObject()
            ref = NewsItemReference(obj, self.context)
            ret.append(ref)
        return ret

class RSSItemReference:
    """a temporary object to wrap a newsitem"""

    __allow_access_to_unprotected_subobjects__ = 1

    def __init__(self, item, context):
        self._item = item
        self._context = context

    def id(self):
        return self._item['title']

    def title(self):
        return self._item['title']

    def description(self, maxchars=1024):
        # XXX we're not so sure about the type of content, so let's not
        # try to limit it for now...
        return self._item['description']

    def link(self):
        return self._item['link']

    def intro(self, maxchars=1024):
        return self.description(maxchars)
    
    def creation_datetime(self):
        return (self._toDateTime(self._item.get('created')) or 
                self._toDateTime(self._item.get('date')) or None)

    def start_datetime(self):
        return None

    def end_datetime(self):
        return None

    def location(self):
        return getattr(self._item, 'location', None)

    def _toDateTime(self, dt):
        """converts a Python datetime object to a Zope DateTime one"""
        if dt is None:
            return None
        if type(dt) in [str, unicode]:
            # string
            return DateTime(dt)
        elif type(dt) == tuple:
            # tuple 
            return DateTime(*dt)
        # datetime?
        return DateTime(dt.year, dt.month, dt.day, dt.hour, dt.minute)

Globals.InitializeClass(NewsItemReference)

class RSSAggregatorNewsProvider(adapter.Adapter):
    
    __implements__ = interfaces.INewsProvider

    def getitems(self, number):
        """return a number of the most current items

            note that this may return less than number, since the RSS feed
            might not provide enough items
        """
        items = self.context.get_merged_feed_contents()
        ret = []
        for item in items:
            ret.append(RSSItemReference(item, self.context))
        return ret

def getNewsProviderAdapter(context):
    if context.meta_type == 'Silva News Viewer':
        return NewsViewerNewsProvider(context)
    elif context.meta_type == 'Silva Agenda Viewer':
        return AgendaViewerNewsProvider(context) 
    elif context.meta_type == 'Silva RSS Aggregator':
        return RSSAggregatorNewsProvider(context)

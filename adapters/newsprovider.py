# Copyright (c) 2002-2004 Infrae. All rights reserved.
# See also LICENSE.txt
# $Id: newsprovider.py,v 1.1.2.1 2005/03/23 16:14:37 guido Exp $
#

import Globals
from AccessControl import ClassSecurityInfo

from Products.Silva.adapters import adapter
from Products.SilvaNews.adapters import interfaces

from Products.Silva import SilvaPermissions

class NewsItemReference:
    """a temporary object to wrap a newsitem"""

    __allow_access_to_unprotected_subobjects__ = 1

    def __init__(self, id, title, link, description,
                    intro, creationtime, start_datetime, 
                    end_datetime, location):
        self._id = id
        self._title = title
        self._link = link
        self._description = description
        self._intro = intro
        self._creationtime = creationtime
        self._start_datetime = start_datetime
        self._end_datetime = end_datetime
        self._location = location

    def id(self):
        """return the id"""
        return self._id

    def title(self):
        """returns the title"""
        return self._title

    def description(self):
        """returns the description"""
        return self._description

    def link(self):
        """returns a link to the item"""
        return self._link

    def intro(self):
        """return the info"""
        return self._intro

    def creationtime(self):
        """returns the creation time"""
        return self._creationtime

    def start_datetime(self):
        """returns the start datetime"""
        return self._start_datetime

    def end_datetime(self):
        """return the end datetime"""
        return self._end_datetime

    def location(self):
        """returns the location (if any)"""
        return self._location

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
            creationtime = context.service_metadata.getMetadataValue(
                            obj, 'silva-extra', 'creationtime')
            ref = NewsItemReference(obj.id, obj.get_title(), 
                    obj.aq_parent.absolute_url(), obj.get_description(),
                    obj.get_intro(), creationtime,
                    getattr(obj, 'start_datetime', lambda: None)(),
                    getattr(obj, 'end_datetime', lambda: None)(),
                    getattr(obj, 'location', lambda: None)())
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
            creationtime = context.service_metadata.getMetadataValue(
                            obj, 'silva-extra', 'creationtime')
            ref = NewsItemReference(obj.id, obj.get_title(), 
                    obj.aq_parent.absolute_url(), obj.get_description(),
                    obj.get_intro(), creationtime,
                    obj.start_datetime(), obj.end_datetime(),
                    obj.location())
            ret.append(ref)
        return ret

class RSSAggregatorNewsProvider(adapter.Adapter):
    
    __implements__ = interfaces.INewsProvider

    def getitems(self, number):
        """return a number of the most current items

            note that this may return less than number, since the RSS feed
            might not provide enough items
        """

def getNewsProviderAdapter(context):
    if context.meta_type == 'Silva News Viewer':
        return NewsViewerNewsProvider(context)
    elif context.meta_type == 'Silva Agenda Viewer':
        return AgendaViewerNewsProvider(context) 
    elif context.meta_type == 'Silva RSS Aggregator':
        return RSSAggregatorNewsProvider(context)

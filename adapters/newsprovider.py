# Copyright (c) 2002-2009 Infrae. All rights reserved.
# See also LICENSE.txt
# $Id: newsprovider.py,v 1.3 2005/05/02 14:22:52 guido Exp $
#
from zope.interface import implements

from silva.core import conf as silvaconf
from silva.core.conf import component

import Globals
from AccessControl import ClassSecurityInfo
from DateTime import DateTime

from Products.Silva import SilvaPermissions
from Products.Silva.adapters import adapter

from Products.SilvaNews.adapters import interfaces
from Products.SilvaNews.interfaces import INewsViewer, IAggregator, IAgendaViewer, INewsItem

class NewsViewerNewsProvider(component.Adapter):
    """Works for BOTH News and Agenda Viewers!"""

    silvaconf.context(INewsViewer)
    implements(interfaces.INewsProvider)

    def getitems(self, number):
        results = self.context.get_items()
        ret = []
        if len(results) < number:
            number = len(results)
        for item in results[:number]:
            obj = item.getObject()
            ref = NewsItemReference(obj, self.context)
            ret.append(ref)
        return ret

class NewsItemReference(object):
    """a temporary object to wrap a newsitem"""

    implements(interfaces.INewsItemReference)

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
        if maxchars > 0:
          desc = desc[:maxchars]
        return desc

    def link(self):
        return self._item.aq_parent.absolute_url()

    def intro(self, maxchars=1024):
        return self._item.get_intro(maxchars)
    
    def thumbnail(self):
        return self._item.get_thumbnail('inv_thumbnail')

    def creation_datetime(self):
        pub_dt = self._context.service_metadata.getMetadataValue(
                        self._item, 'silva-extra', 'publicationtime')
        display_dt = self._item.display_datetime()
        return display_dt or pub_dt

    def start_datetime(self):
        return getattr(self._item.aq_explicit, 'start_datetime', lambda: None)()

    def end_datetime(self):
        return getattr(self._item.aq_explicit, 'end_datetime', lambda: None)()

    def location(self):
        return getattr(self._item.aq_explicit, 'location', lambda: None)()

    def get_news_item(self):
        return self._item
Globals.InitializeClass(NewsItemReference)

class RSSItemReference(object):
    """a temporary object to wrap a newsitem"""

    implements(interfaces.INewsItemReference)

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
    
    def thumbnail(self):
        return None

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
        """converts a Python datetime object to a localized Zope 
           DateTime one"""
        if dt is None:
            return None
        if type(dt) in [str, unicode]:
            # string
            dt = DateTime(dt)
            return dt.toZone(dt.localZone())
        elif type(dt) == tuple:
            # tuple 
            return DateTime(*dt)
        # datetime?
        return DateTime(dt.year, dt.month, dt.day, dt.hour, dt.minute)

    def get_news_item(self):
        return self._item

class RSSAggregatorNewsProvider(component.Adapter):
    
    implements(interfaces.INewsProvider)
    silvaconf.context(IAggregator)

    def getitems(self, number):
        """return a number of the most current items

            note that this may return less than number, since the RSS feed
            might not provide enough items
        """
        items = self.context.get_merged_feed_contents()
        ret = []
        for item in items:
            ret.append(RSSItemReference(item, self.context))
        return ret[:number]

def getNewsProviderAdapter(context):
    """use zope3 adapter lookup mechanism to get the correct adapter"""
    """This function is here in case we need to lookup the adapter from
    untrusted code"""
    return INewsProvider(context)

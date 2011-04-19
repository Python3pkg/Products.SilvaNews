# Copyright (c) 2002-2011 Infrae. All rights reserved.
# See also LICENSE.txt


from Products.Silva.silvaxml.xmlimport import (
    SilvaBaseHandler, NS_URI,
    generateUniqueId, updateVersionCount)
from Products.Silva import mangle
from silva.core import conf as silvaconf

from Products.SilvaDocument.silvaxml.xmlimport import (resolve_path)
from Products.SilvaNews.silvaxml.xmlexport import NS_SILVA_NEWS
from Products.SilvaNews.silvaxml.helpers import *
from Products.SilvaNews.PlainArticle import (
    PlainArticle, PlainArticleVersion)
from Products.SilvaNews.PlainAgendaItem import (
    PlainAgendaItem, PlainAgendaItemVersion)
from Products.SilvaNews.datetimeutils import get_timezone
from silva.app.page.xmlexport import NS_CL
from silva.app.page.xmlimport import (ContentLayoutPartHandler,
                                      ConfigElementHandler)

silvaconf.namespace(NS_SILVA_NEWS)


class SNNHandlerMixin(object):
    """ mixin class to handle shared attribute setting across
        many of the SNN objects """

    def set_attrs(self,attrs,obj):
        set_attribute_as_list(obj, 'target_audiences', attrs)
        set_attribute_as_list(obj, 'subjects', attrs)
        set_attribute_as_bool(obj, 'number_is_days', attrs)
        set_attribute_as_bool(obj, 'show_agenda_items', attrs)
        set_attribute_as_bool(obj, 'keep_to_path', attrs)
        set_attribute_as_int(obj, 'number_to_show', attrs)
        set_attribute_as_int(obj, 'number_to_show_archive', attrs)
        set_attribute_as_int(obj, 'days_to_show', attrs)
        set_attribute_as_int(obj, 'year_range', attrs)
        if attrs.has_key((None,'excluded_items')):
            eis = attrs[(None,'excluded_items')]
            for ei in eis.split(','):
                obj.set_excluded_item(ei,True)


class PlainArticleHandler(SilvaBaseHandler):
    silvaconf.name('plainarticle')

    def getOverrides(self):
        return {(NS_URI, 'content'): PlainArticleContentHandler}

    def startElementNS(self, name, qname, attrs):
        if name == (NS_SILVA_NEWS, 'plainarticle'):
            id = attrs[(None, 'id')].encode('utf-8')
            uid = self.generateOrReplaceId(id)
            object = PlainArticle(uid)
            self.parent()._setObject(uid, object)
            last_author = attrs.get((None, 'last_author'),None)
            if last_author:
                self.setAuthor(getattr(self.parent(), uid), self.parent(),
                               last_author)
            self.setResultId(uid)

    def endElementNS(self, name, qname):
        if name == (NS_SILVA_NEWS, 'plainarticle'):
            self.notifyImport()


class PlainArticleContentHandler(SilvaBaseHandler):
    silvaconf.baseclass()

    def getOverrides(self):
        return{(NS_CL, 'part'): ContentLayoutPartHandler}

    def startElementNS(self, name, qname, attrs):
        if name == (NS_URI, 'content'):
            id = attrs[(None, 'version_id')].encode('utf-8')
            if not mangle.Id(self._parent, id).isValid():
                return
            version = PlainArticleVersion(id)
            parent = self.parent()
            parent._setObject(id, version)
            version = version.__of__(parent)

            set_attribute_as_list(version, 'target_audiences', attrs)
            set_attribute_as_list(version, 'subjects', attrs)
            set_attribute_as_naive_datetime(version, 'display_datetime', attrs)

            last_author = attrs.get((None, 'last_author'),None)
            if last_author:
                self.setAuthor(getattr(self.parent(), uid), self.parent(),
                               last_author)

            self.setResultId(id)
            updateVersionCount(self)

    def endElementNS(self, name, qname):
        if name == (NS_URI, 'content'):
            self.storeMetadata()
            self.storeWorkflow()


class PlainAgendaItemHandler(SilvaBaseHandler):
    silvaconf.name('plainagendaitem')

    def getOverrides(self):
        return {(NS_URI, 'content'): PlainAgendaItemContentHandler}

    def startElementNS(self, name, qname, attrs):
        if name == (NS_SILVA_NEWS, 'plainagendaitem'):
            id = attrs[(None, 'id')].encode('utf-8')
            uid = self.generateOrReplaceId(id)
            object = PlainAgendaItem(uid)
            self.parent()._setObject(uid, object)

            last_author = attrs.get((None, 'last_author'),None)
            if last_author:
                self.setAuthor(getattr(self.parent(), uid), self.parent(),
                               last_author)

            self.setResultId(uid)

    def endElementNS(self, name, qname):
        if name == (NS_SILVA_NEWS, 'plainagendaitem'):
            self.notifyImport()


class PlainAgendaItemContentHandler(SilvaBaseHandler):
    silvaconf.baseclass()

    def getOverrides(self):
        return {(NS_CL, 'part'): ContentLayoutPartHandler}

    def startElementNS(self, name, qname, attrs):
        if name == (NS_URI, 'content'):
            id = attrs[(None, 'version_id')].encode('utf-8')
            if not mangle.Id(self._parent, id).isValid():
                return
            version = PlainAgendaItemVersion(id)
            parent = self.parent()
            parent._setObject(id, version)
            version = version.__of__(parent)

            set_attribute_as_list(version, 'target_audiences', attrs)
            set_attribute_as_list(version, 'subjects', attrs)
            set_attribute(version, 'location', attrs)
            set_attribute(version, 'recurrence', attrs)
            tz_name = set_attribute(version, 'timezone_name', attrs)
            tz = None
            if tz_name:
                tz = get_timezone(tz_name)
            set_attribute_as_bool(version, 'all_day', attrs)
            set_attribute_as_datetime(version, 'start_datetime', attrs, tz=tz)
            set_attribute_as_datetime(version, 'end_datetime', attrs, tz=tz)
            set_attribute_as_naive_datetime(version, 'display_datetime', attrs)

            last_author = attrs.get((None, 'last_author'),None)
            if last_author:
                self.setAuthor(getattr(self.parent(), uid), self.parent(),
                               last_author)

            self.setResultId(id)
            updateVersionCount(self)

    def endElementNS(self, name, qname):
        if name == (NS_URI, 'content'):
            self.storeMetadata()
            self.storeWorkflow()


class NewsPublicationHandler(SilvaBaseHandler):
    silvaconf.name('newspublication')

    def startElementNS(self, name, qname, attrs):
        if name == (NS_SILVA_NEWS, silvaconf.name.bind(self).get(self)):
            id = str(attrs[(None, 'id')])
            parent = self.parent()
            if self.settings().replaceObjects() and id in parent.objectIds():
                self.setResultId(id)
                return
            uid = generateUniqueId(id, parent)
            factory = self.parent().manage_addProduct['SilvaNews']
            factory.manage_addNewsPublication(uid, '', create_default=0)
            last_author = attrs.get((None, 'last_author'),None)
            if last_author:
                self.setAuthor(getattr(self.parent(), uid), self.parent(),
                               last_author)
            self.setResultId(uid)

    def endElementNS(self, name, qname):
        if name == (NS_SILVA_NEWS, silvaconf.name.bind(self).get(self)):
            self.storeMetadata()
            self.notifyImport()


class NewsViewerHandler(SNNHandlerMixin, SilvaBaseHandler):
    """Import a defined News Viewer.
    """
    silvaconf.name('newsviewer')
    factory_name = 'manage_addNewsViewer'

    def startElementNS(self, name, qname, attrs):
        if name == (NS_SILVA_NEWS, silvaconf.name.bind(self).get(self)):
            id = str(attrs[(None, 'id')])
            uid = self.generateOrReplaceId(id)
            factory = self.parent().manage_addProduct['SilvaNews']
            getattr(factory, self.factory_name)(uid,'')
            obj = getattr(self.parent(),uid)
            self.set_attrs(attrs,obj)
            self.setResultId(uid)

        if name == (NS_SILVA_NEWS, 'filter'):
            target = attrs[(None, 'target')]
            info = self.getInfo()
            info.addAction(
                resolve_path,
                [self.result().add_filter, info, target])

    def endElementNS(self, name, qname):
        if name == (NS_SILVA_NEWS, silvaconf.name.bind(self).get(self)):
            self.storeMetadata()
            self.notifyImport()


class AgendaViewerHandler(SNNHandlerMixin, SilvaBaseHandler):
    """Import a defined Agenda Viewer.
    """
    silvaconf.name('agendaviewer')
    factory_name = 'manage_addAgendaViewer'

    def startElementNS(self, name, qname, attrs):
        if name == (NS_SILVA_NEWS, silvaconf.name.bind(self).get(self)):
            id = str(attrs[(None, 'id')])
            uid = self.generateOrReplaceId(id)
            factory = self.parent().manage_addProduct['SilvaNews']
            factory.manage_addAgendaViewer(uid,'')
            obj = getattr(self.parent(),uid)
            self.set_attrs(attrs,obj)
            set_attribute_as_naive_datetime(obj, 'starting_date', attrs)
            self.setResultId(uid)

    def endElementNS(self, name, qname):
        if name == (NS_SILVA_NEWS, silvaconf.name.bind(self).get(self)):
            self.storeMetadata()
            self.notifyImport()


class NewsFilterHandler(SNNHandlerMixin, SilvaBaseHandler):
    silvaconf.name('newsfilter')
    factory_name = 'manage_addNewsFilter'

    def startElementNS(self, name, qname, attrs):
        if name == (NS_SILVA_NEWS, silvaconf.name.bind(self).get(self)):
            id = str(attrs[(None, 'id')])
            uid = self.generateOrReplaceId(id)
            factory = self.parent().manage_addProduct['SilvaNews']
            getattr(factory, self.factory_name)(uid, '')
            obj = getattr(self.parent(),uid)
            self.set_attrs(attrs,obj)
            self.setResultId(uid)

        if name == (NS_SILVA_NEWS, 'source'):
            target = attrs[(None, 'target')]
            info = self.getInfo()
            info.addAction(
                resolve_path,
                [self.result().add_source, info, target])

    def endElementNS(self, name, qname):
        if name == (NS_SILVA_NEWS, silvaconf.name.bind(self).get(self)):
            self.storeMetadata()
            self.notifyImport()


class AgendaFilterHandler(NewsFilterHandler):
    """Import an Agenda Filter.
    """
    silvaconf.name('agendafilter')
    factory_name = 'manage_addAgendaFilter'


class CategoryFilterHandler(SNNHandlerMixin, SilvaBaseHandler):
    """Import a CategoryFilter.
    """
    silvaconf.name('categoryfilter')

    def startElementNS(self, name, qname, attrs):
        if name == (NS_SILVA_NEWS,'categoryfilter'):
            id = str(attrs[(None, 'id')])
            uid = self.generateOrReplaceId(id)
            factory = self.parent().manage_addProduct['SilvaNews']
            factory.manage_addCategoryFilter(uid,'')
            obj = getattr(self.parent(),uid)
            self.set_attrs(attrs,obj)
            self.setResultId(uid)

    def endElementNS(self, name, qname):
        if name == (NS_SILVA_NEWS, 'categoryfilter'):
            self.storeMetadata()
            self.notifyImport()


class RSSAggregatorHandler(SilvaBaseHandler):
    """Import a defined RSS Aggregator.
    """
    silvaconf.name('rssaggregator')

    def startElementNS(self, name, qname, attrs):
        if name == (NS_SILVA_NEWS,'rssaggregator'):
            id = str(attrs[(None, 'id')])
            uid = self.generateOrReplaceId(id)
            factory = self.parent().manage_addProduct['SilvaNews']
            factory.manage_addRSSAggregator(uid,'')
            obj = getattr(self.parent(),uid)
            if (attrs.get((None, 'feed_urls'),None)):
                feed_urls = attrs[(None,'feed_urls')]
                # reformat feed_urls to be in the format set_feeds expects
                obj.set_feeds(feed_urls)
            self.setResultId(uid)

    def endElementNS(self, name, qname):
        if name == (NS_SILVA_NEWS, 'rssaggregator'):
            self.storeMetadata()
            self.notifyImport()


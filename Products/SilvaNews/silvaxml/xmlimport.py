# -*- coding: utf-8 -*-
# Copyright (c) 2002-2013 Infrae. All rights reserved.
# See also LICENSE.txt

from silva.core.xml import handlers
from Products.Silva.silvaxml.xmlimport import NS_SILVA_URI as NS_URI
from Products.Silva import mangle
from silva.core import conf as silvaconf

from Products.SilvaNews.silvaxml.xmlexport import NS_SILVA_NEWS
from Products.SilvaNews.silvaxml import helpers
from Products.SilvaNews.NewsItem import (
    NewsItem, NewsItemVersion)
from Products.SilvaNews.AgendaItem import (
    AgendaItem, AgendaItemVersion)
from Products.SilvaDocument.silvaxml.xmlimport import DocXMLHandler
from Products.SilvaDocument.silvaxml import NS_DOCUMENT_URI as NS_SILVA_DOCUMENT

silvaconf.namespace(NS_SILVA_NEWS)


class SNNHandlerMixin(object):
    """ mixin class to handle shared attribute setting across
        many of the SNN objects """

    def set_attrs(self,attrs,obj):
        helpers.set_attribute_as_list(obj, 'target_audiences', attrs)
        helpers.set_attribute_as_list(obj, 'subjects', attrs)
        helpers.set_attribute_as_bool(obj, 'number_is_days', attrs)
        helpers.set_attribute_as_bool(obj, 'show_agenda_items', attrs)
        helpers.set_attribute_as_bool(obj, 'keep_to_path', attrs)
        helpers.set_attribute_as_int(obj, 'number_to_show', attrs)
        helpers.set_attribute_as_int(obj, 'number_to_show_archive', attrs)
        if (None,'excluded_items') in attrs:
            eis = attrs[(None,'excluded_items')]
            for ei in eis.split(','):
                obj.add_excluded_item(ei)


class NewsItemHandler(handlers.SilvaHandler):
    silvaconf.name('plainarticle')

    def getOverrides(self):
        return {(NS_URI, 'content'): NewsItemContentHandler}

    def startElementNS(self, name, qname, attrs):
        if name == (NS_SILVA_NEWS, 'plainarticle'):
            id = attrs[(None, 'id')].encode('utf-8')
            uid = self.generateOrReplaceId(id)
            object = NewsItem(uid)
            self.parent()._setObject(uid, object)
            self.setResultId(uid)

    def endElementNS(self, name, qname):
        if name == (NS_SILVA_NEWS, 'plainarticle'):
            self.notifyImport()


class NewsItemContentHandler(handlers.SilvaVersionHandler):
    silvaconf.baseclass()

    def getOverrides(self):
        return{(NS_SILVA_DOCUMENT, 'doc'): DocXMLHandler}

    def startElementNS(self, name, qname, attrs):
        if name == (NS_URI, 'content'):
            id = attrs[(None, 'version_id')].encode('utf-8')
            if not mangle.Id(self._parent, id).isValid():
                return
            version = NewsItemVersion(id)
            parent = self.parent()
            parent._setObject(id, version)
            version = version.__of__(parent)

            helpers.set_attribute_as_list(version, 'target_audiences', attrs)
            helpers.set_attribute_as_list(version, 'subjects', attrs)
            helpers.set_attribute_as_naive_datetime(
                version, 'display_datetime', attrs)

            self.setResultId(id)
            self.updateVersionCount()

    def endElementNS(self, name, qname):
        if name == (NS_URI, 'content'):
            self.storeMetadata()
            self.storeWorkflow()


class AgendaItemHandler(handlers.SilvaHandler):
    silvaconf.name('plainagendaitem')

    def getOverrides(self):
        return {(NS_URI, 'content'): AgendaItemContentHandler}

    def startElementNS(self, name, qname, attrs):
        if name == (NS_SILVA_NEWS, 'plainagendaitem'):
            id = attrs[(None, 'id')].encode('utf-8')
            uid = self.generateOrReplaceId(id)
            object = AgendaItem(uid)
            self.parent()._setObject(uid, object)
            self.setResultId(uid)

    def endElementNS(self, name, qname):
        if name == (NS_SILVA_NEWS, 'plainagendaitem'):
            self.notifyImport()


class AgendaItemContentHandler(handlers.SilvaVersionHandler):
    silvaconf.baseclass()

    def getOverrides(self):
        return{(NS_SILVA_DOCUMENT, 'doc'): DocXMLHandler}

    def startElementNS(self, name, qname, attrs):
        if name == (NS_URI, 'content'):
            id = attrs[(None, 'version_id')].encode('utf-8')
            if not mangle.Id(self._parent, id).isValid():
                return
            version = AgendaItemVersion(id)
            parent = self.parent()
            parent._setObject(id, version)
            version = version.__of__(parent)

            helpers.set_attribute_as_list(version, 'target_audiences', attrs)
            helpers.set_attribute_as_list(version, 'subjects', attrs)
            helpers.set_attribute_as_naive_datetime(
                version, 'display_datetime', attrs)

            self.setResultId(id)
            self.updateVersionCount()

    def endElementNS(self, name, qname):
        if name == (NS_URI, 'content'):
            self.storeMetadata()
            self.storeWorkflow()


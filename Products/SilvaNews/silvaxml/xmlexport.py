# -*- coding: utf-8 -*-
# Copyright (c) 2002-2012 Infrae. All rights reserved.
# See also LICENSE.txt

from five import grok
from zope.interface import Interface

from Products.SilvaNews import interfaces
from silva.app.news.datetimeutils import utc_datetime
from Products.SilvaDocument.silvaxml.xmlexport import DocumentVersionProducer
from Products.SilvaNews.silvaxml import NS_SILVA_NEWS
from silva.core.xml import producers


def iso_datetime(dt):
    if dt:
        string = utc_datetime(dt).replace(microsecond=0).isoformat()
        if string.endswith('+00:00'):
            string = string[:-6] + 'Z'
        return string
    return ''


class PlainArticleProducer(producers.SilvaVersionedContentProducer):
    """Export a PlainArticle object to XML.
    """
    grok.adapts(interfaces.INewsItem, Interface)

    def sax(self):
        """sax"""
        self.startElementNS(NS_SILVA_NEWS,
                            'plainarticle',
                            {'id': self.context.id})
        self.sax_workflow()
        self.sax_versions()
        self.endElementNS(NS_SILVA_NEWS,'plainarticle')


class PlainArticleVersionProducer(DocumentVersionProducer):
    """Export a version of a PlainArticle object to XML.
    """
    grok.adapts(interfaces.INewsItemVersion, Interface)

    def sax(self):
        """sax"""
        self.startElement(
            'content',
            {'version_id': self.context.id,
             'subjects': ','.join(self.context.get_subjects()),
             'target_audiences': ','.join(self.context.get_target_audiences()),
             'display_datetime': iso_datetime(
                self.context.get_display_datetime())})
        self.sax_metadata()
        node = self.context.content.documentElement.getDOMObj()
        self.sax_node(node)
        self.endElement('content')


class PlainAgendaItemProducer(producers.SilvaVersionedContentProducer):
    """Export an AgendaItem object to XML.
    """
    grok.adapts(interfaces.IAgendaItem, Interface)

    def sax(self):
        """sax"""
        self.startElementNS(NS_SILVA_NEWS,
                            'plainagendaitem',
                            {'id': self.context.id})
        self.sax_workflow()
        self.sax_versions()
        self.endElementNS(NS_SILVA_NEWS,'plainagendaitem')


class PlainAgendaItemVersionProducer(DocumentVersionProducer):
    """Export a version of an AgendaItem object to XML.
    """
    grok.adapts(interfaces.IAgendaItemVersion, Interface)

    def sax(self):
        """sax"""
        self.startElement(
            'content',
            {'version_id': self.context.id,
             'subjects': ','.join(self.context.get_subjects()),
             'target_audiences': ','.join(self.context.get_target_audiences()),
             'display_datetime': iso_datetime(
                self.context.get_display_datetime())})
        self.sax_metadata()
        node = self.context.content.documentElement.getDOMObj()
        self.sax_node(node)
        self.endElement('content')



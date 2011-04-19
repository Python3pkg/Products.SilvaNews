# Copyright (c) 2002-2011 Infrae. All rights reserved.
# See also LICENSE.txt

from silva.core.interfaces import IPublication
from five import grok
from zope.interface import Interface

# reference management (will move somewhere else)
from zope.traversing.browser import absoluteURL
from silva.core.references.reference import ReferenceSet
from silva.core.references.reference import canonical_path

from Products.SilvaNews import interfaces
from Products.SilvaNews.datetimeutils import utc_datetime
from Products.Silva.silvaxml.xmlexport import (ExternalReferenceError,
    theXMLExporter, VersionedContentProducer, SilvaBaseProducer)
from silva.app.page.xmlexport import ContentLayoutProducerMixin


NS_SILVA_NEWS = 'http://infrae.com/namespace/silva-news-network'
theXMLExporter.registerNamespace('silvanews', NS_SILVA_NEWS)

def iso_datetime(dt):
    if dt:
        string = utc_datetime(dt).replace(microsecond=0).isoformat()
        if string.endswith('+00:00'):
            string = string[:-6] + 'Z'
        return string
    return ''


class ReferenceSupportExporter(object):

    def reference_set_paths(self, name):
        ref_set = ReferenceSet(self.context, name)
        settings = self.getSettings()
        root = settings.getExportRoot()
        for reference in ref_set.get_references():
            if not settings.externalRendering():
                if not reference.target_id:
                    # The reference is broken. Return an empty path.
                    yield ""
                if not reference.is_target_inside_container(root):
                    raise ExternalReferenceError(
                        self.context, reference.target, root)
                # Add root path id as it is always mentioned in exports
                relative_path = [root.getId()] + \
                    reference.relative_path_to(root)
                yield canonical_path('/'.join(relative_path))
            else:
                # Return url to the target
                yield absoluteURL(reference.target, settings.request)


class NewsPublicationProducer(SilvaBaseProducer):
    """Export a News Publication object to XML.
    """
    grok.adapts(interfaces.INewsPublication, Interface)

    def sax(self):
        self.startElementNS(NS_SILVA_NEWS,
                            'newspublication', {'id': self.context.id})
        self.metadata()
        self.startElement('content')
        default = self.context.get_default()
        if default is not None:
            self.startElement('default')
            self.subsax(default)
            self.endElement('default')
        for object in self.context.get_ordered_publishables():
            if (IPublication.providedBy(object) and
                    not self.getSettings().withSubPublications()):
                continue
            self.subsax(object)
        for object in self.context.get_assets():
            self.subsax(object)
        if self.getSettings().otherContent():
            for object in self.context.get_other_content():
                self.subsax(object)
        self.endElement('content')
        self.endElementNS(NS_SILVA_NEWS,'newspublication')


class RSSAggregatorProducer(SilvaBaseProducer):
     """Export a RSSAggregator object to XML.
     """
     grok.adapts(interfaces.IAggregator, Interface)

     def sax(self):
         self.startElementNS(
             NS_SILVA_NEWS,
             'rssaggregator',
             {'id': self.context.id,
              'feed_urls': ','.join(self.context.get_feeds())
              })
         self.metadata()
         self.endElementNS(NS_SILVA_NEWS,'rssaggregator')


class CategoryFilterProducer(SilvaBaseProducer):
     """Export a CategoryFilter object to XML."""
     grok.adapts(interfaces.ICategoryFilter, Interface)

     def sax(self):
         self.startElementNS(
             NS_SILVA_NEWS,
             'categoryfilter',
             {'id': self.context.id,
              'target_audiences': ','.join(self.context.target_audiences()),
              'subjects': ','.join(self.context.subjects()),
              })
         self.metadata()
         self.endElementNS(NS_SILVA_NEWS,'categoryfilter')


class NewsFilterProducer(SilvaBaseProducer, ReferenceSupportExporter):
    """Export a NewsFilter object to XML.
    """
    grok.adapts(interfaces.INewsFilter, Interface)

    def sax(self):
        self.startElementNS(
            NS_SILVA_NEWS,
            'newsfilter',
            {'id': self.context.id,
             'target_audiences': ','.join(self.context.target_audiences()),
             'subjects': ','.join(self.context.subjects()),
             'show_agenda_items': str(self.context.show_agenda_items()),
             'keep_to_path': str(self.context.keep_to_path()),
             'excluded_items': ','.join(self.context.excluded_items())})
        self.sources()
        self.metadata()
        self.endElementNS(NS_SILVA_NEWS,'newsfilter')

    def sources(self):
        self.startElementNS(NS_SILVA_NEWS, "sources")
        for source_path in self.reference_set_paths("sources"):
            if source_path:
                self.startElementNS(
                    NS_SILVA_NEWS, 'source', {'target': source_path})
                self.endElementNS(NS_SILVA_NEWS, 'source')
        self.endElementNS(NS_SILVA_NEWS, "sources")


class AgendaFilterProducer(NewsFilterProducer):
    """Export a AgendaFilter object to XML.
    """
    grok.adapts(interfaces.IAgendaFilter, Interface)

    def sax(self):
        self.startElementNS(
            NS_SILVA_NEWS,
            'agendafilter',
            {'id': self.context.id,
             'target_audiences': ','.join(self.context.target_audiences()),
             'subjects': ','.join(self.context.subjects()),
             'keep_to_path': str(self.context.keep_to_path()),
             'excluded_items': ','.join(self.context.excluded_items())})
        self.sources()
        self.metadata()
        self.endElementNS(NS_SILVA_NEWS,'agendafilter')


class NewsViewerProducer(SilvaBaseProducer, ReferenceSupportExporter):
    """Export a NewsViewer object to XML.
    """
    grok.adapts(interfaces.INewsViewer, Interface)

    def sax(self):
        self.startElementNS(
            NS_SILVA_NEWS,
            'newsviewer',
            {'id': self.context.id,
             'number_to_show': str(self.context.number_to_show()),
             'number_to_show_archive': str(
                    self.context.number_to_show_archive()),
             'number_is_days': str(self.context.number_is_days()),
             'year_range': str(self.context.year_range())})
        self.filters()
        self.metadata()
        self.endElementNS(NS_SILVA_NEWS,'newsviewer')

    def filters(self):
        self.startElementNS(NS_SILVA_NEWS, "filters")
        for filter_path in self.reference_set_paths("filters"):
            if filter_path:
                self.startElementNS(
                    NS_SILVA_NEWS, 'filter', {'target': filter_path})
                self.endElementNS(NS_SILVA_NEWS, 'filter')
        self.endElementNS(NS_SILVA_NEWS, "filters")


class AgendaViewerProducer(NewsViewerProducer):
     """Export a AgendaViewer object to XML."""
     grok.adapts(interfaces.IAgendaViewer, Interface)

     def sax(self):
        self.startElementNS(
            NS_SILVA_NEWS,
            'agendaviewer',
            {'id': self.context.id,
             'days_to_show': str(self.context.days_to_show()),
             'number_to_show_archive': str(
                    self.context.number_to_show_archive()),
             'starting_date': iso_datetime(self.get_starting_date())})
        self.filters()
        self.metadata()
        self.endElementNS(NS_SILVA_NEWS,'agendaviewer')


class PlainArticleProducer(VersionedContentProducer):
    """Export a PlainArticle object to XML.
    """
    grok.adapts(interfaces.INewsItem, Interface)

    def sax(self):
        """sax"""
        self.startElementNS(NS_SILVA_NEWS,
                            'plainarticle',
                            {'id': self.context.id})
        self.workflow()
        self.versions()
        self.endElementNS(NS_SILVA_NEWS,'plainarticle')


class PlainArticleVersionProducer(ContentLayoutProducerMixin,
                                  SilvaBaseProducer):
    """Export a version of a PlainArticle object to XML.
    """
    grok.adapts(interfaces.INewsItemVersion, Interface)

    def sax(self):
        """sax"""
        self.startElement(
            'content',
            {'version_id': self.context.id,
             'subjects': ','.join(self.context.subjects()),
             'target_audiences': ','.join(self.context.target_audiences()),
             'display_datetime': iso_datetime(
                self.context.display_datetime()),
             'external_link': self.context.get_external_link(),
             'link_method': self.context.get_link_method()
             })
        self.metadata()
        self.content_layout_xml()
        self.endElement('content')


class PlainAgendaItemProducer(VersionedContentProducer):
    """Export an AgendaItem object to XML.
    """
    grok.adapts(interfaces.IAgendaItem, Interface)

    def sax(self):
        """sax"""
        self.startElementNS(NS_SILVA_NEWS,
                            'plainagendaitem',
                            {'id': self.context.id})
        self.workflow()
        self.versions()
        self.endElementNS(NS_SILVA_NEWS,'plainagendaitem')


class PlainAgendaItemVersionProducer(ContentLayoutProducerMixin,
                                     SilvaBaseProducer):
    """Export a version of an AgendaItem object to XML.
    """
    grok.adapts(interfaces.IAgendaItemVersion, Interface)

    def sax(self):
        """sax"""
        self.startElement(
            'content',
            {'version_id': self.context.id,
             'subjects': ','.join(self.context.subjects()),
             'target_audiences': ','.join(self.context.target_audiences()),
             'start_datetime': iso_datetime(self.context.get_start_datetime()),
             'end_datetime': iso_datetime(self.context.get_end_datetime()),
             'location': self.context.get_location(),
             'recurrence': self.context.get_recurrence() or '',
             'all_day': str(self.context.is_all_day()),
             'timezone_name': self.context.get_timezone_name(),
             'display_datetime': iso_datetime(
                self.context.display_datetime())})
        self.metadata()
        self.content_layout_xml()
        self.endElement('content')



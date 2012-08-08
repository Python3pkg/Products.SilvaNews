
import logging

from silva.app.news.interfaces import INewsPublication, INewsItemFilter
from silva.core.upgrade.upgrade import BaseUpgrader, content_path
from Products.ParsedXML.ParsedXML import ParsedXML
from Products.SilvaNews.interfaces import INewsItem
from Products.SilvaDocument.upgrader.upgrade_230 import DocumentUpgrader

from zExceptions import NotFound

logger = logging.getLogger('silva.core.upgrade')


VERSION_B1='2.3b1'
VERSION_B2='2.3b2'
VERSION_FINAL='2.3'


class ArticleUpgrader(BaseUpgrader):

    def validate(self, doc):
        return INewsItem.providedBy(doc)

    def upgrade(self, doc):
        # The 3.0 upgrader only upgrade the published, working and
        # last closed version. Only apply this upgrader on thoses.
        for version_id in [doc.get_public_version(),
                           doc.get_unapproved_version(),
                           doc.get_last_closed_version()]:
            if version_id is None:
                continue
            version = doc._getOb(version_id, None)
            if version is None:
                continue
            if not isinstance(version.content, ParsedXML):
                logger.info(
                    u'Upgrade xmlattribute for %s.', content_path(version))
                parsed_xml = version.content._content
                version.content = parsed_xml
        return doc


article_upgrader_agenda = ArticleUpgrader(
    VERSION_B1, ['Obsolete Agenda Item', 'Obsolete Article'], -50)
document_upgrader_agenda = DocumentUpgrader(
    VERSION_B1, ['Obsolete Agenda Item', 'Obsolete Article'], 50)


class NewsAgendaItemVersionCleanup(BaseUpgrader):

    def validate(self, content):
        if hasattr(content, '_calendar_date_representation'):
            return True
        return False

    def upgrade(self, content):
        del content._calendar_date_representation
        return content


class NewsAgendaItemRecurrenceUpgrade(BaseUpgrader):

    def validate(self, content):
        return not hasattr(content, '_recurrence')

    def upgrade(self, content):
        content._end_recurrence_datetime = None
        content._recurrence = None
        return content


agenda_item_upgrader = NewsAgendaItemVersionCleanup(
    VERSION_B2, 'Obsolete Agenda Item Version')
agenda_item_recurrence_upgrader = NewsAgendaItemRecurrenceUpgrade(
    VERSION_B2, 'Obsolete Agenda Item Version')


class NewsFilterUpgrader(BaseUpgrader):

    def validate(self, content):
        return '_sources' in content.__dict__

    def upgrade(self, content):
        logger.info(u"Upgrade News Filter %s.", content_path(content))
        root = content.get_root()
        for source in content._sources:
            try:
                target = root.unrestrictedTraverse(source)
            except (AttributeError, KeyError, NotFound, TypeError):
                logger.error(
                    u'Could not find content %s for News Filter %s.',
                    source,
                    content_path(content))
                continue
            if INewsPublication.providedBy(target):
                content.add_source(target)
            else:
                logger.error(
                    u'Content type %s is not an allowed source for %s.',
                    content_path(target), content_path(content))
        del content._sources
        return content


class NewsViewerUpgrader(BaseUpgrader):

    def validate(self, content):
        return '_filters' in content.__dict__

    def upgrade(self, content):
        logger.info(u"Upgrade News Viewer %s.", content_path(content))
        root = content.get_root()
        for flt in content._filters:
            try:
                target = root.unrestrictedTraverse(flt)
            except (AttributeError, KeyError, NotFound, TypeError):
                logger.error(
                    u'Could not find content %s for News Viewer %s.',
                    flt, content_path(content))
                continue
            if INewsItemFilter.providedBy(target):
                content.add_filter(target)
            else:
                logger.error(
                    u'Content type %s is not an allowed filter for %s.',
                    content_path(target), content_path(content))
        del content._filters
        return content


filter_upgrader = NewsFilterUpgrader(
    VERSION_FINAL, ['Silva News Filter', 'Silva Agenda Filter'])
viewer_upgrader = NewsViewerUpgrader(
    VERSION_FINAL, ['Silva News Viewer', 'Silva Agenda Viewer'])

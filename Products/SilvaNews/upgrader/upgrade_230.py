
import logging

from silva.core.upgrade.upgrade import BaseUpgrader, content_path
from Products.ParsedXML.ParsedXML import ParsedXML
from Products.SilvaNews.interfaces import INewsItem
from Products.SilvaDocument.upgrader.upgrade_230 import DocumentUpgrader

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
                    u'upgrade xmlattribute for %s.', content_path(version))
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
        return hasattr(content, '_sources')

    def upgrade(self, content):
        root = content.get_root()
        allowed = content.get_allowed_types()
        for source in content._sources:
            try:
                target = root.unrestrictedTraverse(source)
            except StandardError as e:
                logger.error('could not find object %s : %s' % (source, e))
                continue
            if target.meta_type in allowed:
                content.add_source(target)
            else:
                logger.warn('content type %s is not an allowed source' %
                    target.meta_type)
        del content._sources
        return content


class NewsViewerUpgrader(BaseUpgrader):

    def validate(self, content):
        return hasattr(content, '_filters')

    def upgrade(self, content):
        root = content.get_root()
        for flt in content._filters:
            try:
                target = root.unrestrictedTraverse(flt)
            except StandardError as e:
                logger.error('could not find object %s : %s' % (flt, e))
                continue
            content.add_filter(target)
        del content._filters
        return content


filter_upgrader = NewsFilterUpgrader(
    VERSION_FINAL, ['Silva News Filter', 'Silva Agenda Filter'])
viewer_upgrader = NewsViewerUpgrader(
    VERSION_FINAL, ['Silva News Viewer', 'Silva Agenda Viewer'])

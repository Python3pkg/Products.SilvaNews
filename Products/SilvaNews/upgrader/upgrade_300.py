
from silva.core.upgrade.upgrader.upgrade_300 import VERSION_A1
from silva.core.upgrade.upgrade import BaseUpgrader
from Products.SilvaDocument.upgrader.upgrade_300 import DocumentUpgrader


class CatalogUpgrader(BaseUpgrader):

    def validate(self, root):
        return bool(root.service_catalog)

    def upgrade(self, root):
        catalog = root.service_catalog

        columns = ['get_end_datetime','get_start_datetime',
            'get_location','get_title', 'display_datetime',
            'get_intro', 'sort_index']

        indexes = ['idx_end_datetime', 'idx_display_datetime',
            'idx_parent_path', 'idx_start_datetime', 'idx_target_audiences',
            'idx_timestamp_ranges', 'idx_subjects', 'idx_is_private']

        existing_columns = catalog.schema()
        existing_indexes = catalog.indexes()

        for column_name in columns:
            if column_name in existing_columns:
                catalog.delColumn(column_name)

        for field_name in indexes:
            if field_name in existing_indexes:
                catalog.delIndex(field_name)

        return root


class RootUpgrader(BaseUpgrader):

    def upgrade(self, root):
        extensions = root.service_extensions
        # If Silva News is installed, we need to refresh it, and
        # install silva.app.news for the migration.
        if extensions.is_installed('SilvaNews'):
            extensions.refresh('SilvaNews')
            if not extensions.is_installed('silva.app.news'):
                extensions.install('silva.app.news')
        return root


class NewsItemUpgrader(DocumentUpgrader):

    def create_document(self, parent, identifier, title):
        factory = parent.manage_addProduct['silva.app.news']
        factory.manage_addNewsItem(identifier, title)

    def copy_version(self, source, target, ensure=False):
        super(NewsItemUpgrader, self).copy_version(source, target, ensure)
        target._subjects = set(source._subjects)
        target._target_audiences = set(source._target_audiences)
        target._display_datetime = source._display_datetime
        target._external_url = source._external_url


class AgendaItemUpgrader(DocumentUpgrader):

    def create_document(self, parent, identifier, title):
        factory = parent.manage_addProduct['silva.app.news']
        factory.manage_addAgendaItem(identifier, title)

    def copy_version(self, source, target, ensure=False):
        super(AgendaItemUpgrader, self).copy_version(source, target, ensure)
        target._subjects = source._subjects
        target._target_audiences = source._target_audiences
        target._display_datetime = source._display_datetime
        target._external_url = source._external_url
        target._occurrences = list( source._occurrences)


class FilterUpgrader(BaseUpgrader):

    def available(self, content):
        return isinstance(content._excluded_items, list)

    def upgrade(self, content):
        content._excluded_items = set(content._excluded_items)
        return content


upgrade_catalog = CatalogUpgrader(
    VERSION_A1, "Silva Root")
upgrade_root = RootUpgrader(
    VERSION_A1, "Silva Root")
upgrade_newsitem = NewsItemUpgrader(
    VERSION_A1, "Obsolete Article")
upgrade_agendaitem = AgendaItemUpgrader(
    VERSION_A1, "Obsolete Agenda Item")
upgrade_filter = FilterUpgrader(
    VERSION_A1, ("Silva Agenda Filter", "Silva News Filter"))
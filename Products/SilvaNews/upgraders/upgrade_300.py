from silva.core.upgrade.upgrader.upgrade_300 import VERSION_A1
from silva.core.upgrade.upgrade import BaseUpgrader


class CatalogUpgrader(BaseUpgrader):

    def validate(self, root):
        return bool(root.service_catalog)

    def upgrade(self, root):
        catalog = root.service_catalog._catalog

        columns = ['get_end_datetime','get_start_datetime',
            'get_location','get_title', 'display_datetime',
            'get_intro', 'sort_index']

        indexes = ['idx_end_datetime', 'idx_display_datetime',
            'idx_parent_path', 'idx_start_datetime', 'idx_target_audiences',
            'idx_timestamp_ranges', 'idx_subjects']

        existing_columns = catalog.schema
        existing_indexes = catalog.indexes

        for column_name in columns:
            if column_name in existing_columns:
                catalog.delColumn(column_name)

        for field_name in indexes:
            if field_name in existing_indexes:
                catalog.delIndex(field_name)

        return root


class SilvaNewsRootUpgrader(BaseUpgrader):

    def upgrade(self, root):
        return root



upgrade_catalog = CatalogUpgrader(VERSION_A1, "Silva Root")
upgrade_root = SilvaNewsRootUpgrader(VERSION_A1, "Silva Root")


from os import path

from App.Common import package_home

from silva.core.conf.installer import DefaultInstaller

from Products.SilvaNews.interfaces import ISilvaNewsExtension


class SilvaNewsInstaller(DefaultInstaller):
    """Installer for the Silva News Service
    """
    not_globally_addables = ['Silva Article', 'Silva Agenda Item']

    def install_custom(self, root):
        self.setup_catalog(root)
        self.register_views(root.service_view_registry)
        self.configure_extra_metadata(root)

        if not hasattr(root.aq_explicit,'service_news'):
            factory = root.manage_addProduct['SilvaNews']
            factory.manage_addServiceNews('service_news')

    def uninstall_custom(self, root):
        self.unregister_views(root.service_view_registry)
        self.unconfigure_extra_metadata(root)

    def configure_extra_metadata(self, root):
        sm = root.service_metadata
        collection = sm.getCollection()
        if 'snn-np-settings' in collection.objectIds():
            collection.manage_delObjects(['snn-np-settings'])
        xml_file = path.join(package_home(globals()), 'snn-np-settings.xml')
        fh = open(xml_file, 'r')
        collection.importSet(fh)
        sm.addTypeMapping('Silva News Publication', ['snn-np-settings'])
        sm.addTypeMapping('Silva News ICS Publication', ['snn-np-settings'])
        sm.initializeMetadata()

    def unconfigure_extra_metadata(self, root):
        sm = root.service_metadata
        collection = sm.getCollection()
        if 'snn-np-settings' in collection.objectIds():
            collection.manage_delObjects(['snn-np-settings'])
        sm.removeTypeMapping('Silva News Publication',['snn-np-settings'])
        sm.removeTypeMapping('Silva News ICS Publication',['snn-np-settings'])

    def register_views(self, reg):
        """Register core views on registry.
        """
        ## edit
        reg.register('edit',
                     'Silva Agenda Filter', ['edit', 'Asset', 'Filter', 'AgendaFilter'])
        reg.register('edit',
                     'Silva News Filter', ['edit', 'Asset', 'Filter', 'NewsFilter'])
        reg.register('edit',
                     'Silva News Publication', ['edit', 'Container', 'Publication', 'NewsPublication'])
        reg.register('edit',
                     'Silva Article', ['edit', 'VersionedContent', 'NewsItem', 'PlainArticle'])
        reg.register('edit',
                     'Silva Agenda Item', ['edit', 'VersionedContent', 'NewsItem', 'PlainAgendaItem'])
        reg.register('edit',
        'Silva News Category Filter', ['edit', 'Asset', 'Filter', 'CategoryFilter'])

        # public
        reg.register('public', 'Silva Agenda Filter', ['public', 'AgendaFilter'])
        reg.register('public',
                     'Silva News Filter', ['public', 'NewsFilter'])
        reg.register('public', 'Silva News Publication', ['public', 'NewsPublication'])

        ## preview - required for e.g. the compare versions feature
        reg.register('preview', 'Silva News Filter', ['public', 'NewsFilter'])
        reg.register('preview', 'Silva Agenda Filter', ['public', 'AgendaFilter'])
        reg.register('preview', 'Silva News Publication', ['public', 'NewsPublication'])

    def unregister_views(self, reg):
        #"""Unregister core views on registry.
        #"""
        ## edit
        reg.unregister('edit', 'Silva Agenda Filter')
        reg.unregister('edit', 'Silva News Filter')
        reg.unregister('edit', 'Silva News Publication')
        reg.unregister('edit', 'Silva News Viewer')
        reg.unregister('edit', 'Silva Agenda Viewer')
        reg.unregister('edit', 'Silva Article')
        reg.unregister('edit', 'Silva Agenda Item')
        reg.unregister('edit', 'Silva News Category Filter')
        ## public
        reg.unregister('public', 'Silva Agenda Filter')
        reg.unregister('public', 'Silva News Filter')
        reg.unregister('public', 'Silva News Publication')
        reg.unregister('public', 'Silva RSS Aggregator')
        reg.unregister('public', 'Silva Article Version')
        reg.unregister('public', 'Silva Agenda Item Version')
        ## preview
        reg.unregister('preview', 'Silva News Filter')
        reg.unregister('preview', 'Silva News Viewer')
        reg.unregister('preview', 'Silva News Publication')
        reg.unregister('preview', 'Silva Agenda Filter')
        reg.unregister('preview', 'Silva Agenda Viewer')
        reg.unregister('preview', 'Silva RSS Aggregator')
        reg.unregister('preview', 'Silva Article Version')
        reg.unregister('preview', 'Silva Agenda Item Version')

    def setup_catalog(self, root):
        """Sets the ZCatalog up"""
        catalog = root.service_catalog

        columns = ['object_path', 'get_title', 'display_datetime',
                   'get_intro', 'sort_index']

        indexes = [
            ('object_path', 'FieldIndex'),
            ('idx_parent_path', 'FieldIndex'),
            ('idx_display_datetime', 'DateIndex'),
            ('idx_timestamp_ranges', 'IntegerRangesIndex'),
            ('idx_subjects', 'KeywordIndex'),
            ('idx_target_audiences', 'KeywordIndex'),
            ]

        existing_columns = catalog.schema()
        existing_indexes = catalog.indexes()

        for column_name in columns:
            if column_name in existing_columns:
                continue
            catalog.addColumn(column_name)

        for field_name, field_type in indexes:
            if field_name in existing_indexes:
                continue
            catalog.addIndex(field_name, field_type)

install = SilvaNewsInstaller("SilvaNews", ISilvaNewsExtension)

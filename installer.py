from os import path

from zope import interface
from zope.interface import Interface
from App.Common import package_home

from silva.core.conf.installer import DefaultInstaller
from silva.core.interfaces import IInvisibleService
from Products.Silva.roleinfo import AUTHOR_ROLES

from interfaces import ISilvaNewsExtension
from ServiceNews import manage_addServiceNews


class SilvaNewsInstaller(DefaultInstaller):
    """Installer for the Silva News Service"""
    
    def install(self, root):
        DefaultInstaller.install(self, root)
        # and add a service_news to the Silva root
        #if not hasattr(root, 'service_news'):
        #    root.manage_addProduct['SilvaNews'].manage_addServiceNews(
        #        'service_news', 'Silva News Network Service')
        self.setup_catalog(root)
        self.configure_security(root)
        self.register_views(root.service_view_registry)
        self.configure_addables(root)
        self.configure_metadata(root)
        
        # allowed_addables_in_publication
        self.configure_xml_widgets(root)

        if not hasattr(root.aq_explicit,'service_news'):
            manage_addServiceNews(root, 'service_news', 'Silva News Network Service')
        
    def uninstall(self, root):
        DefaultInstaller.uninstall(self, root)
        self.unregister_views(root.service_view_registry)
        self.unconfigure_xml_widgets(root)
        self.unconfigure_metadata(root)
        
    def unconfigure_metadata(self, root):
        sm = root.service_metadata
        collection = sm.getCollection()
        if 'snn-np-settings' in collection.objectIds():
            collection.manage_delObjects(['snn-np-settings'])
        sm.removeTypeMapping('Silva News Publication',['snn-np-settings'])
    
    def configure_metadata(self, root):
        sm = root.service_metadata
        collection = sm.getCollection()
        if 'snn-np-settings' in collection.objectIds():
            collection.manage_delObjects(['snn-np-settings'])
        xml_file = path.join(package_home(globals()), 'snn-np-settings.xml')
        fh = open(xml_file, 'r')
        collection.importSet(fh)
        sm.addTypeMapping('Silva News Publication', ['snn-np-settings'])
        sm.initializeMetadata()
        
    def configure_addables(self, root):
        news_non_addables = ['Silva Article', 
                            'Silva Agenda Item',
                            ]
        current_addables = root.get_silva_addables_allowed_in_container()
        new_addables = []
        for a in current_addables:
            if a not in news_non_addables:
                new_addables.append(a)
        root.set_silva_addables_allowed_in_container(new_addables)
        
        
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
                     'Silva News Viewer', ['edit', 'Content', 'NewsViewer'])
        reg.register('edit',
                     'Silva RSS Aggregator', ['edit', 'Content', 'RSSAggregator'])
        reg.register('edit',
                     'Silva Agenda Viewer', ['edit', 'Content', 'AgendaViewer'])
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
        reg.register('public', 'Silva News Viewer', ['public', 'NewsViewer'])
        reg.register('public', 'Silva RSS Aggregator', ['public', 'RSSAggregator'])
        reg.register('public', 'Silva Agenda Viewer', ['public', 'AgendaViewer'])
        reg.register('public', 'Silva Article Version', ['public', 'PlainArticle'])
        reg.register('public', 'Silva Agenda Item Version', ['public', 'PlainAgendaItem'])
    
        ## preview - required for e.g. the compare versions feature
        reg.register('preview', 'Silva News Viewer', ['public', 'NewsViewer'])
        reg.register('preview', 'Silva News Filter', ['public', 'NewsFilter'])
        reg.register('preview', 'Silva Agenda Viewer', ['public', 'AgendaViewer'])
        reg.register('preview', 'Silva Agenda Filter', ['public', 'AgendaFilter'])
        reg.register('preview', 'Silva News Publication', ['public', 'NewsPublication'])
        reg.register('preview', 'Silva RSS Aggregator', ['public', 'RSSAggregator'])
        reg.register('preview', 'Silva Article Version', ['public', 'PlainArticle'])
        reg.register('preview', 'Silva Agenda Item Version', ['public', 
                                                            'PlainAgendaItem'])

        # add
        reg.register('add', 'Silva Agenda Filter', ['add', 'AgendaFilter'])
        reg.register('add', 'Silva News Filter', ['add', 'NewsFilter'])
        reg.register('add', 'Silva News Publication', ['add', 'NewsPublication'])
        reg.register('add', 'Silva News Viewer', ['add', 'NewsViewer'])
        reg.register('add', 'Silva RSS Aggregator', ['add', 'RSSAggregator'])
        reg.register('add', 'Silva Agenda Viewer', ['add', 'AgendaViewer'])
        reg.register('add', 'Silva Article', ['add', 'NewsItem', 'PlainArticle'])
        reg.register('add', 'Silva Agenda Item', ['add', 'NewsItem', 'PlainAgendaItem'])
        reg.register('add', 'Silva News Category Filter', ['add', 'CategoryFilter'])

    def unregister_views(self, reg):
        #"""Unregister core views on registry.
        #"""
        ## edit
        reg.unregister('edit', 'Silva Agenda Filter')
        reg.unregister('edit', 'Silva News Filter')
        reg.unregister('edit', 'Silva News Publication')
        reg.unregister('edit', 'Silva News Viewer')
        reg.unregister('edit', 'Silva RSS Aggregator')
        reg.unregister('edit', 'Silva Agenda Viewer')
        reg.unregister('edit', 'Silva Article')
        reg.unregister('edit', 'Silva Agenda Item')
        reg.unregister('edit', 'Silva News Category Filter')
        ## public
        reg.unregister('public', 'Silva Agenda Filter')
        reg.unregister('public', 'Silva News Filter')
        reg.unregister('public', 'Silva News Publication')
        reg.unregister('public', 'Silva News Viewer')
        reg.unregister('public', 'Silva RSS Aggregator')
        reg.unregister('public', 'Silva Agenda Viewer')
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

        # add
        reg.unregister('add', 'Silva Agenda Filter')
        reg.unregister('add', 'Silva News Filter')
        reg.unregister('add', 'Silva News Publication')
        reg.unregister('add', 'Silva News Viewer')
        reg.unregister('add', 'Silva RSS Aggregator')
        reg.unregister('add', 'Silva Agenda Viewer')
        reg.unregister('add', 'Silva Article')
        reg.unregister('add', 'Silva Agenda Item')
        reg.unregister('add', 'Silva News Category Filter')
    
    def setup_catalog(self, root):
        """Sets the ZCatalog up"""
        catalog = root.service_catalog
    
        #object_path is the Content Object path (parent)
        #of Version objects (e.g. PlainNewsArticleVersion).
        columns = ['object_path','end_datetime','start_datetime','location','get_title', 'display_datetime','get_intro']
        #will need to add: external_link, link_method
        #                  subjects, target_audiences, teaser
        # , formatEventSummary (need to determine how to integrate "my"
        #     event intro and get_intro
    
        indexes = [
            ('object_path', 'FieldIndex'),
            ('idx_parent_path', 'FieldIndex'),
            ('idx_start_datetime', 'DateIndex'),
            ('idx_end_datetime', 'DateIndex'),
            ('idx_display_datetime', 'DateIndex'),
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
            if field_type == 'ZCTextIndex':
                extra = RecordStyle(
                    {'doc_attr':field_name,
                     'lexicon_id':'silva_lexicon',
                     'index_type':'Okapi BM25 Rank'}
                    )
                catalog.addIndex(field_name, field_type, extra)
            else:
                catalog.addIndex(field_name, field_type)
    
    def configure_security(self, root):
        add_permissions = [
            'Add Silva Agenda Filters',
            'Add Silva Agenda Item Versions',
            'Add Silva Agenda Items',
            'Add Silva Agenda Viewers',
            'Add Silva Article Versions',
            'Add Silva Articles',
            'Add Silva News Filters',
            'Add Silva News Publications',
            'Add Silva News Viewers',
            'Add Silva RSS Aggregators',
            'Add Silva News Category Filters',
            ]
        p_perms = root.possible_permissions()
        for perm in add_permissions:
            if perm in p_perms:
                root.manage_permission(perm, AUTHOR_ROLES)
                
    def configure_xml_widgets(self, root):
        """Configure XMLWidgets registries, editor, etc'
        """
        # create the services for XMLWidgets
        for name in ['service_news_sub_viewer']:
            if not hasattr(root, name):
                root.manage_addProduct['XMLWidgets'].manage_addWidgetRegistry(name)
    
        if IInvisibleService is not None:
                interface.directlyProvides(
                    root['service_news_sub_viewer'],
                    IInvisibleService,
                    *interface.directlyProvidedBy(root['service_news_sub_viewer']))
    
        # now register all widgets
        self.registerNewsSubViewer(root)

    def unconfigure_xml_widgets(self,root):
        if hasattr(root.aq_explicit, 'service_news_sub_viewer'):
            root.manage_delObjects(['service_news_sub_viewer'])
        if hasattr(root.aq_explicit, 'service_news_sub_editor'):
            root.manage_delObjects(['service_news_sub_editor'])

    def registerNewsSubViewer(self,root):
        wr = root.service_news_sub_viewer
        wr.clearWidgets()
    
        wr.addWidget('doc', ('service_widgets', 'top', 'field', 'mode_view'))
    
        for name in ['p', 'list', 'heading', 'pre', 'toc', 'image',
                     'nlist', 'table', 'dlist', 'source', 'cite']:
            wr.addWidget(
                name,
                ('service_widgets', 'element', 'doc_elements', name, 'mode_view'))

        
install = SilvaNewsInstaller("SilvaNews", ISilvaNewsExtension)

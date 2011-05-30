# Copyright (c) 2002-2011 Infrae. All rights reserved.
# See also LICENSE.txt
# $Id$

from Products.Silva.testing import SilvaLayer
from DateTime import DateTime
import transaction
import Products.SilvaNews
import unittest


class SilvaNewsLayer(SilvaLayer):

    default_products = SilvaLayer.default_products + ['SilvaNews',]

    def _install_application(self, app):
        super(SilvaNewsLayer, self)._install_application(app)
        app.root.service_extensions.install("silva.core.contentlayout")
        app.root.service_extensions.install('SilvaNews')
        app.root.service_news.set_timezone_name('Europe/Amsterdam')
        transaction.commit()


FunctionalLayer = SilvaNewsLayer(
    Products.SilvaNews, zcml_file='configure.zcml')

class SilvaNewsTestCase(unittest.TestCase):

    layer = FunctionalLayer

    def setUp(self):
        self.root = self.layer.get_application()
        self.layer.login('manager')
        self.service_news = self.root.service_news
        self.service_news.add_subject('sub', 'Subject')
        self.service_news.add_target_audience('ta', 'TA')
        self.catalog = self.root.service_catalog

    def add_news_publication(self, parent, id, title, **kw):
        factory = parent.manage_addProduct['SilvaNews']
        factory.manage_addNewsPublication(id, title, **kw)
        return getattr(parent, id)

    def add_plain_article(self, parent, id, title, **kw):
        factory = parent.manage_addProduct['SilvaNews']
        factory.manage_addPlainArticle(id, title, **kw)
        return getattr(parent, id)

    def add_news_viewer(self, parent, id, title, **kw):
        factory = parent.manage_addProduct['SilvaNews']
        factory.manage_addNewsViewer(id, title, **kw)
        return getattr(parent, id)

    def add_agenda_viewer(self, parent, id, title, **kw):
        factory = parent.manage_addProduct['SilvaNews']
        factory.manage_addAgendaViewer(id, title, **kw)
        return getattr(parent, id)

    def add_news_filter(self, parent, id, title, **kw):
        factory = parent.manage_addProduct['SilvaNews']
        factory.manage_addNewsFilter(id, title, **kw)
        return getattr(parent, id)

    def add_agenda_filter(self, parent, id, title, **kw):
        factory = parent.manage_addProduct['SilvaNews']
        factory.manage_addAgendaFilter(id, title, **kw)
        return getattr(parent, id)

    def add_published_news_item(self, parent, id, title, **kw):
        factory = parent.manage_addProduct['SilvaNews']
        factory.manage_addPlainArticle(id, title, **kw)
        item = getattr(parent, id)
        version = item.get_editable()
        version.set_subjects(['sub'])
        version.set_target_audiences(['ta'])
        version.set_display_datetime(DateTime())
        item.set_next_version_publication_datetime(DateTime())
        item.approve_version()
        item._update_publication_status()
        return item

    def add_published_agenda_item(self, parent, id, title, sdt, edt=None, **kw):
        factory = parent.manage_addProduct['SilvaNews']
        factory.manage_addPlainAgendaItem(id, title, **kw)
        item = getattr(parent, id)
        ver = item.get_editable()
        ver.set_start_datetime(sdt)
        if edt:
            ver.set_end_datetime(edt)
        ver.set_subjects(['sub'])
        ver.set_target_audiences(['ta'])
        ver.set_display_datetime(DateTime())
        item.set_next_version_publication_datetime(DateTime())
        item.approve_version()
        item._update_publication_status()
        return getattr(parent, id)


class NewsBaseTestCase(SilvaNewsTestCase):
    def setUp(self):
        super(NewsBaseTestCase, self).setUp()
        self.sm = self.root.service_metadata
        service_news = self.service_news = self.root.service_news
        service_news.add_subject('sub2', 'Subject 2')
        service_news.add_target_audience('ta2', 'TA 2')

        self.source1 = self.add_news_publication(
            self.root, 'source1', 'News Pub 1')
        self.item1_1 = self.add_plain_article(
            self.source1, 'art1', 'Article 1')
        self.item1_1.set_next_version_publication_datetime(DateTime())
        getattr(self.item1_1, '0').set_subjects(['sub'])
        getattr(self.item1_1, '0').set_target_audiences(['ta'])
        self.item1_1.approve_version()
        self.item1_1._update_publication_status()
        getattr(self.item1_1, '0').set_display_datetime(DateTime())

        self.item1_2 = self.add_plain_article(
            self.source1, 'art2', 'Article 2')
        self.item1_2.set_next_version_publication_datetime(DateTime())
        getattr(self.item1_2, '0').set_subjects(['sub2'])
        getattr(self.item1_2, '0').set_target_audiences(['ta2'])
        self.item1_2.approve_version()
        self.item1_2._update_publication_status()
        getattr(self.item1_2, '0').set_display_datetime(DateTime())

        self.source2 = self.add_news_publication(
            self.root, 'source2', 'News Pub 2')
        binding = self.sm.getMetadata(self.source2)
        binding.setValues('snn-np-settings',{'is_private':'yes'},reindex=1)

        factory = self.root.manage_addProduct['Silva']
        factory.manage_addFolder('somefolder', 'Some Folder')
        self.folder = getattr(self.root, 'somefolder')
        self.source3 = self.add_news_publication(
            self.folder, 'source3', 'Folder ')
        binding = self.sm.getMetadata(self.source3)
        binding.setValues('snn-np-settings',{'is_private':'yes'},reindex=1)

        self.item3_3 = self.add_plain_article(
            self.source3, 'art3', 'Article 3')
        self.item3_3.set_next_version_publication_datetime(DateTime())
        getattr(self.item3_3, '0').set_subjects(['sub'])
        getattr(self.item3_3, '0').set_target_audiences(['ta'])
        self.item3_3.approve_version()
        self.item3_3._update_publication_status()
        getattr(self.item3_3, '0').set_display_datetime(DateTime())

        self.newsfilter = self.add_news_filter(
            self.root, 'newsfilter', 'NewsFilter')
        self.newsfilter.set_subjects(['sub', 'sub2'])
        self.newsfilter.set_target_audiences(['ta', 'ta2'])
        self.newsfilter.add_source(self.source1)

        self.newsviewer = self.add_news_viewer(
            self.root, 'newsviewer', 'NewsViewer')
        self.newsviewer.add_filter(self.newsfilter)

        self.agendafilter = self.add_agenda_filter(
            self.root, 'agendafilter','agendafilter')
        self.agendafilter.set_subjects(['sub'])
        self.agendafilter.set_target_audiences(['ta'])
        self.agendafilter.set_sources([self.source1])
        
        self.agendaviewer = self.add_agenda_viewer(
            self.root, 'agendaviewer', 'AgendaViewer')
        self.agendaviewer.add_filter(self.agendafilter)
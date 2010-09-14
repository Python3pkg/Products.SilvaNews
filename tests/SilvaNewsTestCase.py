# Copyright (c) 2002-2008 Infrae. All rights reserved.
# See also LICENSE.txt
# $Id$

from Testing.ZopeTestCase import installProduct
installProduct('SilvaNews')

from Products.Silva.tests import SilvaTestCase
from DateTime import DateTime

class SilvaNewsTestCase(SilvaTestCase.SilvaTestCase):
    def afterSetUp(self):
        self.installExtension('SilvaNews')
        
    def add_news_publication(self, object, id, title, **kw):
        return self.addObject(object, 'NewsPublication', id, title=title, product='SilvaNews', **kw)

    def add_plain_article(self, object, id, title, **kw):
        return self.addObject(object, 'PlainArticle', id, title=title, product='SilvaNews', **kw)

    def add_plain_article(self, object, id, title, **kw):
        return self.addObject(object, 'PlainArticle', id, title=title, product='SilvaNews', **kw)

    def add_news_viewer(self, object, id, title, **kw):
        return self.addObject(object, 'NewsViewer', id, title=title, product='SilvaNews', **kw)

    def add_news_filter(self, object, id, title, **kw):
        return self.addObject(object, 'NewsFilter', id, title=title, product='SilvaNews', **kw)
    
    def add_agenda_filter(self, object, id, title, **kw):
        return self.addObject(object, 'AgendaFilter', id, title=title, product='SilvaNews', **kw)

    def add_published_agenda_item(self, object, id, title, sdt, edt, **kw):
        obj = self.addObject(object, 'PlainAgendaItem', id, title=title, product='SilvaNews', **kw)
        ver = obj.get_editable()
        ver.set_start_datetime(sdt)
        ver.set_end_datetime(edt)
        ver.set_subjects(['sub'])
        ver.set_target_audiences(['ta'])
        obj.set_next_version_publication_datetime(DateTime())
        obj.approve_version()
        obj._update_publication_status()
        ver.set_display_datetime(DateTime())

class NewsBaseTestCase(SilvaNewsTestCase):
    def afterSetUp(self):
        super(NewsBaseTestCase, self).afterSetUp()
        self.sm = self.root.service_metadata
        service_news = self.service_news = self.root.service_news
        service_news.add_subject('sub', 'Subject')
        service_news.add_subject('sub2', 'Subject 2')
        service_news.add_target_audience('ta', 'TA')
        service_news.add_target_audience('ta2', 'TA 2')

        self.source1 = self.add_news_publication(self.root, 'source1', 'News Pub 1')

        self.item1_1 = self.add_plain_article(self.source1, 'art1', 'Article 1')
        self.item1_1.set_next_version_publication_datetime(DateTime())
        getattr(self.item1_1, '0').set_subjects(['sub'])
        getattr(self.item1_1, '0').set_target_audiences(['ta'])
        self.item1_1.approve_version()
        self.item1_1._update_publication_status()
        getattr(self.item1_1, '0').set_display_datetime(DateTime())

        self.item1_2 = self.add_plain_article(self.source1, 'art2', 'Article 2')
        self.item1_2.set_next_version_publication_datetime(DateTime())
        getattr(self.item1_2, '0').set_subjects(['sub2'])
        getattr(self.item1_2, '0').set_target_audiences(['ta2'])
        self.item1_2.approve_version()
        self.item1_2._update_publication_status()
        getattr(self.item1_2, '0').set_display_datetime(DateTime())

        self.source2 = self.add_news_publication(self.root, 'source2', 'News Pub 2')
        binding = self.sm.getMetadata(self.source2)
        binding.setValues('snn-np-settings',{'is_private':'yes'},reindex=1)

        self.folder = self.add_folder(self.root, 'somefolder', 'Some Folder')
        self.source3 = self.add_news_publication(self.folder, 'source3', 'Folder ')
        binding = self.sm.getMetadata(self.source3)
        binding.setValues('snn-np-settings',{'is_private':'yes'},reindex=1)

        self.item3_3 = self.add_plain_article(self.source3, 'art3', 'Article 3')
        self.item3_3.set_next_version_publication_datetime(DateTime())
        getattr(self.item3_3, '0').set_subjects(['sub'])
        getattr(self.item3_3, '0').set_target_audiences(['ta'])
        self.item3_3.approve_version()
        self.item3_3._update_publication_status()
        getattr(self.item3_3, '0').set_display_datetime(DateTime())

        self.newsfilter = self.add_news_filter(self.root, 'newsfilter', 'NewsFilter')
        self.newsfilter.set_subjects(['sub', 'sub2'])
        self.newsfilter.set_target_audiences(['ta', 'ta2'])

        self.newsviewer = self.add_news_viewer(self.root, 'newsviewer', 'NewsViewer')
        self.newsviewer.set_filter('/root/newsfilter', 1)

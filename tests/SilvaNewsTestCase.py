# Copyright (c) 2002-2008 Infrae. All rights reserved.
# See also LICENSE.txt
# $Id$

from Testing import ZopeTestCase
from Products.Silva.tests import SilvaTestCase
from DateTime import DateTime

ZopeTestCase.installProduct('SilvaNews')


def add_helper(object, typename, id, title):
    getattr(object.manage_addProduct['Silva'], 'manage_add%s' % typename)(id, title)
    return getattr(object, id)

def add_helper_news(object, typename, id, title):
    getattr(object.manage_addProduct['SilvaNews'], 'manage_add%s' % typename)(id, title)
    return getattr(object, id)



class SilvaNewsTestCase(SilvaTestCase.SilvaTestCase):

    def afterSetUp(self):
        self.root.service_extensions.install('SilvaNews')



class NewsBaseTestCase(SilvaNewsTestCase):
    def afterSetUp(self):
        super(NewsBaseTestCase, self).afterSetUp()
        self.sroot = self.root
        service_news = self.service_news = self.sroot.service_news

        self.service_catalog = self.sroot.service_catalog
        
        self.source1 = add_helper_news(self.sroot, 'NewsPublication', 'source1', 'Folder 1')

        self.item1_1 = add_helper_news(self.source1, 'PlainArticle', 'art1', 'Article 1')
        self.item1_1.set_next_version_publication_datetime(DateTime())
        getattr(self.item1_1, '0').set_subjects(['test'])
        getattr(self.item1_1, '0').set_target_audiences(['test'])
        self.item1_1.approve_version()
        self.item1_1._update_publication_status()
        getattr(self.item1_1, '0').set_display_datetime(DateTime())

        self.item1_2 = add_helper_news(self.source1, 'PlainArticle', 'art2', 'Article 2')
        self.item1_2.set_next_version_publication_datetime(DateTime())
        getattr(self.item1_2, '0').set_subjects(['test2'])
        getattr(self.item1_2, '0').set_target_audiences(['test2'])
        self.item1_2.approve_version()
        self.item1_2._update_publication_status()
        getattr(self.item1_2, '0').set_display_datetime(DateTime())

        self.source2 = add_helper_news(self.sroot, 'NewsPublication', 'source2', 'Folder 2')
        self.source2.set_private(1)

        self.folder = add_helper(self.sroot, 'Folder', 'somefolder', 'Some Folder')
        self.source3 = add_helper_news(self.folder, 'NewsPublication', 'source3', 'Folder 3')
        self.source3.set_private(1)

        self.item1_3 = add_helper_news(self.source3, 'PlainArticle', 'art3', 'Article 3')
        self.item1_3.set_next_version_publication_datetime(DateTime())
        getattr(self.item1_3, '0').set_subjects(['test'])
        getattr(self.item1_3, '0').set_target_audiences(['test'])
        self.item1_3.approve_version()
        self.item1_3._update_publication_status()
        getattr(self.item1_3, '0').set_display_datetime(DateTime())

        self.newsfilter = add_helper_news(self.sroot, 'NewsFilter', 'newsfilter', 'NewsFilter')

        self.newsviewer = add_helper_news(self.newsfilter, 'NewsViewer', 'newsviewer', 'NewsViewer')

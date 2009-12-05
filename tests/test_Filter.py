# Copyright (c) 2002-2008 Infrae. All rights reserved.
# See also LICENSE.txt
# $Id$

from DateTime import DateTime

import SilvaNewsTestCase


class NewsFilterTestCase(SilvaNewsTestCase.NewsBaseTestCase):
    """Test the NewsFilter interface.
    """

    def afterSetUp(self):
        super(NewsFilterTestCase, self).afterSetUp()
        self.service_news.add_subject('test', 'Test')
        self.service_news.add_subject('test2', 'Test 2')
        self.service_news.add_target_audience('test', 'Test')
        self.service_news.add_target_audience('test2', 'Test 2')
    
    def test_find_sources(self):
        res = self.newsfilter.find_sources()
        self.assert_('source1' in [i.id for i in res])
        self.assert_('source2' in [i.id for i in res])
        self.assert_('source3' not in [i.id for i in res])
        self.assert_(len(res) == 2)

    def test_sources(self):
        self.assert_(self.newsfilter.sources() == [])
        self.newsfilter.add_source('/root/source1', 1)
        self.assert_(self.newsfilter.sources() == ['/root/source1'])
        self.newsfilter.add_source('/root/source2', 1)
        self.assert_('/root/source1' in self.newsfilter.sources())
        self.assert_('/root/source2' in self.newsfilter.sources())
        self.assert_(len(self.newsfilter.sources()) == 2)
        self.newsfilter.add_source('/root/banaan', 1)
        self.assert_('/root/banaan' not in self.newsfilter.sources())
        self.assert_(len(self.newsfilter.sources()) == 2)
        self.newsfilter.add_source('/root/somefolder/source3', 1)
        self.assert_('/root/somefolder/source3' not in self.newsfilter.sources())
        self.assert_(len(self.newsfilter.sources()) == 2)
        self.newsfilter.add_source('/root/source2', 0)
        self.assert_(self.newsfilter.sources() == ['/root/source1'])

    def test_items(self):
        self.newsfilter.set_subjects(['test'])
        self.newsfilter.set_target_audiences(['test'])
        self.newsfilter.add_source('/root/source1', 1)
        self.newsfilter.add_source('/root/somefolder/source3', 1)
        res = self.newsfilter.get_all_items()
        pps = ['/'.join(i.object_path) for i in res]
        self.assert_('/root/source1/art1' in pps)
        self.assert_(not '/root/source1/art2' in pps)
        self.assert_(not '/root/source1/somefolder/art3' in pps)
        self.assert_(len(pps) == 1)
        self.newsfilter.set_excluded_item(('', 'root', 'source1', 'art1'), 1)
        self.assert_(self.newsfilter.excluded_items() == [('', 'root', 'source1', 'art1')])
        self.assert_([i.object_path for i in self.newsfilter.get_last_items(10)] == [])

    def test_synchronize_with_service(self):
        self.newsfilter.set_subjects(['test'])
        self.newsfilter.synchronize_with_service()
        self.assert_(self.newsfilter.subjects() == ['test'])
        self.service_news.remove_subject('test')
        self.newsfilter.synchronize_with_service()
        self.assert_(self.newsfilter.subjects() == [])

    def test_search_items(self):
        self.newsfilter.set_subjects(['test'])
        self.newsfilter.set_target_audiences(['test'])
        self.newsfilter.add_source('/root/source1', 1)
        self.newsfilter.add_source('/root/source2', 1)
        self.newsfilter.add_source('/root/somefolder/source3', 1)
        res = ['%s - %s' % (i.id, i.object_path) for i in self.service_catalog({})]
        resids = [i.object_path[-1] for i in self.newsfilter.search_items('test')]
        self.assert_('art1' in resids)
        self.assert_('art2' not in resids)
        self.assert_('art3' not in resids)
        self.assert_(len(resids) == 1)

    def test_display_datetime(self):
        self.newsfilter.set_subjects(['test', 'test2'])
        self.newsfilter.set_target_audiences(['test', 'test2'])
        self.newsfilter.add_source('/root/source1', 1)
        self.newsfilter.add_source('/root/somefolder/source3', 1)
        items = self.newsfilter.get_last_items(2)
        itemids = [item.object_path[-1] for item in items]
        self.assertEquals(itemids, ['art1', 'art2'])
        # normal code would never set the display datetime on the viewable,
        # I guess
        self.item1_2.get_viewable().set_display_datetime(DateTime() + 1)
        items = self.newsfilter.get_last_items(2)
        itemids = [item.object_path[-1] for item in items]
        self.assertEquals(itemids, ['art2', 'art1'])

import unittest
def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(NewsFilterTestCase))
    return suite

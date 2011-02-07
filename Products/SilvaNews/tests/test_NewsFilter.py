# Copyright (c) 2002-2011 Infrae. All rights reserved.
# See also LICENSE.txt
# $Id$

from DateTime import DateTime
from Products.SilvaNews.tests import SilvaNewsTestCase

class NewsFilterTestCase(SilvaNewsTestCase.NewsBaseTestCase):
    """Test the NewsFilter interface.
    """
    def test_find_sources(self):
        res = self.newsfilter.get_all_sources()
        ids = [i.id for i in res]
        self.assertTrue('source1' in ids)
        self.assertTrue('source2' in ids)
        self.assertTrue('source3' not in ids)
        self.assertEquals(2, len(res))

    def test_sources(self):
        self.assertTrue(self.newsfilter.get_sources() == [self.source1])
        self.assert_(self.newsfilter.get_sources() == [self.source1])
        self.newsfilter.set_sources([self.source1, self.source2])
        self.assertTrue(self.source1 in self.newsfilter.get_sources())
        self.assertTrue(self.source2 in self.newsfilter.get_sources())
        self.assertEquals(2, len(self.newsfilter.get_sources()))
        parent = self.source2.aq_parent
        parent.manage_delObjects([self.source2.id])
        self.assertEquals(1, len(self.newsfilter.get_sources()))
        self.assertTrue(self.source2 not in self.newsfilter.get_sources())

    def test_items(self):
        self.newsfilter.set_subjects(['sub'])
        self.newsfilter.set_target_audiences(['ta'])
        self.newsfilter.set_sources([self.source1])
        res = self.newsfilter.get_all_items()
        pps = ['/'.join(i.object_path) for i in res]
        self.assertTrue('/root/source1/art1' in pps)
        self.assertTrue(not '/root/source1/art2' in pps)
        self.assertTrue(not '/root/source1/somefolder/art3' in pps)
        self.assertEquals(1, len(pps))
        self.newsfilter.set_excluded_item(('', 'root', 'source1', 'art1'), 1)
        self.assertEquals([('', 'root', 'source1', 'art1')],
                          self.newsfilter.excluded_items())
        self.assertEquals([],
            [i.object_path for i in self.newsfilter.get_last_items(10)])

    def test_synchronize_with_service(self):
        self.newsfilter.set_subjects(['sub'])
        self.newsfilter.synchronize_with_service()
        self.assert_(self.newsfilter.subjects() == ['sub'])
        self.service_news.remove_subject('sub')
        self.newsfilter.synchronize_with_service()
        self.assert_(self.newsfilter.subjects() == [])

    def test_search_items(self):
        self.newsfilter.set_subjects(['sub'])
        self.newsfilter.set_target_audiences(['ta'])
        self.newsfilter.set_sources([self.source1, self.source2, self.source3])
        resids = [i.object_path[-1]
                  for i in self.newsfilter.search_items('sub')]
        self.assertTrue('art1' in resids)
        self.assertTrue('art2' not in resids)
        self.assertTrue('art3' in resids)
        self.assertEquals(2, len(resids))

    def test_display_datetime(self):
        self.newsfilter.set_subjects(['sub', 'sub2'])
        self.newsfilter.set_target_audiences(['ta', 'ta2'])
        self.newsfilter.set_sources([self.source1, self.source3])
        items = self.newsfilter.get_last_items(2)
        itemids = [item.object_path[-1] for item in items]
        """first test to see the order of the articles"""
        self.assertEquals(itemids, ['art1', 'art2'])
        """now change the display datetime of the second article
           to be ahead of the first article, the order
           should change"""
        self.item1_2.get_viewable().set_display_datetime(DateTime() + 1)
        items = self.newsfilter.get_last_items(2)
        itemids = [item.object_path[-1] for item in items]
        self.assertEquals(set(itemids), set(['art2', 'art1']))

import unittest
def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(NewsFilterTestCase))
    return suite

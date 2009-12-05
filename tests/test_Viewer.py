# Copyright (c) 2002-2008 Infrae. All rights reserved.
# See also LICENSE.txt
# $Id$

import SilvaNewsTestCase


class NewsViewerTestCase(SilvaNewsTestCase.NewsBaseTestCase):
    """Test the NewsViewer interface.
    """
    def afterSetUp(self):
        super(NewsViewerTestCase, self).afterSetUp()
        self.service_news.add_subject('test', 'Test')
        self.service_news.add_subject('test2', 'Test 2')
        self.service_news.add_target_audience('test', 'Test')
        self.service_news.add_target_audience('test2', 'Test 2')
        #setup the filters and viewers
        self.newsfilter.set_subjects(['test', 'test2'])
        self.newsfilter.set_target_audiences(['test', 'test2'])
        self.newsfilter.add_source('/root/source1', 1)
        self.newsviewer.set_filter('/root/newsfilter', 1)

    def test_filters(self):
        self.assert_(self.newsviewer.filters() == ['/root/newsfilter'])
        self.newsviewer.set_filter('/root/newsfilter', 0)
        self.assert_(self.newsviewer.filters() == [])

    def test_findfilters(self):
        self.assert_(self.newsviewer.findfilters() == ['/root/newsfilter'])

    def test_findfilters_pairs(self):
        self.assert_(self.newsviewer.findfilters_pairs() == [(u'NewsFilter (<a href="/root/newsfilter/edit">/root/newsfilter</a>)', '/root/newsfilter')])

    def test_verify_filters(self):
        self.assert_(self.newsviewer.filters() == ['/root/newsfilter'])
        self.sroot.manage_delObjects('newsfilter')
        self.assert_(self.newsviewer.filters() == [])

    def test_get_items(self):
        self.newsfilter.set_subjects(['test', 'test2'])
        self.newsfilter.set_target_audiences(['test', 'test2'])
        iops = [i.object_path for i in self.newsviewer.get_items()]
        self.assert_(('', 'root', 'source1', 'art1') in iops)
        self.assert_(('', 'root', 'source1', 'art2') in iops)
        self.assert_(len(iops) == 2)

        self.newsfilter.set_excluded_item(('', 'root', 'source1', 'art2'), 1)
        iops = [i.object_path for i in self.newsviewer.get_items()]
        self.assert_(('', 'root', 'source1', 'art1') in iops)
        self.assert_(not ('', 'root', 'source1', 'art2') in iops)
        self.assert_(len(iops) == 1)

import unittest
def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(NewsViewerTestCase))
    return suite

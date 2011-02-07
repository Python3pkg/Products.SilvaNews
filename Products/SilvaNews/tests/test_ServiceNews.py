# Copyright (c) 2002-2011 Infrae. All rights reserved.
# See also LICENSE.txt
import unittest

from Products.SilvaNews.Tree import DuplicateIdError
from Products.SilvaNews.tests.SilvaNewsTestCase import FunctionalLayer


class ServiceNewsTestCase(unittest.TestCase):
    """Test the ServiceNews interface.
    """

    layer = FunctionalLayer

    def setUp(self):
        super(ServiceNewsTestCase, self).setUp()
        self.root = self.layer.get_application()
        self.service_news = self.root.service_news

    # We're not going to test specific units here but just make a small general test of each datamember,
    # since the methods are very simple data-manipulating things, not really suited to test in units, also
    # the chance of anything going wrong here is minimal. Still it's nice to know that they work :)
    def test_subjects(self):
        self.service_news.add_subject('test1', 'Test 1')
        self.service_news.add_subject('test2', 'Test 2', 'test1')
        self.assert_(('test1', 'Test 1') in self.service_news.subjects())
        self.assert_(('test2', 'Test 2') in self.service_news.subjects())
        #remove the default subject
        self.service_news.remove_subject('generic')
        self.assert_(len(self.service_news.subjects()) == 2)
        self.assert_(self.service_news.subject_tree() == [('test1', 'Test 1', 0), ('test2', 'Test 2', 1)])
        self.assert_(self.service_news.subject_form_tree() == [('Test 1', 'test1'), ('&nbsp;&nbsp;Test 2', 'test2')])
        self.assertRaises(DuplicateIdError, self.service_news.add_subject, 'test1', 'Test 1')
        self.assertRaises(ValueError, self.service_news.remove_subject, 'test1')
        self.service_news.remove_subject('test2')
        self.assert_(self.service_news.subject_tree() == [('test1', 'Test 1', 0)])

    def test_target_audiences(self):
        self.service_news.add_target_audience('test1', 'Test 1')
        self.service_news.add_target_audience('test2', 'Test 2', 'test1')
        self.assert_(('test1', 'Test 1')  in self.service_news.target_audiences())
        self.assert_(('test2', 'Test 2') in self.service_news.target_audiences())
        #remove the default TA
        self.service_news.remove_target_audience('all')
        self.assert_(len(self.service_news.target_audiences()) == 2)
        self.assert_(self.service_news.target_audience_tree() == [('test1', 'Test 1', 0), ('test2', 'Test 2', 1)])
        self.assert_(self.service_news.target_audience_form_tree() == [('Test 1', 'test1'), ('&nbsp;&nbsp;Test 2', 'test2')])
        self.assertRaises(DuplicateIdError, self.service_news.add_target_audience, 'test1', 'Test 1')
        self.assertRaises(ValueError, self.service_news.remove_target_audience, 'test1')
        self.service_news.remove_target_audience('test2')
        self.assert_(self.service_news.target_audience_tree() == [('test1', 'Test 1', 0)])


def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(ServiceNewsTestCase))
    return suite

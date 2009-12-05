# Copyright (c) 2002-2008 Infrae. All rights reserved.
# See also LICENSE.txt
# $Revision: 1.10 $
import os, sys
 
#import SilvaTestCase
from Products.SilvaNews.Tree import DuplicateIdError
import SilvaNewsTestCase


def add_helper(object, typename, id, title):
    getattr(object.manage_addProduct['Silva'], 'manage_add%s' % typename)(id, title)
    return getattr(object, id)

def add_helper_news(object, typename, id, title):
    getattr(object.manage_addProduct['SilvaNews'], 'manage_add%s' % typename)(id, title)
    return getattr(object, id)

class ServiceNewsTestCase(SilvaNewsTestCase.SilvaNewsTestCase):
    """Test the ServiceNews interface.
    """

    def afterSetUp(self):
        super(ServiceNewsTestCase, self).afterSetUp()
        self.service_news = self.root.service_news
        
    # We're not going to test specific units here but just make a small general test of each datamember,
    # since the methods are very simple data-manipulating things, not really suited to test in units, also
    # the chance of anything going wrong here is minimal. Still it's nice to know that they work :)
    def test_subjects(self):
        #first, remove the default subject
        self.service_news.remove_subject('generic')
        self.assert_(len(self.service_news.subjects()) == 0)
        self.service_news.add_subject('test1', 'Test 1')
        self.service_news.add_subject('test2', 'Test 2', 'test1')
        self.assert_(('test1', 'Test 1') in self.service_news.subjects())
        self.assert_(('test2', 'Test 2') in self.service_news.subjects())
        self.assert_(len(self.service_news.subjects()) == 2)
        self.assert_(self.service_news.subject_tree() == [('test1', 'Test 1', 0), ('test2', 'Test 2', 1)])
        self.assert_(self.service_news.subject_form_tree() == [('Test 1', 'test1'), ('&nbsp;&nbsp;Test 2', 'test2')])
        self.assertRaises(DuplicateIdError, self.service_news.add_subject, 'test1', 'Test 1')
        self.assertRaises(ValueError, self.service_news.remove_subject, 'test1')
        self.service_news.remove_subject('test2')
        self.assert_(self.service_news.subject_tree() == [('test1', 'Test 1', 0)])

    def test_target_audiences(self):
        #first, remove the default target audience
        self.service_news.remove_target_audience('all')
        self.assert_(len(self.service_news.target_audiences()) == 0)
        self.service_news.add_target_audience('test1', 'Test 1')
        self.service_news.add_target_audience('test2', 'Test 2', 'test1')
        self.assert_(('test1', 'Test 1')  in self.service_news.target_audiences())
        self.assert_(('test2', 'Test 2') in self.service_news.target_audiences())
        self.assert_(len(self.service_news.target_audiences()) == 2)
        self.assert_(self.service_news.target_audience_tree() == [('test1', 'Test 1', 0), ('test2', 'Test 2', 1)])
        self.assert_(self.service_news.target_audience_form_tree() == [('Test 1', 'test1'), ('&nbsp;&nbsp;Test 2', 'test2')])
        self.assertRaises(DuplicateIdError, self.service_news.add_target_audience, 'test1', 'Test 1')
        self.assertRaises(ValueError, self.service_news.remove_target_audience, 'test1')
        self.service_news.remove_target_audience('test2')
        self.assert_(self.service_news.target_audience_tree() == [('test1', 'Test 1', 0)])


import unittest
def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(ServiceNewsTestCase))
    return suite

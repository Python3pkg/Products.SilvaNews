# Copyright (c) 2002-2011 Infrae. All rights reserved.
# See also LICENSE.txt
# $Id$

import SilvaNewsTestCase


class NewsPublicationTestCase(SilvaNewsTestCase.NewsBaseTestCase):
    """Test the NewsPublication interface.
    """
    def test_hide_from_tocs(self):
        self.assertEquals(self.sm.getMetadataValue(self.source1,'silva-extra','hide_from_tocs'),
                          'hide')
        tree = [ i[1] for i in self.root.get_public_tree() ]
        self.assert_(self.source1 not in tree)
        
    def test_is_private(self):
        self.assertEquals(self.sm.getMetadataValue(self.source1,'snn-np-settings','is_private'),
                          'no')
        self.assertEquals(self.sm.getMetadataValue(self.source2,'snn-np-settings','is_private'),
                          'yes')
        res = self.catalog({'meta_type':'Silva News Publication',
                            'snn-np-settingsis_private':'no'})
        resids = [ r.getPath() for r in res ]
        self.assertEquals(len(resids),1)
        self.assert_('/root/source1' in resids)
        #now test the opposite
        res = self.catalog({'meta_type':'Silva News Publication',
                            'snn-np-settingsis_private':'yes'})
        resids = [ r.getPath() for r in res ]
        self.assert_('/root/source2' in resids)

import unittest
def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(NewsPublicationTestCase))
    return suite

# Copyright (c) 2002-2011 Infrae. All rights reserved.
# See also LICENSE.txt
# $Id$

import SilvaNewsTestCase
from datetime import datetime
from dateutil.relativedelta import relativedelta

class AgendaFilterTestCase(SilvaNewsTestCase.NewsBaseTestCase):
    """Test the AgendaFilter interfaces
    """
    def test_get_next_items(self):
        # add an Agenda Filter to the root

        self.af = self.add_agenda_filter(self.root, 'af','af')
        self.af.set_subjects(['sub'])
        self.af.set_target_audiences(['ta'])
        self.af.set_sources([self.source1])

        now = datetime.now()
        #add an item that ends in the range
        self.add_published_agenda_item(self.source1,
                                       'ai1','ai1',
                                       sdt=now - relativedelta(hours=5),
                                       edt=now + relativedelta(hours=1))
        #add an item that starts in the range (but ends
        # after the range
        self.add_published_agenda_item(self.source1,
                                       'ai2','ai2',
                                       sdt=now + relativedelta(1),
                                       edt=now + relativedelta(5))
        # add an item that starts before and ends after
        # the rangep
        self.add_published_agenda_item(self.source1,
                                       'ai3','ai3',
                                       sdt=now - relativedelta(5),
                                       edt=now + relativedelta(5))
        results = self.af.get_next_items(2)

        self.assertEquals(len(results),3)


import unittest
def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(AgendaFilterTestCase))
    return suite

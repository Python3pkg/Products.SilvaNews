# Copyright (c) 2002-2011 Infrae. All rights reserved.
# See also LICENSE.txt
# $Id$

import SilvaNewsTestCase
from datetime import datetime
from dateutil.relativedelta import relativedelta
from Products.SilvaNews.adapters.interfaces import INewsProvider

class AgendaFilterTestCase(SilvaNewsTestCase.NewsBaseTestCase):
    """Test the AgendaFilter interfaces
    """
    def test_get_next_items(self):
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
        results = self.agendafilter.get_next_items(2)

        self.assertEquals(len(results),3)

    def test_limit_recurring_items(self):
        ais = self.add_news_publication(self.root, 'agenda-items', 'Agenda Items')
        self.agendafilter.add_source(ais)
        self.agendaviewer.set_days_to_show(10)
        
        now = datetime.now()
        self.add_published_agenda_item(ais, 'ai1', 'ai1', sdt = now - relativedelta(days=3), \
                                       edt = now + relativedelta(hours=1))
        self.add_published_agenda_item(ais, 'ai2', 'ai2', sdt = now - relativedelta(days=3), \
                                       edt = now + relativedelta(hours=1))
        self.add_published_agenda_item(ais, 'ai3', 'ai3', sdt = now - relativedelta(days=2), \
                                       edt = now + relativedelta(hours=1))
        self.add_published_agenda_item(ais, 'ai4', 'ai4', sdt = now - relativedelta(days=1), \
                                       edt = now + relativedelta(hours=1))
        self.add_published_agenda_item(ais, 'ai5', 'ai5', sdt = now, edt = now + relativedelta(hours=1))
        
        self.assertTrue(len(INewsProvider(self.agendaviewer).getitems(5, None)), 5)
        self.assertTrue(len(INewsProvider(self.agendaviewer).getitems(10, 0)), 5)
        self.assertTrue(len(INewsProvider(self.agendaviewer).getitems(5, 1)), 2)
        self.assertTrue(len(INewsProvider(self.agendaviewer).getitems(5, 2)), 3)
        self.assertTrue(len(INewsProvider(self.agendaviewer).getitems(5, 3)), 5)

import unittest
def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(AgendaFilterTestCase))
    return suite

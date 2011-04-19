import unittest
from datetime import datetime

from Products.Silva.tests.test_xmlimport import SilvaXMLTestCase
from Products.SilvaNews.tests.SilvaNewsTestCase import FunctionalLayer
from Products.SilvaNews.datetimeutils import local_timezone, UTC


class TestImport(SilvaXMLTestCase):
    layer = FunctionalLayer

    def setUp(self):
        super(TestImport, self).setUp()

    def test_import_news_filter(self):
        self.import_file('import_newsfilter.xml', globs=globals())
        self.assertTrue(hasattr(self.root, 'export'))
        self.assertTrue(hasattr(self.root.export, 'filter'))
        self.assertTrue(hasattr(self.root.export, 'newspub'))
        self.assertEquals([self.root.export.newspub],
                          self.root.export.filter.get_sources())
        self.assertEquals('News Filter', self.root.export.filter.get_title())

    def test_import_agenda_filter(self):
        self.import_file('import_agendafilter.xml', globs=globals())
        self.assertTrue(hasattr(self.root, 'export'))
        self.assertTrue(hasattr(self.root.export, 'filter'))
        self.assertTrue(hasattr(self.root.export, 'newspub'))
        self.assertEquals([self.root.export.newspub],
                          self.root.export.filter.get_sources())
        self.assertEquals('Agenda Filter', self.root.export.filter.get_title())

    def test_import_news_viewer(self):
        self.import_file('import_newsviewer.xml', globs=globals())
        self.assertTrue(hasattr(self.root.export, 'viewer'))
        self.assertEquals([self.root.export.newspub],
                          self.root.export.filter.get_sources())
        self.assertEquals([self.root.export.filter],
                          self.root.export.viewer.get_filters())
        self.assertEquals(self.root.export.viewer.get_year_range(), 3)
        self.assertEquals('News Viewer', self.root.export.viewer.get_title())
        
    def test_import_news_item(self):
        self.import_file('import_newsitem.xml', globs=globals())
        self.assertTrue(hasattr(self.root.export, 'newspub'))
        self.assertTrue(hasattr(self.root.export.newspub, 'news'))
        news = self.root.export.newspub.news
        version = news.get_editable()
        self.assertEquals(['all'], version.subjects())
        self.assertEquals(['generic'], version.target_audiences())
        dt = datetime(2010, 9, 30, 8, 0, 0, tzinfo=UTC)
        dt = dt.astimezone(local_timezone).replace(tzinfo=None)
        self.assertEquals(dt, version.display_datetime())
        
        #test to ensure the content was imported properly
        self.assertEquals('Products.SilvaNews.NewsItem.NewsItemTemplate',
                          version.get_layout_name())
        parts = list(version.get_parts_for_slot("newsitemcontent"))
        self.assertTrue(len(parts) == 1)
        self.assertEquals(parts[0].get_config(),
                          {'rich_text': u'<p>Test</p>'})
        
        self.assertEquals(version.get_external_link(),
                          'http://www.google.com')
        self.assertEquals(version.get_link_method(),
                          'external_link')
        

    def test_import_agenda_item(self):
        self.import_file('import_agendaitem.xml', globs=globals())
        self.assertTrue(hasattr(self.root.export, 'newspub'))
        self.assertTrue(hasattr(self.root.export.newspub, 'event'))
        version = self.root.export.newspub.event.get_viewable()

        self.assertEquals('Europe/Amsterdam', version.get_timezone_name())
        timezone = version.get_timezone()
        self.assertEquals(datetime(2010, 9, 1, 10, 0, 0, tzinfo=timezone),
            version.get_start_datetime())
        self.assertEquals('Rotterdam', version.get_location())
        self.assertTrue(version.is_all_day())
        self.assertEquals(['all'], version.subjects())
        self.assertEquals(['generic'], version.target_audiences())
        self.assertEquals('FREQ=DAILY;UNTIL=20100910T123212Z',
            version.get_recurrence())
        self.assertEquals('Europe/Amsterdam', version.get_timezone_name())
        #display_datetime is still naive.  The DT in the import was in UTC,
        # which was converted to the local time.  Do the same here
        # (do not assume Europe/Amsterdam time)
        dt = datetime(2010, 9, 30, 8, 0, 0, tzinfo=UTC)
        dt = dt.astimezone(local_timezone).replace(tzinfo=None)
        self.assertEquals(
            dt,
            version.display_datetime())


def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TestImport))
    return suite

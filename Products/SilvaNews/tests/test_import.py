import unittest
from datetime import datetime

from Products.Silva.tests.test_xmlimport import SilvaXMLTestCase
from Products.SilvaNews.tests.SilvaNewsTestCase import FunctionalLayer


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
        self.assertEquals('News Viewer', self.root.export.viewer.get_title())

    def test_import_news_item(self):
        self.import_file('import_newsitem.xml', globs=globals())
        self.assertTrue(hasattr(self.root.export, 'newspub'))
        self.assertTrue(hasattr(self.root.export.newspub, 'news'))
        news = self.root.export.newspub.news
        version = news.get_editable()
        self.assertEquals(['all'], version.subjects())
        self.assertEquals(['generic'], version.target_audiences())
        self.assertEquals(
            datetime(2010, 9, 30, 10, 0, 0),
            version.display_datetime())

    def test_import_agenda_item(self):
        self.import_file('import_agendaitem.xml', globs=globals())
        self.assertTrue(hasattr(self.root.export, 'newspub'))
        self.assertTrue(hasattr(self.root.export.newspub, 'event'))
        version = self.root.export.newspub.event.get_viewable()

        self.assertEquals(['all'], version.subjects())
        self.assertEquals(['generic'], version.target_audiences())
        self.assertEquals(
            datetime(2010, 9, 30, 10, 0, 0),
            version.display_datetime())

        occurrences = version.get_occurrences()
        self.assertEquals(len(occurrences), 1)

        occurrence = occurrences[0]
        timezone = occurrence.get_timezone()
        self.assertEquals('Europe/Amsterdam', occurrence.get_timezone_name())
        self.assertEquals('Rotterdam', occurrence.get_location())
        self.assertTrue(occurrence.is_all_day())
        self.assertEquals(
            datetime(2010, 9, 1, 10, 0, 0, tzinfo=timezone),
            occurrence.get_start_datetime())
        self.assertEquals(
            'FREQ=DAILY;UNTIL=20100910T123212Z',
            occurrence.get_recurrence())


def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TestImport))
    return suite

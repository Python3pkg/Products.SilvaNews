import unittest
from datetime import datetime
from Products.Silva.tests.test_xmlexport import SilvaXMLTestCase
from Products.Silva.tests.helpers import publish_object
from Products.SilvaNews.tests.SilvaNewsTestCase import FunctionalLayer
from Products.SilvaNews.datetimeutils import get_timezone
from Products.Silva.silvaxml import xmlexport


class TestExport(SilvaXMLTestCase):
    layer = FunctionalLayer

    def test_export_news_filter(self):
        """Add a filter and a news publication at root level and export
        the filter.
        """
        factory = self.root.manage_addProduct['Silva']
        factory.manage_addFolder('export', 'Export Folder')

        factory = self.root.export.manage_addProduct['SilvaNews']
        factory.manage_addNewsPublication('newspub', 'NewsPublication')
        factory.manage_addNewsFilter('filter', 'News Filter')
        self.root.export.filter.set_sources([self.root.export.newspub])

        xml, info = xmlexport.exportToString(self.root.export)
        self.assertExportEqual(xml, 'export_newsfilter.xml', globs=globals())

    def test_export_agenda_filter(self):
        """Add a filter and a news publication at root level and export
        the filter.
        """
        factory = self.root.manage_addProduct['Silva']
        factory.manage_addFolder('export', 'Export Folder')

        factory = self.root.export.manage_addProduct['SilvaNews']
        factory.manage_addNewsPublication('newspub', 'NewsPublication')
        factory.manage_addAgendaFilter('filter', 'Agenda Filter')
        self.root.export.filter.add_source(self.root.export.newspub)

        xml, info = xmlexport.exportToString(self.root.export)
        self.assertExportEqual(xml, 'export_agendafilter.xml', globs=globals())

    def test_export_news_viewer(self):
        """ Same test than above but with 
        """
        factory = self.root.manage_addProduct['Silva']
        factory.manage_addFolder('export', 'Export Folder')

        factory = self.root.export.manage_addProduct['SilvaNews']
        factory.manage_addNewsPublication('newspub', 'NewsPublication')
        factory.manage_addNewsFilter('filter', 'News Filter')
        factory.manage_addNewsViewer('viewer', 'News Viewer')
        self.root.export.filter.set_sources([self.root.export.newspub])
        self.root.export.viewer.set_filters([self.root.export.filter])
        self.root.export.viewer.set_year_range(3)
        xml, info = xmlexport.exportToString(self.root.export)
        self.assertExportEqual(xml, 'export_newsviewer.xml', globs=globals())

    def test_export_news_item(self):
        """ export an news item
        """
        factory = self.root.manage_addProduct['Silva']
        factory.manage_addFolder('export', 'Export Folder')

        factory = self.root.export.manage_addProduct['SilvaNews']
        factory.manage_addNewsPublication('newspub', 'NewsPublication')
        factory = self.root.export.newspub.manage_addProduct['SilvaNews']

        factory.manage_addPlainArticle('news', 'Some news')
        version = self.root.export.newspub.news.get_editable()
        self.assertTrue(version)
        version.set_subjects(['all'])
        version.set_target_audiences(['generic'])
        version.set_display_datetime(datetime(2010, 9, 30, 10, 0, 0))
        version.set_link_method("external_link")
        version.set_external_link("http://www.google.com")
        xml, info = xmlexport.exportToString(self.root.export)
        self.assertExportEqual(xml, 'export_newsitem.xml', globs=globals())

    def test_export_agenda_item(self):
        """ export an agenda item
        """
        factory = self.root.manage_addProduct['Silva']
        factory.manage_addFolder('export', 'Export Folder')

        factory = self.root.export.manage_addProduct['SilvaNews']
        factory.manage_addNewsPublication('newspub', 'NewsPublication')
        factory = self.root.export.newspub.manage_addProduct['SilvaNews']
        factory.manage_addPlainAgendaItem('event', 'Some event')
        version = self.root.export.newspub.event.get_editable()
        self.assertTrue(version)
        version.set_location('Rotterdam')
        version.set_subjects(['all'])
        version.set_target_audiences(['generic'])
        version.set_recurrence('FREQ=DAILY;UNTIL=20100910T123212Z')
        timezone = get_timezone('Europe/Amsterdam')
        version.set_timezone_name('Europe/Amsterdam')
        version.set_start_datetime(
            datetime(2010, 9, 1, 10, 0, 0, tzinfo=timezone))
        version.set_all_day(True)
        version.set_display_datetime(datetime(2010, 9, 30, 10, 0, 0))
        publish_object(self.root.export.newspub.event)

        xml, info = xmlexport.exportToString(self.root.export)
        self.assertExportEqual(xml, 'export_agendaitem.xml', globs=globals())


def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TestExport))
    return suite

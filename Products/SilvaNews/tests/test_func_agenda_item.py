import unittest
from datetime import datetime
from Products.SilvaNews.datetimeutils import get_timezone
from Products.SilvaNews.tests.SilvaNewsTestCase import FunctionalLayer
from Products.Silva.ftesting import smi_settings


class TestAgendaItemAddTestCase(unittest.TestCase):

    layer = FunctionalLayer

    def setUp(self):
        self.root = self.layer.get_application()
        factory = self.root.manage_addProduct['SilvaNews']
        factory.manage_addNewsPublication('news', 'News Publication')
        self.browser = self.layer.get_browser(settings=smi_settings)
        self.browser.login('manager')
        self.browser.options.handle_errors = False

    def test_agenda_item_add_form(self):
        status = self.browser.open(
            'http://localhost/root/news/edit/+/Silva Agenda Item')
        self.assertEquals(200, status)
        form = self.browser.get_form('addform')
        self.assertTrue(form)
        form.get_control('addform.field.id').value = 'event'
        form.get_control('addform.field.title').value = 'Event'
        form.get_control('addform.field.timezone_name').value = 'Europe/Paris'
        form.get_control('addform.field.start_datetime.day').value = '01'
        form.get_control('addform.field.start_datetime.month').value = '09'
        form.get_control('addform.field.start_datetime.year').value = '2010'
        form.get_control('addform.field.start_datetime.hour').value = '10'
        form.get_control('addform.field.start_datetime.min').value = '20'
        form.get_control('addform.field.subjects').value = ['generic']
        form.get_control('addform.field.target_audiences').value = ['all']
        form.get_control('addform.field.link_method').value = 'article'

        status = form.get_control('addform.action.save_edit').submit()
        self.assertEquals(200, status)

        item = getattr(self.root.news, 'event', False)
        self.assertTrue(item)
        version = item.get_editable()
        self.assertTrue(version)

        self.assertEquals('event', item.id)
        self.assertEquals('Event', version.get_title())
        self.assertEquals('Europe/Paris', version.get_timezone_name())
        self.assertEquals([u'generic'], version.subjects())
        self.assertEquals([u'all'], version.target_audiences())
        self.assertEquals(
            datetime(2010, 9, 1, 10, 20, 0,
                     tzinfo=get_timezone('Europe/Paris')),
            version.get_start_datetime())

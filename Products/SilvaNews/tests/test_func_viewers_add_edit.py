import unittest
from Products.SilvaNews.tests.SilvaNewsTestCase import FunctionalLayer
from Products.Silva.ftesting import smi_settings


class BaseTest(unittest.TestCase):
    layer = FunctionalLayer

    def setUp(self):
        self.root = self.layer.get_application()
        self.browser = self.layer.get_browser(settings=smi_settings)
        self.browser.login('manager', 'manager')


class ViewerAddTestBase(BaseTest):

    meta_type = None
    id = 'viewer'
    path = '/root/%s' % id

    def test_add_form_save_edit(self):
        form = self.get_add_form()
        form.get_control('addform.field.title').value = 'Viewer'
        form.get_control('addform.field.id').value = self.id
        status = form.get_control('addform.action.save_edit').submit()
        self.assertEquals(200, status)
        self.assertEquals('%s/edit' % self.path, self.browser.url)
        self.assertEquals(self.meta_type, getattr(self.root, self.id).meta_type)

    def test_add_form_save(self):
        form = self.get_add_form()
        form.get_control('addform.field.title').value = 'Viewer'
        form.get_control('addform.field.id').value = self.id
        status = form.get_control('addform.action.save').submit()
        self.assertEquals(200, status)
        self.assertEquals('/root/edit', self.browser.url)
        self.assertEquals(self.meta_type, getattr(self.root, self.id).meta_type)

    def test_add_form_cancel(self):
        form = self.get_add_form()
        status = form.get_control('addform.action.cancel').submit()
        self.assertEquals(200, status)
        self.assertEquals('/root/edit', self.browser.url)

    def get_add_form(self):
        status = self.browser.open(
            'http://localhost/root/edit/+/%s' % self.meta_type)
        self.assertEquals(200, status)
        form = self.browser.get_form('addform')
        return form


class NewsViewerAddTestCase(ViewerAddTestBase):
    meta_type = 'Silva News Viewer'


class AgendaViewerAddTestCase(ViewerAddTestBase):
    meta_type = 'Silva Agenda Viewer'


class ViewerEditTestBase(BaseTest):
    meta_type = None
    id = 'viewer'
    path = '/root/%s' % id
    build_method = None

    def setUp(self):
        super(ViewerEditTestBase, self).setUp()
        factory = self.root.manage_addProduct['SilvaNews']
        getattr(factory, self.build_method)(self.id, 'Viewer')
        factory.manage_addNewsPublication('newspub', 'News Pub')
        factory.manage_addNewsFilter('news_filter', 'News Filter')
        self.root.news_filter.set_sources([self.root.newspub])
        self.viewer = getattr(self.root, self.id)

    def test_change_things(self):
        form = self.get_edit_form()
        control = form.get_control('editform.field.timezone_name')
        self.assertEquals('Europe/Amsterdam', control.value)
        control.value = 'Europe/Paris'
        control = form.get_control('editform.field.first_weekday')
        self.assertEquals('0', control.value)
        control.value = '1'
        form.get_control('editform.field.filters').value = '/root/newspub'
        status = form.get_control('editform.action.save-changes').submit()
        self.assertEquals(200, status)
        self.assertEquals([], self.browser.inspect.form_errors)
        self.assertEquals(['Changes saved.'], self.browser.inspect.feedback)

        form = self.browser.get_form('editform')
        control = form.get_control('editform.field.timezone_name')
        self.assertEquals('Europe/Paris', control.value)
        control = form.get_control('editform.field.first_weekday')
        self.assertEquals('1', control.value)

        self.assertEquals('Europe/Paris', self.viewer.get_timezone_name())
        self.assertEquals(1, self.viewer.get_first_weekday())

    def test_change_numbers(self):
        form = self.get_edit_form()
        control = form.get_control('editform.field.number_is_days')
        value = str(int(self.viewer.get_number_is_days()))
        self.assertEquals(value, control.value)
        control.value = str(int(not int(value)))
        control = form.get_control('editform.field.number_to_show')
        self.assertEquals('25', control.value)
        control.value = '10'
        control = form.get_control('editform.field.year_range')
        self.assertEquals('2', control.value)
        control.value = '1'
        form.get_control('editform.field.filters').value = '/root/newspub'
        status = form.get_control('editform.action.save-changes').submit()
        self.assertEquals(200, status)
        self.assertEquals([], self.browser.inspect.form_errors)
        self.assertEquals(['Changes saved.'], self.browser.inspect.feedback)

        form = self.browser.get_form('editform')
        control = form.get_control('editform.field.number_is_days')
        self.assertEquals(str(int(not int(value))), control.value)
        self.assertEquals(int(not int(value)), self.viewer.get_number_is_days())
        control = form.get_control('editform.field.number_to_show')
        self.assertEquals('10', control.value)
        self.assertEquals(10, self.viewer.get_number_to_show())
        control = form.get_control('editform.field.year_range')
        self.assertEquals('1', control.value)
        self.assertEquals(1, self.viewer.get_year_range())

    def test_without_any_filter_set(self):
        form = self.get_edit_form()
        status = form.get_control('editform.action.save-changes').submit()
        self.assertEquals(200, status)
        self.assertEquals(['Missing required value.'],
                          self.browser.inspect.form_errors)
        self.assertEquals(['There were errors.'], self.browser.inspect.feedback)

    def get_edit_form(self):
        status = self.browser.open(
            'http://localhost%s/edit' % self.path)
        self.assertEquals(200, status)
        form = self.browser.get_form('editform')
        return form


class NewsViewerEditTestCase(ViewerEditTestBase):
    meta_type = 'Silva News Viewer'
    build_method = 'manage_addNewsViewer'


class AgendaViewerEditTestCase(ViewerEditTestBase):
    meta_type = 'Silva Agenda Viewer'
    build_method = 'manage_addAgendaViewer'


def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(NewsViewerAddTestCase))
    suite.addTest(unittest.makeSuite(AgendaViewerAddTestCase))
    suite.addTest(unittest.makeSuite(NewsViewerEditTestCase))
    suite.addTest(unittest.makeSuite(AgendaViewerEditTestCase))
    return suite

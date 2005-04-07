import os

from Globals import InitializeClass, package_home
from AccessControl import ClassSecurityInfo
from Products.PageTemplates.PageTemplateFile import PageTemplateFile
from Products.PageTemplates.ZopePageTemplate import ZopePageTemplate
from zExceptions import NotFound

from Products.SilvaExternalSources.interfaces import IExternalSource
from Products.SilvaExternalSources.CodeSource import CodeSource

from Products.Silva import SilvaPermissions
from Products.Silva.helpers import add_and_edit

from Products.Formulator.Form import ZMIForm
from Products.Formulator.XMLToForm import XMLToForm

#from Products.Silva.i18n import translate as _

class InlineViewer(CodeSource):
    """A news viewer object to display news items within a Silva document
    
        Inspired by Marc Petitmermet's Inline News Viewer (some code was
        copied from that product too, thanks Marc!)
    """

    __implements__ = IExternalSource
    meta_type = 'Silva News Inline Viewer'
    security = ClassSecurityInfo()

    def __init__(self, id, title):
        CodeSource.inheritedAttribute('__init__')(self, id, title)
        self._script_id = 'view'
        self._data_encoding = 'UTF-8'

    def manage_afterAdd(self, item, container):
        self._set_form()
        self._set_view()

    security.declareProtected(SilvaPermissions.ChangeSilvaAccess,
                                'refresh')
    def refresh(self):
        """reload the form and pt"""
        if 'view' in self.objectIds():
            self.manage_delObjects(['view'])
        self._set_form()
        self._set_view()
        return 'refreshed for and pagetemplate'

    def _set_form(self):
        self.parameters = ZMIForm('form', 'Properties Form')
        f = open(os.path.join(
                package_home(globals()), 
                'www', 
                'inline_viewer_form.form'))
        XMLToForm(f.read(), self.parameters)
        f.close()

    def _set_view(self):
        f = open(os.path.join(
                package_home(globals()),
                'www',
                'inline_viewer_view.pt'))
        self._setObject('view', ZopePageTemplate('view', f.read()))
        f.close()

    security.declareProtected(SilvaPermissions.AccessContentsInformation,
                                'to_html')
    def to_html(self, *args, **kwargs):
        """render the news list"""
        self.REQUEST['model'] = self
        try:
            return getattr(self, 'view')(**kwargs)
        except:
            import sys, traceback
            exc, e, tb = sys.exc_info()
            tbs = '\n'.join(traceback.format_tb(tb))
            del tb
            ret =  '%s - %s<br />\n\n%s<br />' % (exc, e, tbs)
            return ret

    security.declareProtected(SilvaPermissions.ChangeSilvaContent,
                                'get_viewers')
    def get_viewers(self):
        """returns a list of available viewers
        
            finds all viewers on this level
        """
        # first get self in the right context
        phpath = self.getPhysicalPath()
        parent = self.restrictedTraverse(phpath[:-1])
        ret = [(o.get_title(), o.id) for o in 
                    parent.objectValues(['Silva News Viewer', 
                                            'Silva Agenda Viewer', 
                                            'Silva RSS Aggregator'])]
        return ret

    security.declareProtected(SilvaPermissions.AccessContentsInformation,
                                'get_items')
    def get_items(self, number, viewer):
        """returns the items for the selected viewer"""
        from adapters.newsprovider import getNewsProviderAdapter
        viewerobj = getattr(self.aq_parent, viewer, None)
        if viewerobj == None:
            return []
        adapter = getNewsProviderAdapter(viewerobj)
        return adapter.getitems(number)

    security.declareProtected(SilvaPermissions.AccessContentsInformation,
                                'get_viewer_title')
    def get_viewer_obj(self, viewer):
        """returns the title of a viewer"""
        obj = getattr(self.aq_parent, viewer, None)
        return obj

    security.declareProtected(SilvaPermissions.AccessContentsInformation,
                                'limit_intro')
    def limit_intro(self, intro, length):
        """shortens a bit of text"""
        # XXX disabled for now since it's rather scary to just do
        # string manipulations on HTML...
        return intro

InitializeClass(InlineViewer)

manage_addInlineViewerForm = PageTemplateFile(
    "www/inlineViewerAdd", globals(), __name__='manage_addInlineViewerForm')

def manage_addInlineViewer(context, id, title, REQUEST=None):
    """Add an Inline Viewer"""
    v = InlineViewer(id, unicode(title, 'UTF-8'))
    context._setObject(id, v)
    add_and_edit(context, id, REQUEST)
    return ''

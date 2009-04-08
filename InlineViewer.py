# Copyright (c) 2002-2008 Infrae. All rights reserved.
# See also LICENSE.txt
# $Revision: 1.25 $

from zope.interface import implements

import os

import Products
from Globals import InitializeClass, package_home
from AccessControl import ClassSecurityInfo
from Products.PageTemplates.PageTemplateFile import PageTemplateFile
from Products.PageTemplates.ZopePageTemplate import ZopePageTemplate
from zExceptions import NotFound

from OFS.Image import Image

from Products.Formulator.Form import ZMIForm
from Products.Formulator.XMLToForm import XMLToForm

from Products.SilvaExternalSources.interfaces import IExternalSource
from Products.SilvaExternalSources.CodeSource import CodeSource

from Products.Silva import SilvaPermissions
from Products.Silva.helpers import add_and_edit
from Products.Silva.adapters.virtualhosting import getVirtualHostingAdapter

from interfaces import IViewer
from adapters.interfaces import INewsProvider

#from Products.Silva.i18n import translate as _

def ustr(x):
    if type(x) == unicode:
        return x
    elif type(x) == str:
        return unicode(x, 'UTF-8')
    return str(x)

class InlineViewer(CodeSource):
    """A news viewer object to display news items within a Silva document
    
        Inspired by Marc Petitmermet's Inline News Viewer (some code was
        copied from that product too, thanks Marc!)
    """

    implements(IExternalSource)
    meta_type = 'Silva News Inline Viewer'
    security = ClassSecurityInfo()

    # we know existing objects were already initialized, but
    # they didn't have this attribute yet and we don't want
    # to write an upgrade script because we're lazy :)
    _is_initialized = True
    
    def __init__(self, id):
        CodeSource.inheritedAttribute('__init__')(self, id)
        self._script_id = 'view'
        self._data_encoding = 'UTF-8'
        self._is_initialized = False
        
    security.declareProtected(SilvaPermissions.ChangeSilvaAccess,
                                'refresh')
    def refresh(self):
        """reload the form and pt"""
        for name in ('view','feed_footer','rss10.gif'):
            if name in self.objectIds():
                self.manage_delObjects([name])
        self._set_form()
        self._set_views()
        return 'refreshed form and pagetemplate'

    def _set_form(self):
        self.parameters = ZMIForm('form', 'Properties Form')
        f = open(os.path.join(
                package_home(globals()), 
                'www', 
                'inline_viewer_form.form'))
        XMLToForm(f.read(), self.parameters)
        f.close()

    def _set_views(self):
        f = open(os.path.join(
                package_home(globals()),
                'www',
                'inline_viewer_view.pt'))
        self._setObject('view', ZopePageTemplate('view', f.read()))
        f.close()

        f = open(os.path.join(
                package_home(globals()),
                'www',
                'inline_viewer_footer.pt'))
        self._setObject('feed_footer', 
                        ZopePageTemplate('feed_footer', f.read()))
        f.close()

        f = open(os.path.join(
                package_home(globals()),
                'www',
                'rss10.gif'), 'rb')
        self._setObject('rss10.gif', Image('rss10.gif', 'RSS (1.0)', f))
        f.close()

    security.declareProtected(SilvaPermissions.AccessContentsInformation,
                                'to_html')
    def to_html(self, *args, **kwargs):
        """render the news list"""
        oldmodel = self.REQUEST.other['model']
        self.REQUEST.other['oldmodel'] = oldmodel
        self.REQUEST.other['model'] = self
        try:
            return ustr(getattr(self, self._script_id)(**kwargs))
        finally:
            self.REQUEST.other['model'] = oldmodel
            del self.REQUEST.other['oldmodel']
        #except:
        #    import sys, traceback
        #    exc, e, tb = sys.exc_info()
        #    tbs = '\n'.join(traceback.format_tb(tb))
        #    del tb
        #    ret =  '%s - %s<br />\n\n%s<br />' % (exc, e, tbs)
        #    return ret

    security.declareProtected(SilvaPermissions.ChangeSilvaContent,
                                'get_viewers')
    def get_viewers(self):
        """returns a list of available viewers
            finds all viewers on this level
        """
        adapter = getVirtualHostingAdapter(self)
        root = adapter.getVirtualRoot()
        if root is None:
            root = self.get_root()

        #determine which silva types are IViewers
        viewer_metatypes = []
        mts = Products.meta_types
        for mt in mts:
            if (mt.has_key('instance') and
                IViewer.implementedBy(mt['instance'])):
                viewer_metatypes.append(mt['name'])
                
        #this should get all viewers at this level or higher
        # (to the vhost root), not at the code sources level
        objects = []
        container = self.REQUEST.model.get_container()
        invcontainer = self.get_container()
        while container != root.aq_parent:
            objs = [(o.get_title(), o.id) for o in 
                    container.objectValues(viewer_metatypes)]
            objects.extend(objs)
            container = container.aq_parent
        return objects

    security.declareProtected(SilvaPermissions.AccessContentsInformation,
                                'get_items')
    def get_items(self, number, viewer):
        """returns the items for the selected viewer"""
        viewerobj = getattr(self.REQUEST.oldmodel, viewer, None)
        if viewerobj == None:
            return []
        adapter = INewsProvider(viewerobj)
        return adapter.getitems(number)

    security.declareProtected(SilvaPermissions.AccessContentsInformation,
                                'get_viewer_obj')
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
    v = InlineViewer(id)
    v.title = unicode(title, 'UTF-8')
    context._setObject(id, v)
    add_and_edit(context, id, REQUEST)
    return ''

def inline_viewer_moved(object, event):
    if not object._is_initialized:
        object._set_form()
        object._set_views()
        object._is_initialized = True

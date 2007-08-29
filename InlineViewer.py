# Copyright (c) 2002-2006 Infrae. All rights reserved.
# See also LICENSE.txt
# $Revision: 1.25 $

from zope.interface import implements

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

from OFS.Image import Image

from Products.Formulator.Form import ZMIForm
from Products.Formulator.XMLToForm import XMLToForm

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
        
    def manage_afterAdd(self, item, container):
        if not self._is_initialized:
            self._set_form()
            self._set_views()
            self._is_initialized = True

    security.declareProtected(SilvaPermissions.ChangeSilvaAccess,
                                'refresh')
    def refresh(self):
        """reload the form and pt"""
        if 'view' in self.objectIds():
            self.manage_delObjects(['view'])
        if 'feed_footer' in self.objectIds():
            self.manage_delObjects(['feed_footer'])
        # XXX this code doesn't look like it can work,
        # as rrs10.gif is not removed and set_views tries to
        # add it again
        self._set_form()
        self._set_views()
        return 'refreshed for and pagetemplate'

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
        # XXX this is screwed up, both because the name clashes with the
        # 'normal' request.model, and because this leaks memory (have to
        # store stuff in request.other instead)
        self.REQUEST.form['model'] = self
        try:
            return ustr(getattr(self, 'view')(**kwargs))
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

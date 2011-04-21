# Copyright (c) 2002-2011 Infrae. All rights reserved.
# See also LICENSE.txt
# $Revision: 1.25 $

from zope.interface import implements
from zope.app.container.interfaces import IObjectMovedEvent
import os

import Products
from App.class_init import InitializeClass
from App.Common import package_home

from AccessControl import ClassSecurityInfo
from Products.PageTemplates.PageTemplateFile import PageTemplateFile
from Products.PageTemplates.ZopePageTemplate import ZopePageTemplate

from OFS.Image import Image

from Products.Formulator.Form import ZMIForm
from Products.Formulator.XMLToForm import XMLToForm

from Products.SilvaExternalSources.CodeSource import CodeSource

from silva.core.views.interfaces import IVirtualSite
from silva.core import conf as silvaconf
from Products.Silva import SilvaPermissions
from Products.Silva.helpers import add_and_edit

from Products.SilvaNews.interfaces import IViewer, IInlineViewer
from Products.SilvaNews.adapters.interfaces import INewsProvider


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

    implements(IInlineViewer)
    meta_type = 'Silva News Inline Viewer'
    security = ClassSecurityInfo()
    silvaconf.icon('www/codesource.png')
    silvaconf.factory('manage_addInlineViewerForm')
    silvaconf.factory('manage_addInlineViewer')

    # we know existing objects were already initialized, but
    # they didn't have this attribute yet and we don't want
    # to write an upgrade script because we're lazy :)
    _is_initialized = True

    def __init__(self, id):
        InlineViewer.inheritedAttribute('__init__')(self, id)
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
        filename = os.path.join(
            package_home(globals()), 'www', 'inline_viewer_form.form')
        with open(filename, 'r') as fd:
            XMLToForm(fd.read(), self.parameters)

    def _set_views(self):
        filename = os.path.join(
                package_home(globals()), 'www', 'inline_viewer_view.pt')
        with open(filename, 'r') as fd:
            self._setObject('view', ZopePageTemplate('view', fd.read()))

        filename = os.path.join(
                package_home(
                globals()), 'www', 'inline_viewer_footer.pt')
        with open(filename, 'r') as fd:
            self._setObject('feed_footer',
                            ZopePageTemplate('feed_footer', fd.read()))

        filename = os.path.join(
                package_home(globals()), 'www', 'rss10.gif')
        with open(filename, 'r') as fd:
            self._setObject('rss10.gif', Image('rss10.gif', 'RSS (1.0)', fd))

    security.declareProtected(SilvaPermissions.ChangeSilvaContent,
                                'get_viewers')
    def get_viewers(self, model=None, request=None):
        """returns a list of available viewers
            finds all viewers on this level
        """
        request = request or self.REQUEST
        model = model or request.get('model')
        root = IVirtualSite(request).get_root()

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
        container = model.get_container()
        while container != root.aq_parent:
            objs = [(o.get_title(), o.id) for o in
                    container.objectValues(viewer_metatypes)]
            objects.extend(objs)
            container = container.aq_parent
        return objects

    security.declareProtected(SilvaPermissions.AccessContentsInformation,
                                'get_items')
    def get_items(self, number, viewer, model, recurrence_limit=None):
        """returns the items for the selected viewer"""
        provider = self.get_viewer(viewer, model)
        if provider is None:
            return []
        return INewsProvider(provider).getitems(number, recurrence_limit)

    security.declareProtected(SilvaPermissions.AccessContentsInformation,
                                'get_viewer')
    def get_viewer(self, viewer, model):
        """returns the title of a viewer"""
        return getattr(model, viewer, None)

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

@silvaconf.subscribe(IInlineViewer,
                     IObjectMovedEvent)
def inline_viewer_moved(object, event):
    if not object._is_initialized:
        object._set_form()
        object._set_views()
        object._is_initialized = True

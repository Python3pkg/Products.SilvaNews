# Copyright (c) 2002-2005 Infrae. All rights reserved.
# See also LICENSE.txt
# $Revision: 1.6.2.1 $

# Zope
from AccessControl import ClassSecurityInfo
from Products.PageTemplates.PageTemplateFile import PageTemplateFile
from Globals import InitializeClass
# Silva
from Products.Silva.Publication import Publication
from Products.Silva.interfaces import IPublication
#from Products.Silva.Folder import Folder
from Products.Silva.interfaces import IContainer
from Products.Silva import SilvaPermissions
#misc
from Products.Silva.helpers import add_and_edit
from Products.SilvaNews.interfaces import INewsItem, IAgendaItem
from Products.Silva.SilvaObject import SilvaObject
from Products.Silva import mangle

from ObjectTitle import ObjectTitle

class DuplicateError(Exception):
    pass

icon = 'www/news_source.png'
addable_priority = 3

class NewsPublication(ObjectTitle, Publication):
    """A special publication type (a.k.a. News Source) for news 
    and agenda items. News Filters and Agenda Filters can pick up 
    news from these sources anywhere in a Silva site.
    """
    security = ClassSecurityInfo()

    meta_type = "Silva News Publication"

    __implements__ = (IContainer, IPublication)

    hide_from_tocs = 1
    
    _addables_allowed_in_publication = ['Silva Article', 'Silva Agenda Item', 'Silva Publication', 'Silva Folder']

    def __init__(self, id):
        NewsPublication.inheritedAttribute('__init__')(self, id)
        self._is_private = 0


    # ACCESSORS

    security.declareProtected(SilvaPermissions.AccessContentsInformation,
                              'is_private')
    def is_private(self):
        """Returns the private-state
        """
        return self._is_private

    security.declareProtected(SilvaPermissions.AccessContentsInformation,
                              'idx_is_private')
    idx_is_private = is_private

    security.declareProtected(SilvaPermissions.AccessContentsInformation,
                              'parent_path')
    def parent_path(self):
        """Returns the path of the parent of this source
        """
        return '/'.join(self.aq_inner.aq_parent.getPhysicalPath())

    # MANIPULATORS

    security.declareProtected(SilvaPermissions.ChangeSilvaContent,
                              'set_private')
    def set_private(self, on_or_off):
        """
        Sets the is_private-setting for this source.

        is_private can restrict the availability of this source towards the
        outside-world (when set, the source can only be found by
        filters in the same subdirectory)
        """
        self._is_private = on_or_off
        self.reindex_object()

    security.declareProtected(SilvaPermissions.ChangeSilvaContent,
                              'get_fields_for_bulk_editing')
    def get_fields_for_bulk_editing(self, field_keys, objectids,
                                    startpoint=None):
        """
        Creates a dictionary of values for each field in field_keys,
        if the value is None the field should not be shown (the
        objects do not have the field available at all), if it is a
        string containing '__DO_NOT_FILL_FIELD__', the field should be
        created but not filled (some of the objects have the field,
        but the value is different for them) and if the value is
        something else, the field should be filled (some of the
        objects contain the field, and the value is the same for all
        of them (which is the value of the dictionary-item
        """
        if startpoint is None:
            startpoint = self
        versionpaths = []
        fields = {}
        for key in field_keys:
            fields[key] = None

        # walk through the objects, they should be in direct children of this object
        for item in objectids:
            currentobj = getattr(startpoint, item)
            if INewsItem.isImplementedBy(currentobj):
                version = currentobj.get_editable()
                versionpaths.append(currentobj.getPhysicalPath())
                if not version:
                    # no editable version
                    continue
                for key in fields.keys():
                    if hasattr(version, key):
                        value = getattr(version, key)()
                        if fields[key] is None:
                            fields[key] = value
                        elif fields[key] != value:
                            fields[key] = '__DO_NOT_FILL_FIELD__'
            elif currentobj.implements_container() or currentobj.implements_publication():
                # this is a folder, so walk through it...
                morefields, morepaths = self.get_fields_for_bulk_editing(field_keys, currentobj.objectIds(), currentobj)
                versionpaths += morepaths
                for key in morefields.keys():
                    if fields[key] != morefields[key]:
                        if morefields[key] == '__DO_NOT_FILL_FIELD__':
                            fields[key] = '__DO_NOT_FILL_FIELD__'
                        elif morefields[key] is not None and fields[key] is None:
                            fields[key] = morefields[key]
                        elif morefields[key] is not None and fields[key] is not None:
                            fields[key] = '__DO_NOT_FILL_FIELD__'
        return (fields, versionpaths)

InitializeClass(NewsPublication)

###

manage_addNewsPublicationForm = PageTemplateFile(
    "www/newsPublicationAdd", globals(),
    __name__='manage_addNewsPublicationForm')

def manage_addNewsPublication(self, id, title, create_default=1, REQUEST=None):
    """Add a Silva Newssource."""
    if not mangle.Id(self, id).isValid():
        return
    object = NewsPublication(id)
    self._setObject(id, object)
    object = getattr(self, id)
    object.set_title(title)
    add_and_edit(self, id, REQUEST)
    return ''

# Copyright (c) 2002 Infrae. All rights reserved.
# See also LICENSE.txt
# $Revision: 1.13.2.1 $

# Zope
from AccessControl import ClassSecurityInfo
from OFS.SimpleItem import SimpleItem
from Products.PageTemplates.PageTemplateFile import PageTemplateFile
from DateTime import DateTime
from Globals import InitializeClass
from Products.ParsedXML.ParsedXML import ParsedXML

# Silva interfaces
from Products.Silva.interfaces import IVersionedContent
from Products.SilvaNews.interfaces import INewsItem
from Products.SilvaNews.interfaces import IAgendaItem, IAgendaItemVersion

# Silva
from Products.Silva import SilvaPermissions
from Products.Silva.VersionedContent import VersionedContent
from Products.Silva.helpers import add_and_edit
from AgendaItem import AgendaItem, AgendaItemVersion
from Products.Silva import mangle

icon = 'www/agenda_item.png'
addable_priority = 3.8

class PlainAgendaItem (AgendaItem):
    """A News item for events. Includes date and location
       metadata, as well settings for subjects and audiences.
    """
    security = ClassSecurityInfo()

    meta_type = "Silva Agenda Item"

    __implements__ = IAgendaItem, IVersionedContent

InitializeClass(PlainAgendaItem)

class PlainAgendaItemVersion(AgendaItemVersion):
    """Silva News PlainAgendaItemVersion
    """
    security = ClassSecurityInfo()

    meta_type = "Silva Agenda Item Version"

    __implements__ = IAgendaItemVersion

InitializeClass(PlainAgendaItemVersion)

manage_addPlainAgendaItemForm = PageTemplateFile(
    "www/plainAgendaItemAdd", globals(),
    __name__='manage_addPlainAgendaItemForm')

def manage_addPlainAgendaItem(self, id, title, REQUEST=None):
    """Add a News PlainAgendaItem."""
    if not mangle.Id(self, id).isValid():
        return
    object = PlainAgendaItem(id)
    self._setObject(id, object)
    object = getattr(self, id)
    # add first version
    object._setObject('0', PlainAgendaItemVersion('0'))
    object.create_version('0', None, None)
    object.set_title(title)
    add_and_edit(self, id, REQUEST)
    return ''

manage_addPlainAgendaItemVersionForm = PageTemplateFile(
    "www/plainAgendaItemVersionAdd",
    globals() ,
    __name__='manage_addPlainAgendaItemVersionForm')

def manage_addPlainAgendaItemVersion(self, id, REQUEST=None):
    """Add a PlainAgendaItem version."""
    object = PlainAgendaItemVersion(id)
    self._setObject(id, object)
    add_and_edit(self, id, REQUEST)
    return ''

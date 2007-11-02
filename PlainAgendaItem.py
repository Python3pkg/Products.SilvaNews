# Copyright (c) 2002-2007 Infrae. All rights reserved.
# See also LICENSE.txt
# $Revision: 1.16 $

from zope.interface import implements

# Zope
from AccessControl import ClassSecurityInfo
from DateTime import DateTime
from Globals import InitializeClass

# Silva interfaces
from Products.Silva.interfaces import IVersionedContent
from Products.SilvaNews.interfaces import INewsItem
from Products.SilvaNews.interfaces import IAgendaItem, IAgendaItemVersion

# Silva
from Products.Silva import SilvaPermissions
from AgendaItem import AgendaItem, AgendaItemVersion

class PlainAgendaItem (AgendaItem):
    """A News item for events. Includes date and location
       metadata, as well settings for subjects and audiences.
    """
    security = ClassSecurityInfo()

    meta_type = "Silva Agenda Item"

    implements((IAgendaItem, IVersionedContent))

InitializeClass(PlainAgendaItem)

class PlainAgendaItemVersion(AgendaItemVersion):
    """Silva News PlainAgendaItemVersion
    """
    security = ClassSecurityInfo()

    meta_type = "Silva Agenda Item Version"

    implements(IAgendaItemVersion)

InitializeClass(PlainAgendaItemVersion)

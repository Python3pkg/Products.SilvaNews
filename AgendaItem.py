# Copyright (c) 2002-2005 Infrae. All rights reserved.
# See also LICENSE.txt
# $Revision: 1.17.2.1 $

# Zope
from AccessControl import ClassSecurityInfo
from OFS.SimpleItem import SimpleItem
from Products.PageTemplates.PageTemplateFile import PageTemplateFile
from DateTime import DateTime
from Globals import InitializeClass
from Products.ParsedXML.ParsedXML import ParsedXML

# Silva interfaces
from Products.SilvaNews.interfaces import IAgendaItem, IAgendaItemVersion
from Products.SilvaNews.interfaces import INewsItem, INewsItemVersion

# Silva
from Products.Silva import SilvaPermissions
from Products.Silva.VersionedContent import VersionedContent
from Products.Silva.interfaces import IVersionedContent
from Products.Silva.helpers import add_and_edit

# SilvaNews
from NewsItem import NewsItem, NewsItemVersion

class AgendaItem(NewsItem):
    """Base class for agenda items.
    """
    security = ClassSecurityInfo()

    __implements__ = IAgendaItem, IVersionedContent

InitializeClass(AgendaItem)

class AgendaItemVersion(NewsItemVersion):
    """Base class for agenda item versions.
    """
    
    security = ClassSecurityInfo()

    __implements__ = IAgendaItemVersion

    def __init__(self, id):
        AgendaItemVersion.inheritedAttribute('__init__')(self, id)
        self._start_datetime = None
        self._end_datetime = None
        self._location = ''

    # MANIPULATORS
    security.declareProtected(SilvaPermissions.ChangeSilvaContent,
                              'set_start_datetime')
    def set_start_datetime(self, value):
        self._start_datetime = value
        self.reindex_object()

    security.declareProtected(SilvaPermissions.ChangeSilvaContent,
                              'set_end_datetime')
    def set_end_datetime(self, value):
        self._end_datetime = value
        self.reindex_object()

    security.declareProtected(SilvaPermissions.ChangeSilvaContent,
                              'set_location')
    def set_location(self, value):
        self._location = value
        self.reindex_object()

    # ACCESSORS
    security.declareProtected(SilvaPermissions.AccessContentsInformation,
                              'start_datetime')
    def start_datetime(self):
        """Returns the start date/time
        """
        return self._start_datetime


    security.declareProtected(SilvaPermissions.AccessContentsInformation,
                              'idx_start_datetime')
    idx_start_datetime = start_datetime


    security.declareProtected(SilvaPermissions.AccessContentsInformation,
                              'end_datetime')
    def end_datetime(self):
        """Returns the start date/time
        """
        return self._end_datetime

    security.declareProtected(SilvaPermissions.AccessContentsInformation,
                              'idx_end_datetime')
    idx_end_datetime = end_datetime


    security.declareProtected(SilvaPermissions.AccessContentsInformation,
                              'location')
    def location(self):
        """Returns location manual
        """
        return self._location

    security.declareProtected(SilvaPermissions.AccessContentsInformation,
                              'fulltext')
    def fulltext(self):
        """Deliver the contents as plain text, for full-text search
        """
        parenttext = AgendaItemVersion.inheritedAttribute('fulltext')(self)
        return "%s %s" % (parenttext, self._location)

    def content_xml(self, context):
        """Returns the content as a partial XML-doc
        """
        AgendaItemVersion.inheritedAttribute('content_xml')(self, context)
        xml = u'<start_datetime>%s</start_datetime>' % self._prepare_xml(
            self._start_datetime.rfc822())
        xml += u'<location>%s</location>' % self._prepare_xml(
            self._location)

        context.f.write(xml)

InitializeClass(AgendaItemVersion)

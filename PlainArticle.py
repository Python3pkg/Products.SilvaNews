# Copyright (c) 2002 Infrae. All rights reserved.
# See also LICENSE.txt
# $Revision: 1.13 $

# Zope
from AccessControl import ClassSecurityInfo
from OFS.SimpleItem import SimpleItem
from Products.PageTemplates.PageTemplateFile import PageTemplateFile
from DateTime import DateTime
from Globals import InitializeClass
from Products.ZCatalog.CatalogPathAwareness import CatalogPathAware
from Products.ParsedXML.ParsedXML import ParsedXML

# Silva interfaces
from Products.SilvaNews.INewsItem import INewsItem, INewsItemVersion
from Products.Silva.IVersionedContent import IVersionedContent

# Silva
from Products.Silva import SilvaPermissions
from Products.Silva.VersionedContent import VersionedContent
from Products.Silva.helpers import add_and_edit
from Products.SilvaNews.NewsItem import NewsItem, NewsItemVersion

class PlainArticle(NewsItem):
    """A News item that appears as an individual page. By adjusting
       settings the Author can determine which subjects, and
       for which audiences the Article should be presented.
    """
    # Silva News PlainArticle. All the data of the object is defined 
    # on the version, except for publication_datetime (see SuperClass)

    security = ClassSecurityInfo()

    meta_type = "Silva News Article"

    __implements__ = INewsItem, IVersionedContent

InitializeClass(PlainArticle)

class PlainArticleVersion(NewsItemVersion):
    """Silva News PlainArticle version.
    """
    security = ClassSecurityInfo()

    meta_type = "Silva News PlainArticle Version"

    __implements__ = INewsItemVersion

    def __init__(self, id):
        PlainArticleVersion.inheritedAttribute('__init__')(self, id)

    # MANIPULATORS
    # ACCESSORS

InitializeClass(PlainArticleVersion)

manage_addPlainArticleForm = PageTemplateFile(
    "www/plainArticleAdd", globals(),
    __name__='manage_addPlainArticleForm')

def manage_addPlainArticle(self, id, title, REQUEST=None):
    """Add a News PlainArticle."""
    if not self.is_id_valid(id):
        return
    object = PlainArticle(id, title)
    self._setObject(id, object)
    object = getattr(self, id)
    # add first version
    object._setObject('0', PlainArticleVersion('0'))
    object.create_version('0', None, None)
    add_and_edit(self, id, REQUEST)
    return ''

manage_addPlainArticleVersionForm = PageTemplateFile(
    "www/plainArticleVersionAdd",
    globals() ,
    __name__='manage_addPlainArticleVersionForm')

def manage_addPlainArticleVersion(self, id, REQUEST=None):
    """Add a PlainArticle version."""
    object = PlainArticleVersion(id)
    self._setObject(id, object)
    add_and_edit(self, id, REQUEST)
    return ''

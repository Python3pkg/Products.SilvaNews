# Copyright (c) 2002-2008 Infrae. All rights reserved.
# See also LICENSE.txt
# $Revision: 1.18 $

from zope.interface import implements

# Zope
from AccessControl import ClassSecurityInfo
from DateTime import DateTime
try:
    from App.class_init import InitializeClass # Zope 2.12
except ImportError:
    from Globals import InitializeClass # Zope < 2.12

# Silva
from silva.core import conf as silvaconf
from Products.Silva import SilvaPermissions

# Silva
from Products.SilvaNews.NewsItem import NewsItem, NewsItemVersion
from Products.SilvaNews.interfaces import INewsItem, INewsItemVersion

class PlainArticleVersion(NewsItemVersion):
    """Silva News PlainArticle version.
    """
    security = ClassSecurityInfo()

    meta_type = "Silva Article Version"

    implements(INewsItemVersion)

    def __init__(self, id):
        PlainArticleVersion.inheritedAttribute('__init__')(self, id)

InitializeClass(PlainArticleVersion)

class PlainArticle(NewsItem):
    """A News item that appears as an individual page. By adjusting
       settings the Author can determine which subjects, and
       for which audiences the Article should be presented.
    """
    # Silva News PlainArticle. All the data of the object is defined 
    # on the version, except for publication_datetime (see SuperClass)

    security = ClassSecurityInfo()

    implements(INewsItem)
    meta_type = "Silva Article"
    silvaconf.icon("www/news_item.png")
    silvaconf.priority(3.7)
    silvaconf.versionClass(PlainArticleVersion)
InitializeClass(PlainArticle)

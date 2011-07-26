# Copyright (c) 2002-2011 Infrae. All rights reserved.
# See also LICENSE.txt
# $Id$

# Zope
from AccessControl import ClassSecurityInfo
from App.class_init import InitializeClass

# Silva News
from Products.SilvaNews.NewsItem import NewsItem, NewsItemVersion
from Products.SilvaNews.interfaces import INewsItem
from Products.SilvaNews.interfaces import (
    subjects_source, target_audiences_source)

# Silva
from five import grok
from silva.core import conf as silvaconf
from silva.core.conf.interfaces import ITitledContent
from zeam.form import silva as silvaforms
from zope import interface, schema
from zope.i18nmessageid import MessageFactory

_ = MessageFactory('silva_news')


class PlainArticleVersion(NewsItemVersion):
    """Silva News PlainArticle version.
    """
    security = ClassSecurityInfo()
    meta_type = "Silva Article Version"


InitializeClass(PlainArticleVersion)


class PlainArticle(NewsItem):
    """A News item that appears as an individual page. By adjusting
       settings the Author can determine which subjects, and
       for which audiences the Article should be presented.
    """
    # Silva News PlainArticle. All the data of the object is defined
    # on the version, except for publication_datetime (see SuperClass)

    security = ClassSecurityInfo()
    meta_type = "Silva Article"
    silvaconf.icon("www/news_item.png")
    silvaconf.priority(3.7)
    silvaconf.versionClass(PlainArticleVersion)


InitializeClass(PlainArticle)


class IArticleSchema(interface.Interface):
    subjects = schema.Set(
        title=_(u"subjects"),
        value_type=schema.Choice(source=subjects_source),
        required=True)
    target_audiences = schema.Set(
        title=_(u"target audiences"),
        value_type=schema.Choice(source=target_audiences_source),
        required=True)


class ArticleAddForm(silvaforms.SMIAddForm):
    grok.context(INewsItem)
    grok.name(u"Silva Article")

    fields = silvaforms.Fields(ITitledContent, IArticleSchema)


class ArticleEditProperties(silvaforms.RESTKupuEditProperties):
    grok.context(INewsItem)

    label = _(u"article properties")
    fields = silvaforms.Fields(IArticleSchema)
    actions = silvaforms.Actions(silvaforms.EditAction())

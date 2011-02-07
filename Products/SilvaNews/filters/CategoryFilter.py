# Copyright (c) 2002-2011 Infrae. All rights reserved.
# See also LICENSE.txt
# $Id$


# Zope
from AccessControl import ClassSecurityInfo
from App.class_init import InitializeClass # Zope 2.12

# Silva
from five import grok
from silva.core import conf as silvaconf
from silva.core.conf.interfaces import ITitledContent
from zeam.form import silva as silvaforms
from zope.i18nmessageid import MessageFactory

# SilvaNews
from Products.SilvaNews.ServiceNews import CategoryMixin
from Products.SilvaNews.filters.Filter import Filter
from Products.SilvaNews.interfaces import (ICategoryFilter)


_ = MessageFactory('silva_news')


class CategoryFilter(Filter, CategoryMixin):
    """A Category Filter is useful in large sites where the news articles have
       (too) many subjects and target audiences defined. The Filter will limit
       those that display so only the appropriate ones for that area of the
       site appear.
    """

    security = ClassSecurityInfo()

    meta_type = "Silva News Category Filter"
    grok.implements(ICategoryFilter)
    silvaconf.icon("www/category_filter.png")
    silvaconf.priority(3.6)


InitializeClass(CategoryFilter)


class ICategoryFilterSchema(ITitledContent):
    pass


class CategoryFilterAddForm(silvaforms.SMIAddForm):
    grok.context(ICategoryFilter)
    grok.name(u'Silva News Category Filter')

    fields = silvaforms.Fields(ICategoryFilterSchema)

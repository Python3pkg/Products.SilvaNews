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

from zope.schema.interfaces import IContextSourceBinder
from zope.schema.vocabulary import SimpleVocabulary, SimpleTerm
from zope import schema
from zope.interface import Interface
from Acquisition import aq_parent
from Products.SilvaNews.widgets.tree import Tree
from Products.SilvaNews.interfaces import (subjects_source,
                                           target_audiences_source,
                                           get_subjects_tree,
                                           get_target_audiences_tree)

@grok.provider(IContextSourceBinder)
def filter_subjects_source(context):
    return subjects_source(aq_parent(context.get_container()))

@grok.provider(IContextSourceBinder)
def filter_target_audiences_source(context):
    """Category Filters need to get the filters from the container above
       where the filter resides, so as to prevent a self-referential filtering
       situation (i.e. the edit screen shows only the categories this filter
       is configured to show, preventing adding more categories, so we need
       to go one level above the container"""
    return target_audiences_source(aq_parent(context.get_container()))

class ICategorySchema(Interface):
    subjects = Tree(
        title=_(u"subjects"),
        description=_(
            u'Select the news subjects to filter on. '
            u'Only those selected will appear in this area of the site. '
            u'Select nothing to have all show up.'),
        value_type=schema.Choice(source=filter_subjects_source),
        tree=get_subjects_tree,
        required=True)
    target_audiences = Tree(
        title=_(u"target audiences"),
        description=_(u'Select the target audiences to filter on.'),
        value_type=schema.Choice(source=filter_target_audiences_source),
        tree=get_target_audiences_tree,
        required=True)

class CategoryFilterEditForm(silvaforms.SMIEditForm):
    """ edit form for category filters """
    grok.context(ICategoryFilter)
    fields = silvaforms.Fields(ICategorySchema)


class CategoryFilterAddForm(silvaforms.SMIAddForm):
    grok.context(ICategoryFilter)
    grok.name(u'Silva News Category Filter')

    fields = silvaforms.Fields(ITitledContent, ICategorySchema)

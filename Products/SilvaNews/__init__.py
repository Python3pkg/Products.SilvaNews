# Copyright (c) 2004-2011 Infrae. All rights reserved.
# See also LICENSE.txt
# $Id$

from Products.SilvaNews.installer import install

from silva.core import conf as silvaconf

silvaconf.extension_name("SilvaNews")
silvaconf.extension_title("Silva News Network")
silvaconf.extension_depends(["SilvaDocument", "SilvaExternalSources"])


def initialize(context):
    from Products.SilvaNews import indexing
    context.registerClass(
        indexing.IntegerRangesIndex,
        permission = 'Add Pluggable Index',
        constructors = (indexing.manage_addIntegerRangesIndexForm,
                        indexing.manage_addIntegerRangesIndex),
        visibility=None)


# Specify import path for old classes (for upgrade)
CLASS_CHANGES = {
        'Products.SilvaNews.silvaxmlattribute SilvaXMLAttribute':
            'OFS.SimpleItem SimpleItem',

        # filters

        'Products.SilvaNews.AgendaFilter AgendaFilter':
            'Products.SilvaNews.filters.AgendaFilter AgendaFilter',
        'Products.SilvaNews.CategoryFilter CategoryFilter':
            'Products.SilvaNews.filters.CategoryFilter CategoryFilter',
        'Products.SilvaNews.Filter Filter':
            'Products.SilvaNews.filters.Filter Filter',
        'Products.SilvaNews.NewsFilter NewsFilter':
            'Products.SilvaNews.filters.NewsFilter NewsFilter',
        'Products.SilvaNews.NewsItemFilter NewsItemFilter':
            'Products.SilvaNews.filters.NewsItemFilter NewsItemFilter',

        # viewers

        'Products.SilvaNews.AgendaViewer AgendaViewer':
            'Products.SilvaNews.viewers.AgendaViewer AgendaViewer',
        'Products.SilvaNews.NewsViewer NewsViewer':
            'Products.SilvaNews.viewers.NewsViewer NewsViewer',
        'Products.SilvaNews.RSSAggregator RSSAggregator':
            'Products.SilvaNews.viewers.RSSAggregator RSSAggregator',
    }


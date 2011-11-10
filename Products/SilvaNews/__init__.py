# Copyright (c) 2004-2010 Infrae. All rights reserved.
# See also LICENSE.txt
# $Id$

from Products.SilvaNews.installer import install

from silva.core import conf as silvaconf

silvaconf.extension_name("SilvaNews")
silvaconf.extension_title("Silva Obsolete News Network")
silvaconf.extension_depends(["Silva", "SilvaDocument", "SilvaExternalSources"])


# Specify import path for old classes (for upgrade)
CLASS_CHANGES = {
    'Products.SilvaNews.PlainAgendaItem PlainAgendaItem':
        'Products.SilvaNews.AgendaItem AgendaItem',
    'Products.SilvaNews.PlainAgendaItem PlainAgendaItemVersion':
        'Products.SilvaNews.AgendaItem AgendaItemVersion',
    'Products.SilvaNews.PlainArticle PlainArticle':
        'Products.SilvaNews.NewsItem NewsItem',
    'Products.SilvaNews.PlainArticle PlainArticleVersion':
        'Products.SilvaNews.NewsItem NewsItemVersion',

    'Products.SilvaNews.indexing IntegerRangesIndex':
        'silva.app.news.indexing IntegerRangesIndex',

    'Products.SilvaNews.InlineViewer InlineViewer':
        'Products.SilvaExternalSources.CodeSource CodeSource',

    'Products.SilvaNews.AgendaItem.AgendaItemOccurrence':
        'silva.app.news.AgendaItem.content AgendaItemOccurrence',

    'Products.SilvaNews.viewers.RSSAggregator RSSAggregator':
        'silva.app.news.viewers.RSSAggregator RSSAggregator',
    'Products.SilvaNews.viewers.NewsViewer NewsViewer':
        'silva.app.news.viewers.NewsViewer NewsViewer',
    'Products.SilvaNews.viewers.AgendaViewer AgendaViewer':
        'silva.app.news.viewers.AgendaViewer AgendaViewer',

    'Products.SilvaNews.NewsPublication NewsPublication':
        'silva.app.news.NewsPublication NewsPublication',

    'Products.SilvaNews.ServiceNews ServiceNews':
        'silva.app.news.ServiceNews ServiceNews',
    'Products.SilvaNews.interfaces IServiceNews':
        'silva.app.news.interfaces IServiceNews',
    'Products.SilvaNews.Tree Root':
        'silva.app.news.Tree Root',
    'Products.SilvaNews.Tree Node':
        'silva.app.news.Tree Node',

    'Products.SilvaNews.filters.AgendaFilter AgendaFilter':
        'silva.app.news.filters.AgendaFilter AgendaFilter',
    'Products.SilvaNews.filters.NewsFilter NewsFilter':
        'silva.app.news.filters.NewsFilter NewsFilter',
    'Products.SilvaNews.filters.CategoryFilter CategoryFilter':
        'silva.app.news.filters.CategoryFilter CategoryFilter',
    }


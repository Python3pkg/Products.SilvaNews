# Copyright (c) 2002 Infrae. All rights reserved.
# See also LICENSE.txt
# $Revision: 1.16.2.1 $

import AgendaFilter, NewsFilter, ServiceNews, InlineViewer
import NewsPublication, NewsViewer, AgendaViewer, RSSAggregator
import PlainArticle, PlainAgendaItem

from Products.FileSystemSite.DirectoryView import registerDirectory
from Products.Silva.ExtensionRegistry import extensionRegistry
#from Products.Silva.upgrade import upgrade_registry
from Products.SilvaMetadata.Compatibility import registerTypeForMetadata
import install

def initialize(context):

    extensionRegistry.register(
        'SilvaNews', 'Silva News', context,
        [NewsPublication,
         NewsFilter, NewsViewer, PlainArticle,
         AgendaFilter, AgendaViewer, PlainAgendaItem,
         RSSAggregator],
        install, depends_on='SilvaDocument')

    context.registerClass(
        InlineViewer.InlineViewer,
        constructors = (InlineViewer.manage_addInlineViewerForm,
                        InlineViewer.manage_addInlineViewer),
        icon="www/newsservice.gif"
        )

    context.registerClass(
        ServiceNews.ServiceNews,
        constructors = (ServiceNews.manage_addServiceNewsForm,
                        ServiceNews.manage_addServiceNews),
        icon="www/newsservice.gif"
        )

    registerDirectory('views', globals())

    # metadata
    for obj in [
        NewsPublication.NewsPublication,
        NewsFilter.NewsFilter, NewsViewer.NewsViewer,
        PlainArticle.PlainArticleVersion,
        AgendaFilter.AgendaFilter, AgendaViewer.AgendaViewer,
        PlainAgendaItem.PlainAgendaItemVersion,
        RSSAggregator.RSSAggregator,
        ]:
        registerTypeForMetadata(getattr(obj, 'meta_type'))
    
# upgrade methods
#def upgrade_newsitem(obj):
#    pass

#upgrade_registry.register('Silva News Article', upgrade_newsitem)
#upgrade_registry.register('Silva News AgendaItem', upgrade_newsitem)

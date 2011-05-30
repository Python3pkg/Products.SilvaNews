from five import grok
from zope.publisher.interfaces.browser import IBrowserRequest

from Products.SilvaNews.interfaces import IAgendaItem

try:
    from bethel.core.sitemap.adapters.interfaces import ISiteMapper
    from bethel.core.sitemap.adapters.sitemappers import SilvaObjectSiteMapper
    class AgendaItemSiteMapper(SilvaObjectSiteMapper, grok.MultiAdapter):
        grok.provides(ISiteMapper)
        grok.adapts(IAgendaItem, IBrowserRequest)
        grok.name(u"")
        """never include agenda items in the sitemap"""
        def includeInSitemap(self):
            return False
except ImportError:
    pass # do nothing

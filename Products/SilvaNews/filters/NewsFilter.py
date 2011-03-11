# Copyright (c) 2002-2011 Infrae. All rights reserved.
# See also LICENSE.txt
# $Revision$

from zope import schema
from zope.i18nmessageid import MessageFactory

# Zope
from AccessControl import ClassSecurityInfo
from App.class_init import InitializeClass

# SilvaNews
from Products.SilvaNews.interfaces import INewsFilter, ISubjectTASchema
from Products.SilvaNews.filters.NewsItemFilter import NewsItemFilter


from Products.Silva import SilvaPermissions
from five import grok
from silva.core import conf as silvaconf
from zeam.form import silva as silvaforms

from Products.SilvaNews.interfaces import news_source

_ = MessageFactory('silva_news')


class NewsFilter(NewsItemFilter):
    """To enable editors to channel newsitems on a site, all items
        are passed from NewsFolder to NewsViewer through filters. On a filter
        you can choose which NewsFolders you want to channel items for and
        filter the items on several criteria (as well as individually).
    """
    security = ClassSecurityInfo()

    meta_type = "Silva News Filter"
    grok.implements(INewsFilter)
    silvaconf.icon("www/news_filter.png")
    silvaconf.priority(3.2)

    _article_meta_types = ['Silva Article Version']
    _agenda_item_meta_types = ['Silva Agenda Item Version']

    def __init__(self, id):
        super(NewsFilter, self).__init__(id)
        self._show_agenda_items = 0

    # ACCESSORS

    security.declareProtected(SilvaPermissions.AccessContentsInformation,
                              'get_all_items')
    def get_all_items(self, meta_types=None):
        """
        Returns all items available to this filter. This function will
        probably only be used in the back-end, but nevertheless has
        AccessContentsInformation-security because it does not reveal
        any 'secret' information...
        """
        if not self.get_sources():
            return []
        query = self._prepare_query(meta_types)
        results = self._query(**query)
        return results
    
    
    security.declareProtected(SilvaPermissions.AccessContentsInformation,
                              'get_items_by_userid')
    def get_items_by_userid(self, userid, meta_types=None):
        """Returns all items available to this filter that were authored by
        the given userid. This is an extension of get_all_items().
        """
        if not userid:
            return []
        if not self._sources:
            return []
        query = self._prepare_query(meta_types)
        query['sec_get_last_author_userid'] = userid
        results = self._query(**query)
        return results

    def _get_items_in_range(self, startdate, enddate, meta_types=None):
        #XXX where is this used?  SilvaNewsCalendar?
        query = self._prepare_query(meta_types)
        query['idx_display_datetime'] = {'query': [startdate, enddate],
                                         'range': 'minmax'}
        result = self._query(**query)
 
        for r in result:
            if not r.object_path in self._excluded_items:
                yield r

    security.declarePrivate('get_allowed_meta_types')
    def get_allowed_meta_types(self):
        """Returns the allowed meta_types for this filter"""
        allowed = self._article_meta_types[:]
        if self.show_agenda_items():
            allowed += self._agenda_item_meta_types[:]
        return allowed

    # MANIPULATORS

    security.declareProtected(SilvaPermissions.AccessContentsInformation,
                              'show_agenda_items')
    def show_agenda_items(self):
        return self._show_agenda_items

    security.declareProtected(SilvaPermissions.ChangeSilvaContent,
                              'set_show_agenda_items')
    def set_show_agenda_items(self, value):
        self._show_agenda_items = not not int(value)


InitializeClass(NewsFilter)


class NewsFilterAddForm(silvaforms.SMIAddForm):
    grok.context(INewsFilter)
    grok.name(u'Silva News Filter')


class INewsFilterSchema(ISubjectTASchema):
    _keep_to_path = schema.Bool(
        title=_(u"stick to path"))

    _show_agenda_items = schema.Bool(
        title=_(u"show agenda items"))

    sources = schema.Set(
        value_type=schema.Choice(source=news_source),
        title=_(u"sources"),
        description=_(u"Use predefined sources."))


class NewsFilterEditForm(silvaforms.SMIEditForm):
    """ Base form for filters """
    grok.context(INewsFilter)
    fields = silvaforms.Fields(INewsFilterSchema)

# Copyright (c) 2002-2011 Infrae. All rights reserved.
# See also LICENSE.txt
# $Revision: 1.34 $

from logging import getLogger

from five import grok
from zope.component import getUtility, getMultiAdapter
from zope.schema.interfaces import IContextSourceBinder
from zope.schema.vocabulary import SimpleVocabulary, SimpleTerm
from zope import schema
from zope.interface import Interface

# Zope
from AccessControl import ClassSecurityInfo
from App.class_init import InitializeClass
from datetime import datetime
from OFS.SimpleItem import SimpleItem

# Silva
from Products.Silva import SilvaPermissions
from Products.Silva.Content import Content
from silva.core import conf as silvaconf
from silva.core.services.interfaces import ICatalogService
from silva.core.views import views as silvaviews
from zeam.form import silva as silvaforms
from zeam.utils.batch import batch
from zeam.utils.batch.interfaces import IBatching

from zope.i18nmessageid import MessageFactory
_ = MessageFactory('silva_news')

from silva.core.references.reference import ReferenceSet


# SilvaNews
from Products.SilvaNews.interfaces import (INewsViewer, IServiceNews,
    show_source, timezone_source, week_days_source, filters_source,
    IAgendsViewer)
from Products.SilvaNews.ServiceNews import TimezoneMixin
from Products.SilvaNews.traverser import set_parent
from BTrees.OOBTree import OOBTree
import bisect

logger = getLogger('Products.SilvaNews.NewsViewer')


class NewsViewer(Content, SimpleItem, TimezoneMixin):
    """Used to show news items on a Silva site.

    When setting up a newsviewer you can choose which news- or
    agendafilters it should use to retrieve the items, and how far
    back in time it should go. The items will then be automatically
    fetched via the filter for each page request.
    """

    meta_type = 'Silva News Viewer'
    grok.implements(INewsViewer)
    silvaconf.icon("www/news_viewer.png")
    silvaconf.priority(3.1)

    filter_meta_types = ['Silva News Filter',
                         'Silva Agenda Filter',
                         'Silva iCalendar Filter']

    _filter_reference_name = u'viewer-filter'

    _number_to_show = 25
    _number_to_show_archive = 10
    _number_is_days = 0
    _year_range = 2

    # define wether the items are displayed sub elements of the viewer
    _proxy = False

    security = ClassSecurityInfo()

    security.declareProtected(SilvaPermissions.AccessContentsInformation,
                              'default_timezone')
    def default_timezone(self):
        """ this is an override of TimezoneMixin to make the service news
        to decide the default timezone
        """
        service_news = getUtility(IServiceNews)
        return service_news.get_timezone()

    security.declareProtected(SilvaPermissions.AccessContentsInformation,
                              'default_timezone_name')
    def default_timezone_name(self):
        service_news = getUtility(IServiceNews)
        return service_news.get_timezone_name()

    security.declareProtected(SilvaPermissions.AccessContentsInformation,
                              'get_first_weekday')
    def get_first_weekday(self):
        first_weekday = getattr(self, '_first_weekday', None)
        if first_weekday is None:
            return getUtility(IServiceNews).get_first_weekday()
        return first_weekday

    security.declareProtected(SilvaPermissions.AccessContentsInformation,
                              'year_range')
    def year_range(self):
        """Returns number of items to show
        """
        if not hasattr(self, '_year_range'):
            self._year_range = 2
        return self._year_range

    security.declareProtected(SilvaPermissions.AccessContentsInformation,
                              'get_year_range')
    get_year_range = year_range

    security.declareProtected(SilvaPermissions.AccessContentsInformation,
                              'number_to_show')
    def number_to_show(self):
        """Returns number of items to show
        """
        return self._number_to_show

    security.declareProtected(SilvaPermissions.AccessContentsInformation,
                              'get_number_to_show')
    get_number_to_show = number_to_show

    security.declareProtected(SilvaPermissions.AccessContentsInformation,
                                'number_to_show_archive')
    def number_to_show_archive(self):
        """returns the number of items to show per page in the archive"""
        return self._number_to_show_archive

    get_number_to_show_archive = number_to_show_archive

    security.declareProtected(SilvaPermissions.AccessContentsInformation,
                              'is_published')
    def is_published(self):
        """Returns 1 so the object will be shown in TOCs and such"""
        return 1

    security.declareProtected(SilvaPermissions.AccessContentsInformation,
                              'is_deletable')
    def is_deletable(self):
        """return 1 so this object can always be deleted"""
        return 1

    security.declareProtected(SilvaPermissions.AccessContentsInformation,
                              'can_set_title')
    def can_set_title(self):
        """return 1 so the title can be set"""
        return 1

    security.declareProtected(SilvaPermissions.AccessContentsInformation,
                              'number_is_days')
    def number_is_days(self):
        """
        Returns the value of number_is_days (which controls whether
        the filter should show <n> items or items of <n> days back)
        """
        return self._number_is_days

    security.declareProtected(SilvaPermissions.AccessContentsInformation,
                              'get_number_is_days')
    get_number_is_days = number_is_days

    def _get_filters_reference_set(self):
        if hasattr(self, '_v_filter_reference_set'):
            refset = getattr(self, '_v_filter_reference_set', None)
            if refset is not None:
                return refset
        self._v_filter_reference_set = ReferenceSet(self, 'filters')
        return self._v_filter_reference_set

    security.declareProtected(SilvaPermissions.AccessContentsInformation,
                              'get_filters')
    def get_filters(self):
        """Returns a list of all filters of this object
        """
        return list(self._get_filters_reference_set())

    security.declareProtected(SilvaPermissions.AccessContentsInformation,
                              'has_filter')
    def has_filter(self):
        """Returns a list of (the path to) all filters of this object
        """
        gen = list(self._get_filters_reference_set().get_references())
        return len(gen) > 0

    security.declareProtected(SilvaPermissions.AccessContentsInformation,
                              'get_all_filters')
    def get_all_filters(self):
        util = getUtility(ICatalogService)
        query = {}
        query['meta_type'] = {
            'operator': 'or',
            'query': self.filter_meta_types}
        return [brain.getObject() for brain in util(query)]

    def _get_items_helper(self, func, sortattr=None, nogenerator=True):
        #1) helper function for get_items...this was the same
        #code in NV and AV.  Now this helper contains that code
        #and calls func(obj) for each filter to actually
        #get the items.  Func can be a simple lamba: function
        #2) sortattr is an attribute of the CatalogBraings objects
        #   i.e. a result item.  It's a catalog metadata column
        #   use it for fast sort / merging of multiple filters
        #   e.g. on display_datetime or start_datetime
        results = OOBTree()
        for newsfilter in self._get_filters_reference_set():
            try:  #now that verify_filters caches for 5 minutes, it's possible
                  # (however slight) that this will fail
                obj = self.aq_inner.restrictedTraverse(newsfilter)
            except:
                continue
            for result in func(obj):
                results[result.silva_object_url] = result
                
            #now use bisect to insert the items in a sorted manner
            sortedresults = []
            for r in results.itervalues():
                #Why do we also add r.silva_object_url?  Because for some reason, comparing
                # mybrains sometimes raises an error that you can't compare a mybrains
                # with an implicitacquirerwrapper.  So, silva_object_url is meant as
                # a quickly-findable unique value
                bisect.insort_right(sortedresults,(getattr(r,sortattr,None),r.silva_object_url,r))
            #events should be ordered oldest first
            # (i.e. it's happening sooner)
            #news should be ordered newest first
            # and so sortedresults should be reversed
            if not IAgendaViewer.providedBy(self):
                sortedresults.reverse()
            if no_generator:
                return [ r[2] for r in sortedresults ]
            else:
                def make_generator(l):
                    for item in l:
                        yield item[2]
                return make_generator(sortedresults)
        else:
            if no_generator:
                return results.values()
            else:
                return results.itervalues()

    security.declareProtected(SilvaPermissions.AccessContentsInformation,
                              'get_items')
    def get_items(self, number=None, number_is_days=None):
        """Gets the items from the filters
        """
        func = lambda x: x.get_last_items(number or self._number_to_show,
                                          number_is_days or self._number_is_days)
        #merge/sort results if > 1 filter
        sortattr = None
        if self.has_filter():
            sortattr = 'display_datetime'
        results = self._get_items_helper(func,'display_datetime')

        if not self._number_is_days:
            return results[:self._number_to_show]

        return results

    security.declareProtected(SilvaPermissions.AccessContentsInformation,
                              'get_items_from_date')
    def get_items_from_date(self,date=None, sortattr='display_datetime'):
        """Gets the items from the filters, like get_items only
           starts at a specific date
        """
        #XXX aaltepet: where is this used?
        if not date:
            date = DateTime()
            
        func = lambda x: x.get_last_items_from_date(self._number_to_show,
                                                    date,
                                                    self._number_is_days)
        results = self._get_items_helper(func,sortattr)

        if sortattr:
            results = [ (getattr(r,sortattr,None),getattr(r,'object_path',None),r) for r in results ]
            results.sort()
            results = [ r[2] for r in results ]
            results.reverse()
        return results
 
    def get_items_by_month_datetime(self, datetime):
        """ gets the items from the filters by date, given a zope DateTime"""
        return self.get_items_by_date(datetime.month(), datetime.year())


    security.declareProtected(SilvaPermissions.AccessContentsInformation,
                              'get_items_by_date')
    def get_items_by_date(self, month, year):
        """Gets the items from the filters
        """
        func = lambda x: x.get_items_by_date(month,year,
            timezone=self.get_timezone())
        sortattr = None
        if self.has_filter():
            sortattr = 'sort_index'
        return self._get_items_helper(func,sortattr)

    security.declareProtected(SilvaPermissions.AccessContentsInformation,
                              'get_items_for_year')
    def get_items_for_year(self, year, sortattr='display_datetime'):
        #year is a number
        # returns all items for the given year.  sortattr is an attribute
        # that is a metadata column, not a zcatalog index.
        start = DateTime(year,1,1).earliestTime()
        end = (start+364).latestTime()
        func = lambda x: x._get_items_in_range(start,end)
        return self._get_items_helper(func,sortattr,no_generator=False)


    security.declareProtected(SilvaPermissions.AccessContentsInformation,
                              'get_items_by_date_range')
    def get_items_by_date_range(self, start, end):
        """Gets the items from the filters
        """
        func = lambda x: x.get_items_by_date_range(start, end)
        sortattr = None
        if self.has_filter():
            sortattr = 'sort_index'
        return self._get_items_helper(func, sortattr)

    security.declareProtected(SilvaPermissions.AccessContentsInformation,
                              'search_items')
    def search_items(self, keywords):
        """Search the items in the filters
        """
        func = lambda x: x.search_items(keywords)
        sortattr = None
        if self.has_filter():
            sortattr = 'sort_index'
        return self._get_items_helper(func,sortattr)

    # MANIPULATORS

    security.declareProtected(SilvaPermissions.ChangeSilvaContent,
                              'set_year_range')
    def set_year_range(self, number):
        """Sets the range of years to show links to
        """
        self._year_range = number

    security.declareProtected(SilvaPermissions.ChangeSilvaContent,
                              'set_number_to_show')
    def set_number_to_show(self, number):
        """Sets the number of items to show
        """
        self._number_to_show = number

    security.declareProtected(SilvaPermissions.ChangeSilvaContent,
                                'set_number_to_show_archive')
    def set_number_to_show_archive(self, number):
        """set self._number_to_show_archive"""
        self._number_to_show_archive = number

    security.declareProtected(SilvaPermissions.ChangeSilvaContent,
                              'set_number_is_days')
    def set_number_is_days(self, onoff):
        """Sets the number of items to show
        """
        self._number_is_days = int(onoff)

    security.declareProtected(SilvaPermissions.ChangeSilvaContent,
                              'set_filters')
    def set_filters(self, filters):
        """update filters
        """
        self._get_filters_reference_set().set(filters)

    security.declareProtected(SilvaPermissions.ChangeSilvaContent,
                              'add_filter')
    def add_filter(self, filter):
        """add filters
        """
        self._get_filters_reference_set().add(filter)
        return filter

    security.declareProtected(SilvaPermissions.AccessContentsInformation,
                              'allow_feeds')
    def allow_feeds(self):
        return True

    security.declareProtected(SilvaPermissions.AccessContentsInformation,
                              'allow_feeds')
    def set_proxy(self, item, force=False):
        """ Set the viewer as parent of the item if it is configured to or
        is force flag is set.
        """
        if force or self._proxy:
            return set_parent(self, item)
        return item


InitializeClass(NewsViewer)


class INewsViewerSchema(Interface):
    """ Fields description for use in forms only
    """
    number_is_days = schema.Choice(
        source=show_source,
        title=_(u"show"),
        description=_(u"Show a specific number of items, or show "
                      u"items from a range of days in the past."),
        required=True)

    number_to_show = schema.Int(
        title=_(u"days / items number"),
        description=_(u"Number of news items to show per page."),
        required=True)

    number_to_show_archive = schema.Int(
        title=_(u"archive number"),
        description=_(u"Number of archive items to show per page."),
        required=True)

    year_range = schema.Int(
        title=_(u"year range"),
        description=_(u"Allow navigation this number of years ahead "
                      u"of / behind today."),
        required=True)

    timezone_name = schema.Choice(
        source=timezone_source,
        title=_(u"timezone"),
        description=_(u"Defines the time zone for the agenda and news "
                      u"items that will be rendered by this viewer."),
        required=True)

    _proxy = schema.Bool(
        title=_(u"proxy mode"),
        description=_(u"When proxy mode is enabled items of the viewers are "
                      u"displayed as children of the viewer"),
        required=False,
        default=False)

    first_weekday = schema.Choice(
        title=_(u"first day of the week"),
        source=week_days_source,
        description=_(u"Define first day of the week for calendar display."),
        required=True)

    filters = schema.Set(
        value_type=schema.Choice(source=filters_source),
        title=_(u"filters"),
        description=_(u"Use predefined filters."))


class NewsViewerAddForm(silvaforms.SMIAddForm):
    """Add form news viewer
    """
    grok.context(INewsViewer)
    grok.name('Silva News Viewer')


class NewsViewerEditForm(silvaforms.SMIEditForm):
    """ Edit form for news viewer
    """
    grok.context(INewsViewer)
    fields = silvaforms.Fields(INewsViewerSchema)
    fields['number_is_days'].mode = u'radio'


class NewsViewerListView(object):

    def _set_parent(self, item):
        """ Change the parent of the NewsItem so traversing is made trough
        the news viewer
        """
        version = item.getObject()
        content = version.get_content()
        return self.context.set_proxy(content)


class NewsViewerView(silvaviews.View, NewsViewerListView):
    """ Default view for news viewer
    """
    grok.context(INewsViewer)

    @property
    def archive_url(self):
        return self.url('archives')

    @property
    def search_url(self):
        return self.url('search')

    def update(self):
        self.request.timezone = self.context.get_timezone()
        self.results = map(self._set_parent, self.context.get_items())


class NewsViewerSearchView(silvaviews.Page, NewsViewerListView):
    """ Search view for news viewer
    """
    grok.context(INewsViewer)
    grok.name('search')

    def update(self):
        self.request.timezone = self.context.get_timezone()
        self.query = self.request.get('query', '')
        self.results = []
        try:
            self.results = map(self._set_parent,
                               self.context.search_items(self.query) or [])
        except:
            pass


@grok.provider(IContextSourceBinder)
def monthes(context):
    month_list = []
    service_news = getUtility(IServiceNews)
    for m, month in enumerate(service_news.get_month_abbrs()):
        month_list.append(
            SimpleTerm(value=m+1, token=str(m+1), title=month))
    return SimpleVocabulary(month_list)

@grok.provider(IContextSourceBinder)
def years(context):
    year = datetime.now(context.get_timezone()).year
    year_list = []
    for y in range(year - context.get_year_range(), year + 1):
        year_list.append(SimpleTerm(value=y, token=str(y), title=str(y)))
    return SimpleVocabulary(year_list)


class IArchiveForm(Interface):
    year = schema.Choice(
        title=_(u"year"),
        source=years,
        required=False)
    month = schema.Choice(
        title=_(u"month"),
        source=monthes,
        required=False)


def current_month(form):
    return datetime.now(form.context.get_timezone()).month

def current_year(form):
    return datetime.now(form.context.get_timezone()).year


class NewsViewerArchivesView(silvaforms.PublicForm, NewsViewerListView):
    """ Archives view
    """
    grok.context(INewsViewer)
    grok.name('archives')

    postOnly = False
    ignoreContent = True
    ignoreRequest = False

    fields = silvaforms.Fields(IArchiveForm)
    fields['month'].defaultValue = current_month
    fields['year'].defaultValue = current_year

    @silvaforms.action(_(u'go'), identifier='update')
    def go(self):
        data, errors = self.extractData()
        if len(errors) > 0:
            self.results = []
        else:
            self.results = self.context.get_items_by_date(
                data.getWithDefault('month'),
                data.getWithDefault('year'))
            self.results = map(self._set_parent, self.results)
        self.items = batch(
            self.results,
            request=self.request,
            count=self.context.number_to_show_archive())
        self.batch = getMultiAdapter(
            (self, self.items, self.request), IBatching)

    def update(self):
        self.request.timezone = self.context.get_timezone()
        # always execute action
        self.request.form['form.action.update'] = '1'



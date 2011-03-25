# Copyright (c) 2002-2011 Infrae. All rights reserved.
# See also LICENSE.txt
# $Id$

from five import grok
from zope.interface import Interface, invariant, Invalid
from zope.component import getUtility
from zope.intid.interfaces import IIntIds
from zope.schema.interfaces import IContextSourceBinder
from zope.schema.vocabulary import SimpleVocabulary, SimpleTerm
from zope import schema

from silva.core.interfaces import (IAsset, ISilvaService, IPublication, IContent,
                                   IContentLayout, IVersionedContentLayout,
                                   IVersion)
from silva.core.contentlayout.templates.interfaces import ITemplate

from Products.SilvaExternalSources.interfaces import IExternalSource
from Products.SilvaNews.datetimeutils import zone_names

from zope.i18nmessageid import MessageFactory
_ = MessageFactory('silva_news')

class IInlineViewer(IExternalSource):
    """Marker interface for Inline News Viewer"""

class ISilvaNewsExtension(Interface):
    """Marker interface for SNN Extension"""

class INewsItem(IVersionedContentLayout):
    """Silva News Item interface
    """

@grok.provider(IContextSourceBinder)
def subjects_source(context):
    service = getUtility(IServiceNews)
    result = []
    for value, title, depth in service.filtered_subject_tree(context):
        result.append(SimpleTerm(
            value=value, token=value, title="-" * depth + title))
    return SimpleVocabulary(result)

@grok.provider(IContextSourceBinder)
def target_audiences_source(context):
    service = getUtility(IServiceNews)
    result = []
    for value, title, depth in service.filtered_ta_tree(context):
        result.append(SimpleTerm(
            value=value, token=value, title="-" * depth + title))
    return SimpleVocabulary(result)

@grok.provider(IContextSourceBinder)
def link_method_source(context):
    values = [(u"article",u"Article"),
              (u"external_link",u"External Link"),
              (u"nothing",u"Nothing")
              ]
    return SimpleVocabulary( [ SimpleTerm(v[0],v[0],v[1]) for v in values ] ) 


class ISubjectTASchema(Interface):
    subjects = schema.List(
        title=_(u"subjects"),
        description=_(
            u'Select the news subjects to filter on. '
            u'Only those selected will appear in this area of the site. '
            u'Select nothing to have all show up.'),
        value_type=schema.Choice(source=subjects_source),
        required=True)
    target_audiences = schema.List(
        title=_(u"target audiences"),
        description=_(u'Select the target audiences to filter on.'),
        value_type=schema.Choice(source=target_audiences_source),
        required=True)

class INewsItemSchema(ISubjectTASchema):
    """This schema defines the editable properties for
       news items (which appears in the infopanel when editing
       news items"""
    link_method = schema.Choice( 
        title=u"link method",
        description=u"what to link this article to when displayed in syndication",
        source=link_method_source,
        required = True
        )
    external_link = schema.TextLine(
        title=u"external link",
        description=u"if link method is 'external link', the url of the external link, otherwise leave blank",
        required = False,
        default=u""
        )
    
    @invariant
    def externalLinkMethod(event):
        if (event.link_method == 'external_link' and \
            not event.external_link):
            raise Invalid("`External Link` is required when `Link Method` is set to `External Link`")

class INewsItemVersion(IVersion, IContentLayout):
    """Silva news item version.

    This contains the real content for a news item.
    """

    def set_subjects(subjects):
        """Sets the subjects this news item is in."""

    def set_target_audiences(target_audiences):
        """Sets the target audiences for this news item."""

    def source_path():
        """Returns the physical path of the versioned content."""

    def is_private():
        """Returns true if the item is private.

        Private items are picked up only by news filters in the same
        container as the source.
        """

    def get_subjects():
        """Returns the subjects this news item is in."""

    def get_target_audiences():
        """Returns the target audiences for this news item."""

    def fulltext():
        """Returns a string containing all the words of all content.

        For fulltext ZCatalog search.
        XXX This should really be on an interface in the Silva core"""

    def to_xml():
        """Returns an XML representation of the object"""

    def content_xml():
        """Returns the document-element of the XML-content.

        XXX what does this mean?
        (not used by all subclasses)"""

class IAgendaItem(INewsItem):
    """Silva AgendaItem Version.
    """

class IAgendaItemVersion(INewsItemVersion):
    def get_start_datetime():
        """Returns start_datetime
        """

    def get_end_datetime():
        """Returns end_datetime
        """

    def get_location():
        """Returns location
        """

    def set_start_datetime(value):
        """Sets the start datetime to value (DateTime)"""

    def set_end_datetime(value):
        """Sets the end datetime to value (DateTime)"""

    def set_location(value):
        """Sets the location"""

class INewsPublication(IPublication):
    """Marker interface for INewsPublication"""

class IFilter(IAsset):

    def get_subjects():
        """Returns the list of subjects."""

    def get_target_audiences():
        """Returns the list of target audiences."""

    def set_subject(subjects):
        """Updates the list of subjects"""

    def set_target_audience(target_audiences):
        """Updates the list of target_audiences"""

    def synchronize_with_service():
        """Checks whether the lists of subjects and target_audiences
        only contain items that the service_news-lists contain (to remove
        items from the object's list that are removed in the service)
        """

class ICategoryFilter(IFilter):
    """A CategoryFilter is editable in silva.  It allows you to specify elements in the silva news article and silva news filter to hide from content authors"""

class INewsItemFilter(IFilter):
    """Super-class for news item filters.

    A NewsItemFilter picks up news from news sources. Editors can
    browse through this news. It can also be used by
    public pages to expose published news items to end users.

    A super-class for the News Filters (NewsFilter, AgendaFilter)
    which contains shared code for both filters"""

    def find_sources():
        """returns all the sources available for querying"""

    def get_sources():
        """return the source list of this newsitemfilter"""

    def set_sources(sources_list):
        """set the source list of this newsitemfilter"""

    def add_source(source):
        """add a"""

    def keep_to_path():
        """Returns true if the item should keep to path"""

    def set_keep_to_path(value):
        """Removes the filter from the list of filters where the item
        should appear"""

    def number_to_show():
        """Returns amount of items to show."""

    def set_number_to_show(number):
        """Updates the list of target_audiences"""

    def excluded_items():
        """Returns a list of object-paths of all excluded items
        """

    def set_excluded_items(object_path, add_or_remove):
        """Adds or removes an item to or from the excluded_items list
        """

    def verity_excluded_items():
        """maintain the list of excluded items in this filter,
        by removing ones that no longer exist (i.e. have been deleted)"""

    def search_items(keywords, meta_types=None):
        """ Returns the items from the catalog that have keywords
        in fulltext"""

    def filtered_subject_form_tree():
        """return a subject_form_tree (for the SMI edit screen)
        that is filtered through a news category filter, or if
        none are found, all subjects from the news service"""

    def filtered_ta_form_tree():
        """return a ta_form_tree (for the SMI edit screen)
        that is filtered through a news category filter, or if
        none are found, all ta's from the news service"""

    #functions to aid in compatibility between news and agenda filters
    # and viewers, so the viewers can pull from both types of filters

    def get_agenda_items_by_date(month, year, meta_types=None,
            timezone=None):
        """        Returns non-excluded published AGENDA-items for a particular
        month. This method is for exclusive use by AgendaViewers only,
        NewsViewers should use get_items_by_date instead (which
        filters on idx_display_datetime instead of start_datetime and
        returns all objects instead of only IAgendaItem-
        implementations)"""

    def get_next_items(numdays, meta_types=None):
        """ Note: ONLY called by AgendaViewers
        Returns the next <number> AGENDAitems,
        should return items that conform to the
        AgendaItem-interface (IAgendaItemVersion), although it will in
        any way because it requres start_datetime to be set.
        NewsViewers use only get_last_items.
        """

    def get_last_items(number, number_id_days=0, meta_types=None):
        """Returns the last (number) published items
           This is _only_ used by News Viewers.
        """

class INewsFilter(INewsItemFilter):
    """A filter for news items"""

    def show_agenda_items():
        """should we also show agenda items?"""

    def set_show_agenda_items():
        """sets whether to show agenda items"""

    def get_allowed_meta_types():
        """returns what metatypes are filtered on
        This is different because AgendaFilters search on start/end
        datetime, whereas NewsFilters look at display datetime"""

    def get_all_items(meta_types=None):
        """Returns all items, only to be used on the back-end"""

    def get_items_by_date(month, year, meta_types=None):
        """For looking through the archives
        This is different because AgendaFilters search on start/end
        datetime, whereas NewsFilters look at display datetime"""

class IAgendaFilter(INewsItemFilter):
    """A filter for agenda items"""

    def get_items_by_date(month, year, meta_types=None):
        """gets the events for a specific month
        This is different because AgendaFilters search on start/end
        datetime, whereas NewsFilters look at display datetime"""

    def backend_get_items_by_date(month, year, meta_types=None):
        """Returns all published items for a particular month
           FOR: the SMI 'items' tab"""

class IViewer(IContent):
    """Base interface for SilvaNews Viewers"""

_number_to_show = [
    (_(u"number of days"), 1),
    (_(u"number of items"), 0)
]

@grok.provider(IContextSourceBinder)
def show_source(context):
    terms = []
    for info in _number_to_show:
        title, value = info
        terms.append(SimpleTerm(value=value, token=value, title=title))
    return SimpleVocabulary(terms)

_week_days_list = [
    (_(u'Monday'),    0),
    (_(u'Tuesday'),   1),
    (_(u'Wednesday'), 2),
    (_(u'Thursday'),  3),
    (_(u'Friday'),    4),
    (_(u'Saturday'),  5),
    (_(u'Sunday'),    6)
]

@grok.provider(IContextSourceBinder)
def week_days_source(context):
    week_days_terms = []
    for info in _week_days_list:
        title, value = info
        week_days_terms.append(
            SimpleTerm(value=value, token=value, title=title))
    return SimpleVocabulary(week_days_terms)

@grok.provider(IContextSourceBinder)
def timezone_source(context):
    terms = []
    for zone in zone_names:
        terms.append(SimpleTerm(title=zone,
                                value=zone,
                                token=zone))
    return SimpleVocabulary(terms)

@grok.provider(IContextSourceBinder)
def filters_source(context):
    terms = []
    intids = getUtility(IIntIds)
    for filter in context.get_all_filters():
        path = "/".join(filter.getPhysicalPath())
        terms.append(SimpleTerm(value=filter,
                                title="%s (%s)" % (filter.get_title(), path),
                                token=str(intids.register(filter))))
    return SimpleVocabulary(terms)

@grok.provider(IContextSourceBinder)
def news_source(context):
    terms = []
    intids = getUtility(IIntIds)
    for source in context.get_all_sources():
        path = "/".join(source.getPhysicalPath())
        terms.append(SimpleTerm(value=source,
                                title="%s (%s)" % (source.get_title(), path),
                                token=str(intids.register(source))))
    return SimpleVocabulary(terms)

class INewsViewer(IViewer):
    """A viewer of news items.
    """
    # manipulators
    def set_number_to_show(number):
        """Set the number of items to show on the front page.
        """

    def set_number_to_show_archive(number):
        """Set the number to show per page in the archives.
        """

    def set_number_is_days(onoff):
        """If set to True, the number to show will be by days back, not number.
        """

    # accessors
    def number_to_show():
        """Amount of news items to show.
        """

    def number_to_show_archive():
        """Number of items per page to show in the archive.
        """

    def number_is_days():
        """If number_is_days is True, the number_to_show will control
        days back to show instead of number of items.
        """

    def get_filters():
        """Returns a list of associated filters.
        """

    def set_filters(filter_list):
        """set a list of the filters.
        """

    def add_filter(filter):
        """ add a filter.
        """

    def findfilters():
        """Returns a list of all paths to all filters.
        """

    def get_items():
        """Get items from the filters according to the number to show.
        """

    def get_items_by_date(month, year):
        """Given a month and year, give all items published then.
        """

    def search_items(keywords):
        """Search the items in the filters.
        """

    def set_proxy(item, force=False):
        """ Set the news viewer as parent of the item if proxy mode enabled.
        """

class IAggregator(INewsViewer):
    """interface for RSSAggregator"""

class IAgendaViewer(INewsViewer):
    def days_to_show():
        """Return number of days to show on front page.
        """

    def set_days_to_show(number):
        """Sets the number of days to show in the agenda.
        """

class IServiceNews(ISilvaService):
    """A service that provides trees of subjects and target_audiences.

    It allows these trees to be edited on a site-wide basis. It also
    provides these trees to the filter and items.

    The trees are dicts with the content as key and a a list of parent
    (first item) and children (the rest of the items) as value.
    """

    def add_subject(subject, parent):
        """Adds a subject to the tree of subjects.

        Subject is added under parent. If parent is None, the subject
        is added to the root.
        """

    def add_target_audience(target_audience, parent):
        """Adds a target_audience to the tree of target_audiences.

        Target audience is added under parent. If parent is None, the
        target_audience is added to the root.
        """

    def remove_subject(subject):
        """Removes the subject from the tree of subjects.
        """

    def remove_target_audience(target_audience):
        """Removes the target_audience from the tree of target_audiences.
        """

    # ACCESSORS
    def subjects():
        """Return the tree of subjects.
        """

    def subject_tuples():
        """Returns subject tree in tuple representation.

        Each tuple is an (indent, subject) pair.
        """

    def target_audiences():
        """Return the tree of target_audiences.
        """

    def target_audience_tuples():
        """Returns target audience tree in tuple representation.

        Each tuple is an (indent, subject) pair.
        """


class INewsItemTemplate(ITemplate):
    """A one-column template for news items"""

class IAgendaItemTemplate(ITemplate):
    """A one-column template for agenda items"""
    
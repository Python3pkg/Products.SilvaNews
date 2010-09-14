from zope.interface import Interface
from silva.core.interfaces import IAsset, ISilvaService, IPublication, IContent
from Products.SilvaDocument.interfaces import IDocument, IDocumentVersion
from Products.SilvaExternalSources.interfaces import IExternalSource


class IInlineViewer(IExternalSource):
    """Marker interface for Inline News Viewer"""


class ISilvaNewsExtension(Interface):
    """Marker interface for SNN Extension"""


class INewsItem(IDocument):
    """Silva News Item interface
    """


class INewsItemVersion(IDocumentVersion):
    """Silva news item version.

    This contains the real content for a news item.
    """

    def set_subjects(self, subjects):
        """Sets the subjects this news item is in."""

    def set_target_audiences(self, target_audiences):
        """Sets the target audiences for this news item."""

    def source_path(self):
        """Returns the physical path of the versioned content."""

    def is_private(self):
        """Returns true if the item is private.

        Private items are picked up only by news filters in the same
        container as the source.
        """

    def subjects(self):
        """Returns the subjects this news item is in."""

    def target_audiences(self):
        """Returns the target audiences for this news item."""

    def fulltext(self):
        """Returns a string containing all the words of all content.

        For fulltext ZCatalog search.
        XXX This should really be on an interface in the Silva core"""

    def to_xml(self):
        """Returns an XML representation of the object"""

    def content_xml(self):
        """Returns the document-element of the XML-content.

        XXX what does this mean?
        (not used by all subclasses)"""


class IAgendaItem(INewsItem):
    """Silva AgendaItem Version.
    """


class IAgendaItemVersion(INewsItemVersion):
    def start_datetime():
        """Returns start_datetime
        """

    def location():
        """Returns location
        """

    def set_start_datetime(value):
        """Sets the start datetime to value (DateTime)"""

    def set_location(value):
        """Sets the location"""

    def set_location(value):
        """Sets the manual location"""


class INewsPublication(IPublication):
    """Marker interface for INewsPublication"""


class IFilter(IAsset):

    def subjects(self):
        """Returns the list of subjects."""

    def target_audiences(self):
        """Returns the list of target audiences."""

    def set_subject(self, subject, on_or_off):
        """Updates the list of subjects"""

    def set_target_audience(self, target_audience, on_or_off):
        """Updates the list of target_audiences"""

    def synchronize_with_service(self):
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

    def find_sources(self):
        """returns all the sources available for querying"""

    def sources(self):
        """return the sourcelist of this newsitemfilter"""

    def verify_sources(self):
        """Verifies the sourcelist against the available sources,
           removing those sources that no longer exist"""

    def add_source(self, sourcepath, add_or_remove):
        """add or remove a source from the sourcelist"""

    def keep_to_path(self):
        """Returns true if the item should keep to path"""

    def set_keep_to_path(self, value):
        """Removes the filter from the list of filters where the item
        should appear"""

    def number_to_show(self):
        """Returns amount of items to show."""

    def set_number_to_show(self, number):
        """Updates the list of target_audiences"""

    def excluded_items(self):
        """Returns a list of object-paths of all excluded items
        """

    def set_excluded_items(self, object_path, add_or_remove):
        """Adds or removes an item to or from the excluded_items list
        """

    def verity_excluded_items(self):
        """maintain the list of excluded items in this filter,
        by removing ones that no longer exist (i.e. have been deleted)"""

    def search_items(self, keywords, meta_types=None):
        """ Returns the items from the catalog that have keywords
        in fulltext"""

    def filtered_subject_form_tree(self):
        """return a subject_form_tree (for the SMI edit screen)
        that is filtered through a news category filter, or if
        none are found, all subjects from the news service"""

    def filtered_ta_form_tree(self):
        """return a ta_form_tree (for the SMI edit screen)
        that is filtered through a news category filter, or if
        none are found, all ta's from the news service"""

    #functions to aid in compatibility between news and agenda filters
    # and viewers, so the viewers can pull from both types of filters

    def get_agenda_items_by_date(self, month, year, meta_types=None):
        """        Returns non-excluded published AGENDA-items for a particular
        month. This method is for exclusive use by AgendaViewers only,
        NewsViewers should use get_items_by_date instead (which
        filters on idx_display_datetime instead of start_datetime and
        returns all objects instead of only IAgendaItem-
        implementations)"""

    def get_next_items(self, numdays, meta_types=None):
        """ Note: ONLY called by AgendaViewers
        Returns the next <number> AGENDAitems,
        should return items that conform to the
        AgendaItem-interface (IAgendaItemVersion), although it will in
        any way because it requres start_datetime to be set.
        NewsViewers use only get_last_items.
        """

    def get_last_items(self, number, number_id_days=0, meta_types=None):
        """Returns the last (number) published items
           This is _only_ used by News Viewers.
        """


class INewsFilter(INewsItemFilter):
    """A filter for news items"""

    def show_agenda_items(self):
        """should we also show agenda items?"""

    def set_show_agenda_items(self):
        """sets whether to show agenda items"""

    def get_allowed_meta_types(self):
        """returns what metatypes are filtered on
        This is different because AgendaFilters search on start/end
        datetime, whereas NewsFilters look at display datetime"""

    def get_all_items(self, meta_types=None):
        """Returns all items, only to be used on the back-end"""

    def get_items_by_date(self, month, year, meta_types=None):
        """For looking through the archives
        This is different because AgendaFilters search on start/end
        datetime, whereas NewsFilters look at display datetime"""


class IAgendaFilter(INewsItemFilter):
    """A filter for agenda items"""

    def get_allowed_meta_types(self):
        """returns what metatypes are filtered on
        This is different because AgendaFilters search on start/end
        datetime, whereas NewsFilters look at display datetime"""

    def get_items_by_date(self, month, year, meta_types=None):
        """gets the events for a specific month
        This is different because AgendaFilters search on start/end
        datetime, whereas NewsFilters look at display datetime"""

    def backend_get_items_by_date(self, month, year, meta_types=None):
        """Returns all published items for a particular month
           FOR: the SMI 'items' tab"""


class IViewer(IContent):
    """Base interface for SilvaNews Viewers"""


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

    def set_filter(newsfilter, on_or_off):
        """Adds or removes a filter from the list of filters.

        If on_or_off is True, add filter, if False, remove filter.
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

    def filters():
        """Returns a list of the path to all news filters associated.
        """

    def findfilters():
        """Returns a list of all paths to all filters.
        """

    def findfilters_pairs():
        """Returns a list of tuples (title, path) for all filters.
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

    def rss():
        """Represent this viewer as an RSS feed. (RSS 1.0)
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

    def add_subject(self, subject, parent):
        """Adds a subject to the tree of subjects.

        Subject is added under parent. If parent is None, the subject
        is added to the root.
        """

    def add_target_audience(self, target_audience, parent):
        """Adds a target_audience to the tree of target_audiences.

        Target audience is added under parent. If parent is None, the
        target_audience is added to the root.
        """

    def remove_subject(self, subject):
        """Removes the subject from the tree of subjects.
        """

    def remove_target_audience(self, target_audience):
        """Removes the target_audience from the tree of target_audiences.
        """

    # ACCESSORS
    def subjects(self):
        """Return the tree of subjects.
        """

    def subject_tuples(self):
        """Returns subject tree in tuple representation.

        Each tuple is an (indent, subject) pair.
        """

    def target_audiences(self):
        """Return the tree of target_audiences.
        """

    def target_audience_tuples(self):
        """Returns target audience tree in tuple representation.

        Each tuple is an (indent, subject) pair.
        """


class ISilvaXMLAttribute(Interface):
    """an interface for SilvaXMLAttribute objects,
     i.e. an attribute which contains silvaxml
     A Silva object could have multiple attributes
     containing silva xml, each of which is a
     SilvaXMLAttribute"""

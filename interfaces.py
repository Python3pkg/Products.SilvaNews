from zope.interface import Interface
from Products.Silva.interfaces import ISilvaObject, IVersion

class INewsItem(ISilvaObject):
    """Silva News Item interface
    """

class INewsItemVersion(IVersion):
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

    def content_xml(self):
        """Returns the document-element of the XML-content.

        XXX what does this mean?
        (not used by all subclasses)"""

    def to_xml(self):
        """Returns an XML representation of the object"""
        
class IAgendaItem(INewsItem):
    """Silva AgendaItem.
    """

class IAgendaItemVersion(INewsItemVersion):
    def start_datetime(self):
        """Returns start_datetime
        """

    def location(self):
        """Returns location
        """

    def location(self):
        """Returns manually entered location
        """

    def set_start_datetime(self, value):
        """Sets the start datetime to value (DateTime)"""

    def set_location(self, value):
        """Sets the location"""

    def set_location(self, value):
        """Sets the manual location"""

class INewsFilter(Interface):
    """Filter for news items.

    A filter picks up news from news sources. Editors can
    browse through this news. It can also be used by
    public pages to expose published news items to end users.
    """
    
    def keep_to_path(self):
        """Returns true if the item should keep to path
        """

    def number_to_show(self):
        """Returns amount of items to show.
        """

    def subjects(self):
        """Returns the list of subjects.
        """

    def target_audiences(self):
        """Returns the list of target audiences.
        """

    def set_keep_to_path(self, value):
        """Removes the filter from the list of filters where the item
        should appear
        """

    def set_subject(self, subject, on_or_off):
        """Updates the list of subjects
        """

    def set_target_audience(self, target_audience, on_or_off):
        """Updates the list of target_audiences
        """

    def set_number_to_show(self, number):
        """Updates the list of target_audiences
        """

    def get_all_items(self, meta_types=('Silva News Article',)):
        """Returns all items, only to be used on the back-end
        """

    def get_all_public_items(self, meta_types=('Silva News Article',)):
        """Returns all published items
        """

    def get_last_public_items(self, meta_types=('Silva News Article',)):
        """Returns the last self._number_to_show published items
        """

class INewsViewer(Interface):
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
    
class IAgendaViewer(INewsViewer):
    def days_to_show():
        """Return number of days to show on front page.
        """

    def set_days_to_show(number):
        """Sets the number of days to show in the agenda.
        """

class IServiceNews(Interface):
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

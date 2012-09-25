# -*- coding: utf-8 -*-
# Copyright (c) 2002-2012 Infrae. All rights reserved.
# See also LICENSE.txt

from zope.interface import Interface

from Products.SilvaDocument.interfaces import IDocument, IDocumentVersion


class ISilvaNewsExtension(Interface):
    """Marker interface for SNN Extension"""


class INewsCategorization(Interface):
    """Categorize news information by subject and target audience.
    """

    def get_subjects():
        """Returns the list of subjects."""

    def get_target_audiences():
        """Returns the list of target audiences."""

    def set_subjects(subjects):
        """Updates the list of subjects"""

    def set_target_audiences(target_audiences):
        """Updates the list of target_audiences"""


class INewsItem(IDocument):
    """Silva News Item interface
    """


class INewsItemVersion(IDocumentVersion, INewsCategorization):
    """Silva news item version.

    This contains the real content for a news item.
    """

    def source_path():
        """Returns the physical path of the versioned content."""

    def is_private():
        """Returns true if the item is private.

        Private items are picked up only by news filters in the same
        container as the source.
        """

    def fulltext():
        """Returns a string containing all the words of all content.

        For fulltext ZCatalog search.
        XXX This should really be on an interface in the Silva core"""


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



# Copyright (c) 2002 Infrae. All rights reserved.
# See also LICENSE.txt
# $Revision: 1.12.2.3 $

from AccessControl import ClassSecurityInfo
from Globals import InitializeClass
from Products.PageTemplates.PageTemplateFile import PageTemplateFile
from DateTime import DateTime
import Acquisition

from Products.Silva.interfaces import IContent
from Products.Silva import SilvaPermissions
from Products.Silva.Content import Content
from Products.SilvaDocument.Document import Document
from Products.Silva.helpers import add_and_edit
from Products.Silva import mangle

from Products.SilvaNews.NewsViewer import NewsViewer

import feedparser

icon = 'www/rss_viewer.png'
addable_priority = 3.6

class RSSViewer(NewsViewer):
    """A viewer for (external) RSS streams. 
    """

    security = ClassSecurityInfo()

    __implements__ = IContent

    meta_type = 'Silva RSS Viewer'

    def __init__(self, id):
        RSSViewer.inheritedAttribute('__init__')(self, id)
        self._rss_feed = ''
        self._rss_last_modified = ''
        self._caching_period = 30 # in seconds, 0 means don't cache


    # MANIPULATORS

    security.declareProtected(SilvaPermissions.ChangeSilvaContent,
                              'set_rss_feed')
    def set_rss_feed(self, url):
        """Sets the URL for the RSS feed to use"""
        self._rss_feed = url
        self._rss_last_modified = ''



    # ACCESSORS

    security.declareProtected(SilvaPermissions.AccessContentsInformation,
                              'get_channel')
    def get_channel(self):
        """Gets the date from the RSS feed
        """
        if self._rss_feed:
            res = feedparser.parse(self._rss_feed)
        else:
            raise Exception, 'Please choose a feed first!'

        return res

    security.declareProtected(SilvaPermissions.AccessContentsInformation,
                              'rss_feed')
    def rss_feed(self):
        """Returns the URL of the RSS feed"""
        return self._rss_feed

InitializeClass(RSSViewer)

manage_addRSSViewerForm = PageTemplateFile(
    "www/rssViewerAdd", globals(),
    __name__='manage_addRSSViewerForm')

def manage_addRSSViewer(self, id, title, REQUEST=None):
    """Add a News RSSViewer."""
    if not mangle.Id(self, id).isValid():
        return
    object = RSSViewer(id)
    self._setObject(id, object)
    object = getattr(self, id)
    object.set_title(title)
    add_and_edit(self, id, REQUEST)
    return ''

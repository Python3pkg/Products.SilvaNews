# Copyright (c) 2002-2008 Infrae. All rights reserved.
# See also LICENSE.txt
# $Revision: 1.13 $

# Zope
from AccessControl import ClassSecurityInfo
from App.class_init import InitializeClass

from Products.SilvaNews.interfaces import INewsPublication
from Products.SilvaMetadata.interfaces import IMetadataService
from Products.Silva.Publication import Publication
from Products.Silva import SilvaPermissions

from five import grok
from silva.core import conf as silvaconf
from zope.component import getUtility
from zope.lifecycleevent.interfaces import IObjectCreatedEvent
from zeam.form import silva as silvaforms


class NewsPublication(Publication):
    """A special publication type (a.k.a. News Source) for news
    and agenda items. News Filters and Agenda Filters can pick up
    news from these sources anywhere in a Silva site.
    """
    security = ClassSecurityInfo()

    grok.implements(INewsPublication)
    meta_type = "Silva News Publication"
    silvaconf.icon("www/news_source.png")
    silvaconf.priority(3)

    def __init__(self, id):
        super(NewsPublication, self).__init__(id)
        self._addables_allowed_in_container = [
            'Silva Article', 'Silva Agenda Item',
            'Silva Publication', 'Silva Folder',
            'Silva News Viewer', 'Silva Agenda Viewer',
            'Silva News Filter', 'Silva Agenda Filter']

    security.declareProtected(SilvaPermissions.AccessContentsInformation,
                              'parent_path')
    def parent_path(self):
        """Returns the path of the parent of this source
        """
        return '/'.join(self.aq_inner.aq_parent.getPhysicalPath())

    security.declareProtected(SilvaPermissions.AccessContentsInformation,
                              'idx_parent_path')
    idx_parent_path = parent_path


InitializeClass(NewsPublication)


@silvaconf.subscribe(INewsPublication, IObjectCreatedEvent)
def news_publication_created(publication, event):
    """news publications should have their 'hide_from_tocs' set to
       'hide'.  This can be done after they are added
    """
    binding = getUtility(IMetadataService).getMetadata(publication)
    binding.setValues('silva-extra', {'hide_from_tocs': 'hide'}, reindex=1)
    binding.setValues('snn-np-settings', {'is_private': 'no'}, reindex=1)

    factory = publication.manage_addProduct['Silva']
    factory.manage_addAutoTOC(
        'index', publication.get_title_or_id(),
        local_types=['Silva Article', 'Silva Agenda Item'])


class NewsPublicationAddForm(silvaforms.SMIAddForm):
    grok.context(INewsPublication)
    grok.name(u"Silva News Publication")

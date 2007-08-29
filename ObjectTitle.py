# Copyright (c) 2002-2006 Infrae. All rights reserved.
# See also LICENSE.txt
# $Revision: 1.25 $

from AccessControl import ClassSecurityInfo
from Products.Silva import SilvaPermissions
from Globals import InitializeClass

class ObjectTitle:
    """Simple mixin that holds functionality to store and get titles

    Can be used to allow Container type objects to have their own title
    """
    # XXX Is this the way to go? Would it be better to have a special type
    # of container for this? Should the objects subclass something else 
    # instead?

    security = ClassSecurityInfo()

    security.declareProtected(SilvaPermissions.AccessContentsInformation,
                              'get_title')
    def get_title(self):
        """Return the title

        Is overridden to regain the behaviour of SilvaObject instead of that
        of superclass Silva.Folder
        """
        return self.service_metadata.getMetadataValue(
            self, 'silva-content', 'maintitle')

    security.declareProtected(SilvaPermissions.AccessContentsInformation, 
                              'get_short_title')
    def get_short_title(self):
        """Get the short title or the title
        """
        short_title = self.service_metadata.getMetadataValue(
            self, 'silva-content', 'shorttitle')
        if not short_title:
            return self.get_title()
        return short_title

    security.declareProtected(SilvaPermissions.AccessContentsInformation, 
                              'get_short_title_editable')
    get_short_title_editable = get_short_title

    security.declareProtected(SilvaPermissions.AccessContentsInformation,
                              'get_title_editable')
    get_title_editable = get_title

    security.declareProtected(SilvaPermissions.AccessContentsInformation,
                              'get_title_or_id')
    def get_title_or_id(self):
        return self.get_title() or self.id

    security.declareProtected(SilvaPermissions.AccessContentsInformation,
                              'get_title_or_id_editable')
    get_title_or_id_editable = get_title_or_id

    def set_title(self, title):
        binding = self.service_metadata.getMetadata(self)
        binding.setValues('silva-content', {'maintitle': title.encode('UTF-8')})

InitializeClass(ObjectTitle)

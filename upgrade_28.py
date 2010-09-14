# Copyright (c) 2002-2009 Infrae. All rights reserved.
# See also LICENSE.txt
# $Id$
from silva.core.upgrade.upgrade import BaseUpgrader

#this is the Silva version these upgrades should run under
VERSION_B1='2.2b1'

class IndexUpgrader(BaseUpgrader):
    """ remove the idx_is_private catalog index; it's
        not used anymore.  This functionality has been moved
        into metadata."""
    def upgrade(self, obj):
        if 'idx_is_private' in obj.service_catalog.indexes():
            obj.service_catalog.delIndex('idx_is_private')
        return obj

indexupgrader = IndexUpgrader(VERSION_B1, 'Silva Root')

class SNNRefresher(BaseUpgrader):
    """ Root upgrader to refresh SNN if it was
        installed in Silva 2.1.  Since the extension
        registry is installed test has changed, this
        needs to check if the SilvaNews view directory
        is present.  If it is, install the extension
        """
    
    def upgrade(self, obj):
        se = obj.service_extensions
        name = 'SilvaNews'
        if hasattr(obj.service_views.aq_explicit, name):
            #SNN was installed, so reinstall
            if se.is_installed(name):
                se.refresh(name)
            else:
                se.install(name)
        return obj
    
#give it the highest priority so that the silva core 
# metadata and secondrootupgraders can run first
SNNRefresher = SNNRefresher(VERSION_B1, 'Silva Root', 0)

class NewsPubIsPrivateUpgrader(BaseUpgrader):
    """ upgrade obj._is_private to snn-np-settings: is_private
    metadata set"""

    def upgrade(self, obj):
        if obj.__dict__.has_key('_is_private'):
            ip = obj._is_private
            del obj._is_private
            newip = 'no'
            if ip:
                newip = 'yes'
            binding = obj.service_metadata.getMetadata(obj)
            binding.setValues('snn-np-settings',{'is_private': newip})
        return obj

newspubupgrader = NewsPubIsPrivateUpgrader(
    VERSION_B1, 'Silva News Publication', 100)

class SNNServiceCleanup(BaseUpgrader):
    """ this upgrader cleans up the service news, as it no longer
        manages SNN's upgrades """
    
    def upgrade(self, obj):
        #remove service_news._content_version
        if hasattr(obj.aq_explicit, '_content_version'):
            del obj._content_version
        return obj

SNNServiceCleanupUpgrader = SNNServiceCleanup(VERSION_B1, 'Silva News Service', 50)

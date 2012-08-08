

from silva.core.upgrade.upgrade import BaseUpgrader

VERSION_B2='2.2b2'


class NewsPublicationUpgrader(BaseUpgrader):
    """ upgrade obj._is_private to snn-np-settings: is_private
    metadata set"""

    def upgrade(self, obj):
        if obj.__dict__.has_key('_is_private'):
            if obj._is_private:
                value = 'yes'
            else:
                value = 'no'
            binding = obj.service_metadata.getMetadata(obj)
            binding.setValues('snn-np-settings', {'is_private': value})
            del obj._is_private
        return obj


news_publication_upgrader = NewsPublicationUpgrader(
    VERSION_B2, 'Silva News Publication', 100)


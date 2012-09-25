# -*- coding: utf-8 -*-
# Copyright (c) 2012  Infrae. All rights reserved.
# See also LICENSE.txt

from zope.cachedescriptors.property import Lazy

from silva.core.upgrade.upgrade import BaseUpgrader
from silva.app.news.interfaces import IServiceNews
from zope.component import getUtility

from Products.SilvaMetadata.interfaces import IMetadataService

VERSION_B2='2.2b2'


class NewsPublicationUpgrader(BaseUpgrader):
    """ upgrade obj._is_private to snn-np-settings: is_private
    metadata set"""

    @Lazy
    def metadata(self):
        return getUtility(IMetadataService)

    @Lazy
    def news(self):
        return getUtility(IServiceNews)

    def validate(self, container):
        return (container.__dict__.has_key('_is_private') or
                container._getOb('index', None) is None)

    def upgrade(self, container):
        if container.__dict__.has_key('_is_private'):
            if container._is_private:
                value = 'yes'
            else:
                value = 'no'
            binding = self.metadata.getMetadata(container)
            binding.setValues('snn-np-settings', {'is_private': value}, reindex=1)
            del container._is_private
        if container._getOb('index', None) is None:
            factory = container.manage_addProduct['silva.app.news']
            factory.manage_addNewsViewer(
                'index', container.get_title_or_id())
            factory.manage_addNewsFilter(
                'filter', 'Filter for %s' % container.get_title_or_id())

            viewer = container._getOb('index')
            filter = container._getOb('filter')

            # Configure the new filter and viewer.

            filter.set_subjects(
                self.news.get_subjects_tree().get_ids(1))
            filter.set_target_audiences(
                self.news.get_target_audiences_tree().get_ids(1))
            filter.add_source(container)
            viewer.add_filter(filter)

        return container


publication_upgrader = NewsPublicationUpgrader(
    VERSION_B2, 'Silva News Publication', 100)


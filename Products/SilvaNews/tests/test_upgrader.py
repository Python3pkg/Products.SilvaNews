# -*- coding: utf-8 -*-

import unittest

from Products.Silva.testing import tests
from Products.SilvaNews.testing import FunctionalLayer
from Products.SilvaNews.upgrader.upgrade_220 import publication_upgrader
from Products.SilvaNews.upgrader.upgrade_230 import filter_upgrader
from Products.SilvaNews.upgrader.upgrade_230 import viewer_upgrader
from Products.SilvaMetadata.interfaces import IMetadataService

from zope.component import getUtility
from zope.interface.verify import verifyObject
from silva.core.services.interfaces import ICatalogService
from silva.app.news.NewsPublication import NewsPublication
from silva.app.news.filters.NewsFilter import NewsFilter
from silva.app.news.viewers.NewsViewer import NewsViewer
from silva.app.news.interfaces import INewsFilter, INewsViewer


class UpgraderTestCase(unittest.TestCase):
    layer = FunctionalLayer
    maxDiff = None

    def setUp(self):
        self.root = self.layer.get_application()
        self.layer.login('editor')

    def test_upgrade_news_viewer(self):
        """Test upgrade of a news viewer
        """
        self.root._setObject('news', NewsFilter('news'))
        self.root._setObject('events', NewsFilter('events'))
        self.root._setObject('viewer', NewsViewer('viewer'))
        self.assertIn('news', self.root.objectIds())
        self.assertIn('events', self.root.objectIds())
        self.assertIn('viewer', self.root.objectIds())
        self.assertIn('index', self.root.objectIds())
        self.root.viewer._filters = [
            '/root/index',
            '/root/news',
            '/root/lala',
            '/root/@@pouet',
            '/root/events']
        self.assertTrue(viewer_upgrader.validate(self.root.viewer))
        self.assertEqual(
            viewer_upgrader.upgrade(self.root.viewer),
            self.root.viewer)
        self.assertFalse(viewer_upgrader.validate(self.root.viewer))
        tests.assertContentItemsEqual(
            self.root.viewer.get_filters(),
            [self.root.news, self.root.events])

    def test_upgrade_news_filter(self):
        """Test upgrade of a news filter.
        """
        self.root._setObject('news', NewsPublication('news'))
        self.root._setObject('events', NewsPublication('events'))
        self.root._setObject('filter', NewsFilter('filter'))
        self.assertIn('news', self.root.objectIds())
        self.assertIn('events', self.root.objectIds())
        self.assertIn('filter', self.root.objectIds())
        self.assertIn('index', self.root.objectIds())
        self.root.filter._sources = [
            '/root/news',
            '/root/events',
            '/root/index',
            '/root/lala',
            '/root/@@pouet']
        self.assertTrue(filter_upgrader.validate(self.root.filter))
        self.assertEqual(
            filter_upgrader.upgrade(self.root.filter),
            self.root.filter)
        self.assertFalse(filter_upgrader.validate(self.root.filter))
        tests.assertContentItemsEqual(
            self.root.filter.get_sources(),
            [self.root.news, self.root.events])

    def test_upgrade_news_publication(self):
        """Test upgrade of a news publication.
        """
        self.root._setObject('news', NewsPublication('news'))
        self.assertIn('news', self.root.objectIds())
        news = self.root.news
        news._is_private = True
        self.assertItemsEqual(news.objectIds(), [])
        self.assertTrue(publication_upgrader.validate(news))
        self.assertEqual(publication_upgrader.upgrade(news), news)
        self.assertFalse(publication_upgrader.validate(news))
        self.assertItemsEqual(news.objectIds(), ['index', 'filter'])
        metadata = getUtility(IMetadataService)
        self.assertEqual(
            metadata.getMetadataValue(news, 'snn-np-settings', 'is_private'),
            'yes')
        self.assertTrue(verifyObject(INewsViewer, news._getOb('index')))
        self.assertTrue(verifyObject(INewsFilter, news._getOb('filter')))
        catalog = getUtility(ICatalogService)
        self.assertItemsEqual(
            [b.getPath() for b in catalog(
                    {'meta_type': 'Silva News Publication',
                     'snn-np-settingsis_private': 'yes'})],
            ['/root/news'])

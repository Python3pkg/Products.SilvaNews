# -*- coding: utf-8 -*-

import unittest

from Products.SilvaNews.testing import FunctionalLayer
from Products.SilvaNews.upgrader.upgrade_220 import news_publication_upgrader
from Products.SilvaMetadata.interfaces import IMetadataService

from zope.component import getUtility
from zope.interface.verify import verifyObject
from silva.app.news.NewsPublication import NewsPublication
from silva.app.news.interfaces import INewsFilter, INewsViewer


class UpgraderTestCase(unittest.TestCase):
    layer = FunctionalLayer

    def setUp(self):
        self.root = self.layer.get_application()
        self.layer.login('editor')

    def test_upgrade_publication_private(self):
        self.root._setObject('news', NewsPublication('news'))
        self.assertIn('news', self.root.objectIds())
        news = self.root.news
        news._is_private = True
        self.assertItemsEqual(news.objectIds(), [])
        self.assertTrue(news_publication_upgrader.validate(news))
        self.assertEqual(news_publication_upgrader.upgrade(news), news)
        self.assertFalse(news_publication_upgrader.validate(news))
        self.assertItemsEqual(news.objectIds(), ['index', 'filter'])
        metadata = getUtility(IMetadataService)
        self.assertEqual(
            metadata.getMetadataValue(news, 'snn-np-settings', 'is_private'),
            'yes')
        self.assertTrue(verifyObject(INewsViewer, news._getOb('index')))
        self.assertTrue(verifyObject(INewsFilter, news._getOb('filter')))

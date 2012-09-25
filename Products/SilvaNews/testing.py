# -*- coding: utf-8 -*-
# Copyright (c) 2011-2012 Infrae. All rights reserved.
# See also LICENSE.txt

from Products.Silva.testing import SilvaLayer
import Products.SilvaNews
import transaction


class SilvaNewsLayer(SilvaLayer):
    default_products = SilvaLayer.default_products + [
        'SilvaExternalSources',
        'SilvaDocument',
        ]
    default_packages = SilvaLayer.default_packages + [
        'silva.app.document',
        'silva.app.news'
        ]

    def _install_application(self, app):
        super(SilvaNewsLayer, self)._install_application(app)
        app.root.service_extensions.install('silva.app.document')
        app.root.service_extensions.install('silva.app.news')
        app.root.service_extensions.install('SilvaDocument')
        app.root.service_extensions.install('SilvaNews')
        transaction.commit()


FunctionalLayer = SilvaNewsLayer(Products.SilvaNews)

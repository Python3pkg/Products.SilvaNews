# -*- coding: utf-8 -*-
# Copyright (c) 2012-2013 Infrae. All rights reserved.
# See also LICENSE.txt

from silva.core.conf.installer import DefaultInstaller
from Products.SilvaNews.interfaces import ISilvaNewsExtension


class SilvaNewsInstaller(DefaultInstaller):
    """Installer for the Silva News Service
    """
    not_globally_addables = ['Obsolete Article', 'Obsolete Agenda Item']

install = SilvaNewsInstaller("SilvaNews", ISilvaNewsExtension)

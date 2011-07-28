
from silva.core.conf.installer import DefaultInstaller
from Products.SilvaNews.interfaces import ISilvaNewsExtension


class SilvaNewsInstaller(DefaultInstaller):
    """Installer for the Silva News Service
    """
    not_globally_addables = ['Obsolete Article', 'Obsolete Agenda Item']

install = SilvaNewsInstaller("SilvaNews", ISilvaNewsExtension)

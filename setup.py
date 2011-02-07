# Copyright (c) 2002-2008 Infrae. All rights reserved.
# See also LICENSE.txt
# $Id$

from setuptools import setup, find_packages
import os

version = '2.9.2dev'

def product_readme(filename):
    return  open(os.path.join('Products', 'SilvaNews', filename)).read()


setup(name='Products.SilvaNews',
      version=version,
      description="News extension for Silva",
      long_description=product_readme("README.txt") + "\n" +
                       product_readme("HISTORY.txt"),

      classifiers=[
              "Framework :: Zope2",
              "Topic :: Internet :: WWW/HTTP :: Dynamic Content :: Message Boards",
              "Programming Language :: Python",
              "Topic :: Software Development :: Libraries :: Python Modules",
              ],
      keywords='news silva zope2',
      author='Infrae',
      author_email='info@infrae.com',
      url='http://infrae.com/products/silva',
      license='BSD',
      packages=find_packages(exclude=['ez_setup']),
      namespace_packages=['Products'],
      include_package_data=True,
      zip_safe=False,
      install_requires=[
        'Products.Formulator',
        'Products.ParsedXML',
        'Products.Silva',
        'Products.SilvaDocument',
        'five.grok',
        'icalendar',
        'megrok.chameleon',
        'python-dateutil',
        'setuptools',
        'silva.core.conf',
        'silva.core.interfaces',
        'silva.core.references',
        'silva.core.services',
        'silva.core.smi',
        'silva.core.upgrade',
        'silva.core.views',
        'z3locales',
        'zeam.form.silva',
        'zeam.utils.batch',
        'zope.app.container',
        'zope.component',
        'zope.i18nmessageid',
        'zope.interface',
        'zope.intid',
        'zope.lifecycleevent',
        'zope.location',
        'zope.publisher',
        'zope.schema',
        'zope.traversing',
        ],
      entry_points = """
      [zodbupdate]
      renames = Products.SilvaNews:CLASS_CHANGES
      [zeam.form.components]
      recurrence = Products.SilvaNews.widgets.recurrence:register
      """
      )

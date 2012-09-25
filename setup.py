# -*- coding: utf-8 -*-
# Copyright (c) 2002-2012 Infrae. All rights reserved.
# See also LICENSE.txt

from setuptools import setup, find_packages
import os

version = '3.0c1'

tests_require = [
    'Products.Silva [test]',
    'Products.SilvaDocument [test]',
    ]

def product_readme(filename):
    return  open(os.path.join('Products', 'SilvaNews', filename)).read()


setup(name='Products.SilvaNews',
      version=version,
      description="News extension for Silva 2.x.",
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
        'five.grok',
        'Products.Silva',
        'Products.SilvaDocument',
        'python-dateutil',
        'setuptools',
        'silva.app.news',
        'silva.core.conf',
        'silva.core.interfaces',
        'silva.core.smi',
        'silva.core.upgrade',
        'silva.core.views',
        'z3locales',
        'zope.interface',
        ],
      tests_require = tests_require,
      extras_require = {'test': tests_require},
      entry_points = """
      [zodbupdate]
      renames = Products.SilvaNews:CLASS_CHANGES
      """
      )

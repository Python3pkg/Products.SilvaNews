# Copyright (c) 2002-2011 Infrae. All rights reserved.
# See also LICENSE.txt
# $Id$

from SilvaNewsTestCase import SilvaNewsTestCase
from Products.Silva.roleinfo import AUTHOR_ROLES

class SilvaNewsInstallerTestCase(SilvaNewsTestCase):

    def test_news_service_available(self):
        #make sure the news service is present
        self.assertEquals(True, hasattr(self.root,'service_news'))

    def is_installed(self):
        self.assertEquals(True,
                          self.root.service_extensions.is_installed(
                'SilvaNews'))

    def test_catalog_columns(self):
        #ensure catalog columns are setup
        catalog = self.catalog
        columns = ['object_path',
                   'get_title',
                   'display_datetime',
                   'get_intro']
        existing_columns = catalog.schema()
        for cn in columns:
            self.assertEquals(True,
                              cn in existing_columns)
    def test_catalog_indexes(self):
        #ensure catalog indexes are setup
        catalog = self.catalog
        indexes = [
            ('object_path', 'FieldIndex'),
            ('idx_parent_path', 'FieldIndex'),
            ('idx_display_datetime', 'DateIndex'),
            ('idx_subjects', 'KeywordIndex'),
            ('idx_target_audiences', 'KeywordIndex'),
        ]
        existing_indexes = catalog.getIndexObjects()
        for (id,mt) in indexes:
            index = None
            for i in existing_indexes:
                if i.id == id:
                    index = i
                    break
            self.assertEquals(id, index.id)
            self.assertEquals(index.meta_type,mt)

    def test_security(self):
        #ensure addable security is assigned to the
        # appropriate roles
        root = self.root
        add_permissions = [
            'Add Silva Agenda Filters',
            'Add Silva Agenda Item Versions',
            'Add Silva Agenda Items',
            'Add Silva Agenda Viewers',
            'Add Silva Article Versions',
            'Add Silva Articles',
            'Add Silva News Filters',
            'Add Silva News Publications',
            'Add Silva News Viewers',
            'Add Silva RSS Aggregators',
            'Add Silva News Category Filters',
            ]
        possible_permissions = root.possible_permissions()
        a_roles = list(AUTHOR_ROLES[:])
        a_roles.sort()
        for perm in add_permissions:
            if perm in possible_permissions:
                roles = [ r['name'] for r in root.rolesOfPermission(perm)
                          if r['selected'] == 'SELECTED' ]
                self.assertEquals(a_roles,roles)

    def test_addables(self):
        # make sure the root addables doesn't include
        # news/agenda items
        addables = self.root.get_silva_addables_allowed_in_container()
        allowed_snn_types = ['Silva Agenda Filter','Silva Agenda Viewer',
                             'Silva News Category Filter',
                             'Silva News Filter', 'Silva News Publication',
                             'Silva News Viewer', 'Silva RSS Aggregator']
        for allowed in allowed_snn_types:
            self.assert_(allowed in addables)
        disallowed_snn_types = ['Silva Article', 'Silva Agenda Item']
        for dis in disallowed_snn_types:
            self.assert_(dis not in addables)

import unittest
def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(SilvaNewsInstallerTestCase))
    return suite

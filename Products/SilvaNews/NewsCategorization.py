# -*- coding: utf-8 -*-
# Copyright (c) 2011 Infrae. All rights reserved.
# See also LICENSE.txt
# $Id$

# Zope
from AccessControl import ClassSecurityInfo
from App.class_init import InitializeClass
from Products.Silva import SilvaPermissions


class NewsCategorization(object):
    security = ClassSecurityInfo()

    def __init__(self, id):
        super(NewsCategorization, self).__init__(id)
        self._subjects = set()
        self._target_audiences = set()

    security.declareProtected(
        SilvaPermissions.ChangeSilvaContent, 'set_subjects')
    def set_subjects(self, subjects):
        self._subjects = set(subjects)

    security.declareProtected(
        SilvaPermissions.ChangeSilvaContent, 'set_target_audiences')
    def set_target_audiences(self, target_audiences):
        self._target_audiences = set(target_audiences)

    security.declareProtected(
        SilvaPermissions.AccessContentsInformation, 'get_subjects')
    def get_subjects(self):
        """Returns the subjects
        """
        return set(self._subjects or [])

    security.declareProtected(
        SilvaPermissions.AccessContentsInformation, 'get_target_audiences')
    def get_target_audiences(self):
        """Returns the target audiences
        """
        return set(self._target_audiences or [])

InitializeClass(NewsCategorization)



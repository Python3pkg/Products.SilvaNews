# Copyright (c) 2002-2011 Infrae. All rights reserved.
# See also LICENSE.txt
# $Id$
from five import grok
from zope.component import getUtility

# Zope
from AccessControl import ClassSecurityInfo
from App.class_init import InitializeClass
from OFS import SimpleItem

# Silva
from Products.Silva.Publishable import NonPublishable
from Products.SilvaNews.interfaces import IServiceNews
import Products.Silva.SilvaPermissions as SilvaPermissions

# SilvaNews interfaces
from Products.SilvaNews.interfaces import IFilter


class Filter(NonPublishable, SimpleItem.SimpleItem):
    """
    Filter object, a small object that shows a couple of different
    screens to different users, a filter for all NewsItem-objects to
    the editor and a filter (containing some different info) for all
    published NewsItem-objects for the end-users.
    """
    security = ClassSecurityInfo()

    grok.implements(IFilter)
    grok.baseclass()

    def __init__(self, id):
        super(Filter, self).__init__(id)
        self._subjects = []
        self._target_audiences = []

    # ACCESSORS

    security.declareProtected(SilvaPermissions.AccessContentsInformation,
                              'get_subjects')
    def get_subjects(self):
        """Returns a list of subjects
        """
        return list(self._subjects or [])

    security.declareProtected(SilvaPermissions.AccessContentsInformation,
                              'subjects')
    subjects = get_subjects


    security.declareProtected(SilvaPermissions.AccessContentsInformation,
                              'get_target_audiences')
    def get_target_audiences(self):
        """Returns a list of target audiences
        """
        return list(self._target_audiences or [])

    security.declareProtected(SilvaPermissions.AccessContentsInformation,
                              'target_audiences')
    target_audiences = get_target_audiences

    security.declareProtected(SilvaPermissions.ChangeSilvaContent,
                              'set_subjects')
    def set_subjects(self, subjects):
        """Sets the subjects"""
        self._subjects = subjects
        self.synchronize_with_service()

    security.declareProtected(SilvaPermissions.ChangeSilvaContent,
                              'set_target_audiences')
    def set_target_audiences(self, ta):
        self._target_audiences = ta
        self.synchronize_with_service()

    security.declareProtected(SilvaPermissions.ChangeSilvaContent,
                              'synchronize_with_service')
    def synchronize_with_service(self):
        """Checks whether the lists of subjects and target_audiences
        only contain items that the service_news-lists contain (to remove
        items from the object's list that are removed in the service)
        """
        service_news = getUtility(IServiceNews)
        service_subjects = [s[0] for s in service_news.get_subjects()]
        service_target_audiences = [t[0] for t in service_news.get_target_audiences()]

        removed_subjects = []
        removed_target_audiences = []

        subjects = self._subjects[:]
        target_audiences = self._target_audiences[:]

        new_subs = []
        for i in range(len(subjects)):
            s = subjects[i]
            if  s in service_subjects:
                new_subs.append(s)

        new_tas = []
        for i in range(len(target_audiences)):
            ta = target_audiences[i]
            if ta in service_target_audiences:
                new_tas.append(ta)

        self._subjects = new_subs
        self._target_audiences = new_tas

        return removed_subjects + removed_target_audiences

InitializeClass(Filter)

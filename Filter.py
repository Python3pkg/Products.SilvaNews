# Copyright (c) 2002 Infrae. All rights reserved.
# See also LICENSE.txt
# $Revision: 1.12.2.1 $

# Zope
from OFS import SimpleItem
from AccessControl import ClassSecurityInfo
from Globals import InitializeClass
from Products.PageTemplates.PageTemplateFile import PageTemplateFile
from DateTime import DateTime
import OFS

# Silva interfaces
from interfaces import INewsItem
from Products.Silva.interfaces import IAsset

# Silva
from Products.Silva.Asset import Asset
import Products.Silva.SilvaPermissions as SilvaPermissions
from Products.Silva.helpers import add_and_edit

class MetaTypeException(Exception):
    pass

class Filter(Asset):
    """
    Filter object, a small object that shows a couple of different
    screens to different users, a filter for all NewsItem-objects to
    the editor and a filter (containing some different info) for all
    published NewsItem-objects for the end-users.
    """
    security = ClassSecurityInfo()
    
    __implements__ = IAsset

    _allowed_source_types = ['Silva News Publication']

    def __init__(self, id):
        Filter.inheritedAttribute('__init__')(self, id, 'dummy')
        self._keep_to_path = 0
        self._subjects = []
        self._target_audiences = []
        self._excluded_items = []
        self._sources = []


    # ACCESSORS

    security.declareProtected(SilvaPermissions.AccessContentsInformation,
                              'subjects')
    def subjects(self):
        """Returns a list of subjects
        """
        return self._subjects

    security.declareProtected(SilvaPermissions.AccessContentsInformation,
                              'find_sources')
    def find_sources(self):
        """Returns all the sources available for querying
        """
        results = self._query(
            meta_type=self._allowed_source_types,
            sort_on='id',
            is_private=0)

        pp = []
        cpp = '/'.join(self.aq_inner.aq_parent.getPhysicalPath())
        while 1:
            if cpp == '':
                break
            pp.append(cpp)
            cpp = cpp[:cpp.rfind('/')]

        results += self._query(
            meta_type=self._allowed_source_types,
            sort_on='id',
            is_private=1,
            parent_path=pp)

        # remove doubles
        res = []
        urls = []
        for r in results:
            if not r.getURL() in urls:
                res.append(r)
                urls.append(r.getURL())

        return res

    security.declareProtected(SilvaPermissions.AccessContentsInformation,
                              'keep_to_path')
    def keep_to_path(self):
        """Returns true if the item should keep to path
        """
        return self._keep_to_path

    security.declareProtected(SilvaPermissions.AccessContentsInformation,
                              'target_audiences')
    def target_audiences(self):
        """Returns a list of target audiences
        """
        return self._target_audiences


    # MANIPULATORS

    security.declareProtected(SilvaPermissions.AccessContentsInformation,
                              'sources')
    def sources(self):
        """Returns the list of sources
        """
        self.verify_sources()
        return self._sources

    security.declareProtected(SilvaPermissions.ChangeSilvaContent,
                              'add_source')
    def add_source(self, sourcepath, add_or_remove):
        """Add a source
        """
        if add_or_remove:
            if not sourcepath in self._sources:
                self._sources.append(sourcepath)
        else:
            if sourcepath in self._sources:
                self._sources.remove(sourcepath)
        self._p_changed = 1
        self.reindex_object()

    security.declareProtected(SilvaPermissions.ChangeSilvaContent,
                              'verify_sources')
    def verify_sources(self):
        """Verifies the sourcelist against the available sources
        """
        allowedsources = [s.getPath() for s in self.find_sources()]
        do_reindex = 0
        for source in self._sources:
            if not source in allowedsources:
                self._sources.remove(source)
                do_reindex = 1
        if do_reindex:
            self.reindex_object()

    security.declareProtected(SilvaPermissions.ChangeSilvaContent,
                              'set_excluded_item')
    def set_excluded_item(self, objectpath, add_or_remove):
        """Adds or removes an item to or from the excluded_items list
        """
        if add_or_remove:
            if not objectpath in self._excluded_items:
                self._excluded_items.append(objectpath)
        else:
            if objectpath in self._excluded_items:
                self._excluded_items.remove(objectpath)
        self._p_changed = 1

    security.declareProtected(SilvaPermissions.AccessContentsInformation,
                              'excluded_items')
    def excluded_items(self):
        """Returns a list of object-paths of all excluded items
        """
        self.verify_excluded_items()
        return self._excluded_items

    def verify_excluded_items(self):
        do_reindex = 0
        for item in self._excluded_items:
            result = self._query(object_path=[item])
            if not str(item) in [str(i.object_path) for i in result]:
                self._excluded_items.remove(item)
                do_reindex = 1
        if do_reindex:
            self.reindex_object()

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
                              'set_keep_to_path')
    def set_keep_to_path(self, value):
        """
        Sets the keep_to_path property to restrict the searcharea of
        the browser THIS METHOD IS NOT IN USE RIGHT NOW... delete?
        """
        # make sure the var will contain either 0 or 1
        self._keep_to_path = not not value
        self.reindex_object()

    security.declareProtected(SilvaPermissions.ChangeSilvaContent,
                              'synchronize_with_service')
    def synchronize_with_service(self):
        """Checks whether the lists of subjects and target_audiences
        only contain items that the service_news-lists contain (to remove
        items from the object's list that are removed in the service)
        """
        # XXX This isn't called yet from anywhere since the methods it was
        # called from are replaced by metadata functionality
        service_subjects = self.service_news.subjects()
        service_target_audiences = self.service_news.target_audiences()

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

        self.reindex_object()
        return removed_subjects + removed_target_audiences

    security.declareProtected(SilvaPermissions.AccessContentsInformation,
                              'search_items')
    def search_items(self, keywords, meta_types=None):
        """Returns the items from the catalog that have keywords in fulltext.
        """
        keywords = unicode(keywords, 'UTF-8')
        self.verify_sources()
        if not meta_types:
            meta_types = self.get_allowed_meta_types()
        self.verify_excluded_items()

        # replace +'es with spaces so the effect is the same...
        keywords = keywords.replace('+', ' ')

        result = self._query(
            fulltext = keywords.split(' '),
            version_status = 'public',
            path = self._sources,
            subjects = self._subjects,
            target_audiences = self._target_audiences,
            meta_type = meta_types,
            sort_on = 'silva-extrapublicationtime',
            sort_order = 'descending')

        result =  [r for r in result if not r.object_path in
                   self._excluded_items]

        return result


    # HELPERS

    def _query(self, **kw):
        return self.service_catalog(kw)
    
    def _check_meta_types(self, meta_types):
        for type in meta_types:
            if type not in self._allowed_news_meta_types():
                raise MetaTypeException, "Illegal meta_type: %s" % type

    def _allowed_news_meta_types(self):
        return [addable_dict['name']
                for addable_dict in self.filtered_meta_types()
                if self._is_news_addable(addable_dict)]

    def _is_news_addable(self, addable_dict):
        return (
            addable_dict.has_key('instance') and
            INewsItem.isImplementedByInstancesOf(
            addable_dict['instance']))

InitializeClass(Filter)

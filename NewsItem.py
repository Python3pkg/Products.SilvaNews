# Copyright (c) 2002-2008 Infrae. All rights reserved.
# See also LICENSE.txt
# $Revision: 1.35 $

from zope.interface import implements, implementsOnly, implementedBy

# Python
from StringIO import StringIO
from xml.sax import parseString
from xml.sax.handler import ContentHandler

# Zope
from AccessControl import ClassSecurityInfo
from DateTime import DateTime
try:
    from App.class_init import InitializeClass # Zope 2.12
except ImportError:
    from Globals import InitializeClass # Zope < 2.12

# Silva
from silva.core import conf as silvaconf
from silva.core.smi.interfaces import IFormsEditorSupport
from silva.core.services.interfaces import ICataloging
from silva.core.views import views as silvaviews
from Products.Silva import SilvaPermissions
from Products.Silva.helpers import add_and_edit
from Products.Silva.Image import havePIL
from Products.Silva.VersionedContent import VersionedContent
from silva.core.interfaces import IRoot
from Products.Silva.SilvaObject import NoViewError

from Products.SilvaDocument.transform.Transformer import EditorTransformer
from Products.SilvaDocument.transform.base import Context
from Products.SilvaDocument.Document import Document,DocumentVersion

from silvaxmlattribute import SilvaXMLAttribute
from interfaces import INewsItem, INewsItemVersion, INewsPublication

class MetaDataSaveHandler(ContentHandler):
    def startDocument(self):
        self.title = ''
        self.inside_title = False
        self.metadata = {}

    def startElement(self, name, attributes):
        if name == 'h2' and not self.title:
            self.inside_title = True
        elif name == 'meta':
            if (attributes.get('scheme') ==
                    'http://infrae.com/namespace/metadata/silva-news-network'
                    ):
                name = attributes.get('name', '')
                content = attributes.get('content', '')
                self.metadata[name] = self.parse_content(content)

    def endElement(self, name):
        if name == 'h2':
            self.inside_title = False

    def characters(self, data):
        if self.inside_title:
            self.title += data

    def parse_content(self, content):
        return [self.deentitize_and_deescape_pipes(x) for
                    x in content.split('|')]

    def deentitize_and_deescape_pipes(self, data):
        data = data.replace('&pipe;', '|')
        data = data.replace('&lt;', '<')
        data = data.replace('&gt;', '>')
        data = data.replace('&quot;', '"')
        data = data.replace('&amp;', '&')
        return data

class NewsItem(Document):
    """Base class for all kinds of news items.
    """
    security = ClassSecurityInfo()

    #remove the formed editor support interface, as news items
    # don't support the forms-based editor
    implementsOnly(INewsItem, [ i for i in implementedBy(Document) if i != IFormsEditorSupport ])
    silvaconf.baseclass()

    # MANIPULATORS

    security.declareProtected(SilvaPermissions.ApproveSilvaContent,
                              'set_next_version_display_datetime')
    def set_next_version_display_datetime(self, dt):
        """Set display datetime of next version.
        """
        if self._approved_version[0]:
            id = self._approved_version[0]
        elif self._unapproved_version[0]:
            id = self._unapproved_version[0]
        else:
            raise VersioningError,\
                  _('No next version.')
        version = getattr(self, id, None)
        version.set_display_datetime(dt)

    security.declareProtected(SilvaPermissions.ChangeSilvaContent,
                              'set_unapproved_version_display_datetime')
    def set_unapproved_version_display_datetime(self, dt):
        """Set display datetime for unapproved
        """
        if self._unapproved_version == empty_version:
            raise VersioningError,\
                  _('No unapproved version.')

        id = self._unapproved_version[0]
        version = getattr(self, id, None)
        version.set_display_datetime(dt)

    security.declareProtected(SilvaPermissions.AccessContentsInformation,
                                'implements_newsitem')
    def implements_newsitem(self):
        return True

    security.declareProtected(SilvaPermissions.ChangeSilvaContent,
                                'PUT')
    def PUT(self, REQUEST=None, RESPONSE=None):
        """PUT support"""
        # XXX we may want to make this more modular/pluggable at some point
        # to allow more content-types (+ transformations)
        if REQUEST is None:
            REQUEST = self.REQUEST
        if RESPONSE is None:
            RESPONSE = REQUEST.RESPONSE
        content = REQUEST['BODYFILE'].read()
        self.save_title_and_metadata(content)
        self.get_editable().content.saveEditorHTML(content)
        self.sec_update_last_author_info()

    def save_title_and_metadata(self, html):
        handler = MetaDataSaveHandler()
        parseString(html, handler)

        version = self.get_editable()
        version.set_subjects(handler.metadata['subjects'])
        version.set_target_audiences(handler.metadata['target_audiences'])
        # a bit nasty, should perhaps happen in AgendaItem only?
        if hasattr(version, 'start_datetime'):
            version.set_start_datetime(
                DateTime(handler.metadata['start_datetime'][0]))
        if hasattr(version, 'end_datetime'):
            end_datetime = handler.metadata['end_datetime'][0]
            if not end_datetime:
                end_datetime = None
            else:
                end_datetime = DateTime(end_datetime)
            version.set_end_datetime(end_datetime)
        if hasattr(version, 'location'):
            version.set_location(handler.metadata['location'][0])
        version.set_title(handler.title)

InitializeClass(NewsItem)

class NewsItemVersion(DocumentVersion):
    """Base class for news item versions.
    """
    security = ClassSecurityInfo()
    silvaconf.baseclass()
    implements(INewsItemVersion)

    def __init__(self, id):
        NewsItemVersion.inheritedAttribute('__init__')(self, id)
        self._subjects = []
        self._target_audiences = []
        self._display_datetime = None
        self.content = SilvaXMLAttribute('content')

    def clearEditorCache(self):
        """ override this method in DocumentVersion.  There is no
            editor cache for news/agenda items, as they don't use
            the forms-based editor """
        pass

    def _get_document_element(self):
        """returns the document element of this
           version's ParsedXML object.
           for News Items, this is inside a
           silvaxmlattribute"""
        return self.content.get_content().documentElement

    # XXX I would rather have this get called automatically on setting
    # the publication datetime, but that would have meant some nasty monkey-
    # patching would be required...
    security.declareProtected(SilvaPermissions.ChangeSilvaContent,
                                'set_display_datetime')
    def set_display_datetime(self, ddt):
        """set the display datetime

            this datetime is used to determine whether an item should be shown
            in the news viewer, and to determine the order in which the items
            are shown
        """
        self._display_datetime = ddt
        ICataloging(self).reindex()

    security.declareProtected(SilvaPermissions.AccessContentsInformation,
                                'display_datetime')
    def display_datetime(self):
        """returns the display datetime

            see 'set_display_datetime'
        """
        return self._display_datetime

    security.declareProtected(SilvaPermissions.AccessContentsInformation,
                                'idx_display_datetime')
    idx_display_datetime = display_datetime


    security.declareProtected(SilvaPermissions.ChangeSilvaContent,
                              'set_subjects')

    def set_subjects(self, subjects):
        self._subjects = subjects
        ICataloging(self).reindex()

    security.declareProtected(SilvaPermissions.ChangeSilvaContent,
                              'set_target_audiences')
    def set_target_audiences(self, target_audiences):
        self._target_audiences = target_audiences
        ICataloging(self).reindex()

    # ACCESSORS
    security.declareProtected(SilvaPermissions.AccessContentsInformation,
                              'get_intro')
    def get_intro(self, max_size=128):
        """Returns first bit of the news item's content

            this returns all elements up to and including the first
            paragraph, if it turns out that there are more than max_size
            characters in the data returned it will truncate (per element)
            to minimally 1 element
        """
        # something in here needs 'model', so make sure it's available...
        model = self.REQUEST.get('model',None)
        self.REQUEST['model'] = self
        content = self.content._content
        ret = []
        length = 0
        se = self.service_editor
        for child in content.childNodes[0].childNodes:
            if child.nodeName in ('image','source'):
                continue
            # XXX the viewer is set every iteration because the renderView
            # calls of certain elements will set it to something else
            se.setViewer('service_news_sub_viewer')
            add = se.renderView(child)
            if type(add) != unicode:
                add = unicode(add, 'UTF-8')
            if len(add) + length > max_size:
                ret.append(add)
                break
            length += len(add)
            ret.append(add)
            # break after the first <p> node
            #if child.nodeName == 'p':
            #    break
        if model: #restore or remove model
            self.REQUEST['model'] = model
        else:
            try: #for some reason this doesn't always work ???
                #it seems that saving from kupu is broken if this isn't
                #escaped
                del self.REQUEST['model']
            except AttributeError:
                pass
        return '\n'.join(ret)

    security.declareProtected(SilvaPermissions.AccessContentsInformation,
                                'get_thumbnail')
    def get_thumbnail(self, divclass=None):
        """returns an image tag for the tumbnail of the first image in the item

            returns '' if no image is available
        """
        images = self.content._content.documentElement.getElementsByTagName('image')
        if not images:
            return ''
        #check to see if Pil is installed
        if not havePIL:
            return ''
        imgpath = images[0].getAttribute('path').split('/')
        try:
            img = self.restrictedTraverse(imgpath)
        except KeyError:
            return '[broken image]'
        if not img:
            return '[broken image]'
        tag = ('<a class="newsitemthumbnaillink" href="%s">%s</a>' %
                    (self.object().absolute_url(), img.tag(thumbnail=1)))
        if divclass:
            tag = '<div class="%s">%s</div>' % (divclass, tag)
        return tag

    security.declareProtected(SilvaPermissions.AccessContentsInformation,
                                'get_description')
    def get_description(self):
        return self.service_metadata.getMetadataValue(
            self, 'silva-extra', 'content_description')

    def _get_source(self):
        c = self.aq_inner.aq_parent
        while (1):
            if INewsPublication.providedBy(c):
                return c
            if IRoot.providedBy(c):
                return None
            c = c.aq_parent
        return None

    security.declareProtected(SilvaPermissions.AccessContentsInformation,
                              'source_path')
    def source_path(self):
        """Returns the path to the source containing this item
        """
        source = self._get_source()
        if not source:
            return None
        return source.getPhysicalPath()

    security.declareProtected(SilvaPermissions.AccessContentsInformation,
                              'is_private')
    def is_private(self):
        """Returns whether the object is in a private source
        """
        source = self._get_source()
        if not source:
            return False
        return self.service_metadata.getMetadataValue(source,'snn-np-settings','is_private')

    security.declareProtected(SilvaPermissions.AccessContentsInformation,
                              'idx_is_private')
    idx_is_private = is_private

    security.declareProtected(SilvaPermissions.AccessContentsInformation,
                              'subjects')
    def subjects(self):
        """Returns the subjects
        """
        return self._subjects

    security.declareProtected(SilvaPermissions.AccessContentsInformation,
                              'idx_subjects')
    idx_subjects = subjects

    security.declareProtected(SilvaPermissions.AccessContentsInformation,
                              'target_audiences')
    def target_audiences(self):
        """Returns the target audiences
        """
        return self._target_audiences

    security.declareProtected(SilvaPermissions.AccessContentsInformation,
                              'idx_target_audiences')
    idx_target_audiences = target_audiences

    security.declareProtected(SilvaPermissions.AccessContentsInformation,
                              'last_author_fullname')
    def last_author_fullname(self):
        """Returns the userid of the last author, to be used in
        combination with the ZCatalog.  The data this method returns
        can, in opposite to the sec_get_last_author_info data, be
        stored in the ZCatalog without any problems.
        """
        return self.sec_get_last_author_info().fullname()

    security.declareProtected(SilvaPermissions.AccessContentsInformation,
                              'fulltext')
    def fulltext(self):
        """Returns all data as a flat string for full text-search
        """
        s = StringIO()
        self.content.toXML(s)
        content = self._flattenxml(s.getvalue())
        return "%s %s %s %s" % (self.get_title(),
                                      " ".join(self._subjects),
                                      " ".join(self._target_audiences),
                                      content)

InitializeClass(NewsItemVersion)


from Products.Silva.adapters.indexable import IndexableAdapter


class NewsItemVersionIndexableAdapter(IndexableAdapter):

    silvaconf.context(INewsItemVersion)

    def getIndexes(self):
        # Override for news items is it change the content attribute
        # of a document version, the default adapter break.
        return []


class NewsItemView(silvaviews.View):
    """ View on a News Item (either Article / Agenda ) """

    silvaconf.context(INewsItem)

    def render(self):
        """Document uses a grok view, but news items aren't
           ready for that yet, so call back into the silvaviews
           machinery.  Note: this is a direct copy of the last
           part of SilvaObject.view_vesion"""
        self.request.model = self.content
        self.request['model'] = self.content
        try:
            view = self.context.service_view_registry.get_view(
                'public', self.content.meta_type)
        except KeyError:
            msg = 'no public view defined'
            raise NoViewError, msg
        else:
            rendered = view.render()
            try:
                del self.request.model
            except AttributeError, e:
                pass
            return rendered

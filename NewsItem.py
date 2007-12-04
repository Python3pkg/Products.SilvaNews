# Copyright (c) 2002-2007 Infrae. All rights reserved.
# See also LICENSE.txt
# $Revision: 1.35 $

from zope.interface import implements

# Python
from StringIO import StringIO
from xml.sax import parseString
from xml.sax.handler import ContentHandler

# Zope
from AccessControl import ClassSecurityInfo
from DateTime import DateTime
from Globals import InitializeClass

# Silva
from Products.Silva import SilvaPermissions
from Products.Silva.VersionedContent import CatalogedVersionedContent
from Products.Silva.Version import CatalogedVersion
from Products.Silva.interfaces import IVersionedContent
from Products.Silva.helpers import add_and_edit
from Products.Silva.Metadata import export_metadata

from silvaxmlattribute import SilvaXMLAttribute
from Products.SilvaDocument.transform.Transformer import EditorTransformer
from Products.SilvaDocument.transform.base import Context
from Products.Silva.Image import havePIL

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
                    'http://infrae.com/namespaces/metadata/silva-news'
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

class NewsItem(CatalogedVersionedContent):
    """Base class for all kinds of news items.
    """
    security = ClassSecurityInfo()

    implements(IVersionedContent)

    # MANIPULATORS

    #modifaction to make it possible to set the display datetime
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

    #modifaction to make it possible to set the display datetime unapproved versioned content
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

    # ACCESSORS
    security.declareProtected(SilvaPermissions.AccessContentsInformation,
                              'to_xml')
    def to_xml(self, context):
        """Maps to the most useful(?) version
        (public, else unapproved or approved)
        """
        if context.last_version == 1:
            version_id = self.get_next_version()
            if version_id is None:
                version_id = self.get_public_version()
        else:
            version_id = self.get_public_version()

        if version_id is None:
            return

        version = getattr(self, version_id)

        context.f.write('<silva_newsitem id="%s">' % self.id)
        version.to_xml(context)
        context.f.write('</silva_newsitem>')

    security.declareProtected(SilvaPermissions.ChangeSilvaContent,
                                'editor_xml')
    def editor_xml(self):
        browser = 'Mozilla'
        if self.REQUEST['HTTP_USER_AGENT'].find('MSIE') > -1:
            browser = 'IE'

        context = Context(f=StringIO(),
                            last_version=1,
                            url=self.absolute_url(),
                            browser=browser,
                            model=self)
        self.to_xml(context)
        xml = context.f.getvalue()
        return xml

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

class NewsItemVersion(CatalogedVersion):
    """Base class for news item versions.
    XXX making this subclass DocumentVersion does restrict matters,
    but is clearer than doing the same thing in here again which was
    the case before.
    """
    security = ClassSecurityInfo()

    def __init__(self, id):
        # XXX dummy title?
        NewsItemVersion.inheritedAttribute('__init__')(self, id)
        self._subjects = []
        self._target_audiences = []
        self._display_datetime = None
        self.content = SilvaXMLAttribute('content')

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
        self.reindex_object()

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
        self.reindex_object()

    security.declareProtected(SilvaPermissions.ChangeSilvaContent,
                              'set_target_audiences')
    def set_target_audiences(self, target_audiences):
        self._target_audiences = target_audiences
        self.reindex_object()

    # ACCESSORS
    security.declareProtected(SilvaPermissions.AccessContentsInformation,
                              'get_intro')
    def get_intro(self, max_size=1024):
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
        img = self.restrictedTraverse(imgpath)
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
        
    security.declareProtected(SilvaPermissions.AccessContentsInformation,
                              'source_path')
    def source_path(self):
        """Returns the path to the source containing this item
        """
        obj = self.aq_inner.aq_parent
        while (obj.getPhysicalPath() != ('',) and
               not obj.meta_type == 'Silva News Publication'):
            obj = obj.aq_parent
        if obj.getPhysicalPath() != ('',):
            return '/'.join(obj.getPhysicalPath())
        else:
            return None

    security.declareProtected(SilvaPermissions.AccessContentsInformation,
                              'is_private')
    def is_private(self):
        """Returns whether the object is in a private source
        """
        # XXX why not rely on acquisition from source?
        source = self.source_path()
        if source and self.restrictedTraverse(source).is_private():
            return 1
        else:
            return 0

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
                              'info_item')
    def info_item(self):
        return self._info_item

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
 
    security.declareProtected(SilvaPermissions.AccessContentsInformation,
                              'to_xml')
    def to_xml(self, context):
        """Returns the content as a partial XML-document
        """
        export_metadata(self, context)

        f = context.f
        f.write(u'<title>%s</title>' % self.get_title())
        f.write(u'<meta_type>%s</meta_type>' % self.meta_type)
        # XXX really don't know how to deal with this...
        f.write(u'<sta>')
        self.content_xml(context)
        f.write(u'</sta>')
        self.content.toXML(f)

    def content_xml(self, context):
        """Writes all content elements to the XML stream"""
        f = context.f
        for subject in self._subjects:
            f.write(u'<subject>%s</subject>' % self._prepare_xml(subject))
        for audience in self._target_audiences:
            f.write(u'<target_audience>%s</target_audience>' % self._prepare_xml(audience))
    
    def _prepare_xml(self, inputstring):
        inputstring = inputstring.replace(u'&', u'&amp;')
        inputstring = inputstring.replace(u'<', u'&lt;')
        inputstring = inputstring.replace(u'>', u'&gt;')

        return inputstring

    # XXX had to copy this from SilvaDocument.Document...
    def _flattenxml(self, xmlinput):
        """Cuts out all the XML-tags, helper for fulltext (for content-objects)
        """
        # XXX this need to be fixed by using ZCTextIndex or the like
        return xmlinput

InitializeClass(NewsItemVersion)

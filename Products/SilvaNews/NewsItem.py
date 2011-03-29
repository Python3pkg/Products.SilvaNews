# Copyright (c) 2002-2011 Infrae. All rights reserved.
# See also LICENSE.txt
# $Revision: 1.35 $

import re
from types import ListType
from five import grok
from zope.component import getUtility, getMultiAdapter
from zope.i18nmessageid import MessageFactory
from zope.cachedescriptors.property import CachedProperty
from megrok import pagetemplate as pt

# Zope
from AccessControl import ClassSecurityInfo
from App.class_init import InitializeClass
from DateTime import DateTime
from zope.interface import Interface, Invalid, invariant
from zope.schema import Choice, Set, TextLine
from zope.schema.interfaces import IContextSourceBinder
from zope.schema.vocabulary import SimpleVocabulary, SimpleTerm

# Silva
from silva.core.interfaces import IRoot
from silva.core.interfaces.events import IContentPublishedEvent
from silva.core.references.interfaces import IReferenceService
from silva.core.views import views as silvaviews
from silva.core.views.interfaces import IPreviewLayer
from silva.core.smi.interfaces import ISMILayer
from silva.core.contentlayout.contentlayout import ContentLayout
from silva.core.contentlayout.editor import PropertiesPreviewProvider
from silva.core.contentlayout.templates.template import Template, TemplateView
from silva.core.services.interfaces import ICataloging
from silva.core.layout.interfaces import IMetadata
from zeam.form import silva as silvaforms
from zeam.form.silva.form import SilvaDataManager
from zeam.form.silva.actions import EditAction
from zeam.form import base as baseforms
from zeam.form.base.markers import DISPLAY, NO_VALUE

from Products.Silva.VersionedContent import CatalogedVersionedContent
from Products.Silva.Version import CatalogedVersion
from Products.Silva import SilvaPermissions
from Products.Silva.transform.renderer.xsltrendererbase import XSLTTransformer
from Products.SilvaNews.interfaces import (INewsItem, INewsItemVersion, 
                                           INewsItemTemplate)
from Products.SilvaNews.interfaces import (INewsPublication, IServiceNews,
     INewsViewer, INewsItemSchema)
from Products.SilvaNews.datetimeutils import datetime_to_unixtimestamp

_ = MessageFactory('silva_news')

#for formatting the time according to Bethel's standards
time_re = re.compile('((:00)|((12:00 )?(am|pm)))',re.I)
def time_replace(matchobj):
    g0 = matchobj.group(0)
    if g0 == 'am':
        return 'a.m.'
    elif g0 == 'pm':
        return 'p.m.'
    elif g0 == '12:00 pm':
        return 'noon'
    elif g0 == '12:00 am':
        return 'midnight'
    elif g0 == ':00': #strip it!
        pass
    return ''

class NewsItem(CatalogedVersionedContent):
    """Base class for all kinds of news items.
    """
    grok.baseclass()
    grok.implements(INewsItem)

    security = ClassSecurityInfo()
    # MANIPULATORS

    security.declareProtected(SilvaPermissions.ApproveSilvaContent,
                              'set_next_version_display_datetime')
    def set_next_version_display_datetime(self, dt):
        """Set display datetime of next version.
        """
        version = getattr(self, self.get_next_version())
        version.set_display_datetime(dt)

    security.declareProtected(SilvaPermissions.ChangeSilvaContent,
                              'set_unapproved_version_display_datetime')
    def set_unapproved_version_display_datetime(self, dt):
        """Set display datetime for unapproved
        """
        version = getattr(self, self.get_unapproved_version())
        version.set_display_datetime(dt)
InitializeClass(NewsItem)

class NewsItemVersion(CatalogedVersion, ContentLayout):
    """Base class for news item versions.
    """
    security = ClassSecurityInfo()
    grok.baseclass()
    grok.implements(INewsItemVersion)

    def __init__(self, id):
        super(NewsItemVersion, self).__init__(id)
        ContentLayout.__init__(self, id)
        self._subjects = []
        self._target_audiences = []
        self._display_datetime = None
        self._external_link = None
        self._link_method = 'article'

    # XXX I would rather have this get called automatically on setting
    # the publication datetime, but that would have meant some nasty monkey-
    # patching would be required...
    security.declareProtected(SilvaPermissions.ChangeSilvaContent,
                                'set_display_datetime')
    def set_display_datetime(self, ddt, reindex=True):
        """set the display datetime

            this datetime is used to determine whether an item should be shown
            in the news viewer, and to determine the order in which the items
            are shown
        """
        self._display_datetime = ddt
        if reindex:
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

    security.declareProtected(SilvaPermissions.AccessContentsInformation,
                                'get_display_datetime')
    get_display_datetime = display_datetime

    security.declareProtected(SilvaPermissions.ChangeSilvaContent,
                              'set_subjects')
    def set_subjects(self, subjects, reindex=True):
        self._subjects = list(subjects)
        if reindex:
            ICataloging(self).reindex()
            
    security.declareProtected(SilvaPermissions.ChangeSilvaContent,
                              'set_link_method')
    def set_link_method(self, method):
        self._link_method = method

    security.declareProtected(SilvaPermissions.ChangeSilvaContent,
                              'set_external_link')
    def set_external_link(self, link):
        self._external_link = link

    security.declareProtected(SilvaPermissions.ChangeSilvaContent,
                              'set_target_audiences')
    def set_target_audiences(self, target_audiences, reindex=True):
        self._target_audiences = list(target_audiences)
        if reindex:
            ICataloging(self).reindex()

    security.declareProtected(SilvaPermissions.AccessContentsInformation,
                                'get_thumbnail')
    def get_thumbnail(self, divclass=None):
        """returns an image tag for the tumbnail of the first image in the item

            returns '' if no image is available
        """
        image = self.get_thumbnail_image()
        if image is None:
            return u''
        tag = (u'<a class="newsitemthumbnaillink" href="%s">%s</a>' %
               (self.article_url(), image.tag(thumbnail=1)))
        if divclass:
            tag = u'<div class="%s">%s</div>' % (divclass, tag)
        return tag

    security.declareProtected(SilvaPermissions.AccessContentsInformation,
                                'get_thumbnail_image')
    def get_thumbnail_image(self):
        preview = IMetadata(self.get_content())('syndication','img-preview')
        if preview:
            img = self.restrictedTraverse(preview, None)
            return img
        return None
        #XXX this is the new 'references' way, but we aren't pulling the
        #    first image from the doc content anymore, we're using metadata
        images = self.content.documentElement.getElementsByTagName('image')
        if not images:
            return None
        reference_name = images[0].getAttribute('reference')
        service = getUtility(IReferenceService)
        reference = service.get_reference(self, name=reference_name)
        if reference is None:
            return None
        return reference.target

    security.declareProtected(SilvaPermissions.AccessContentsInformation,
                                'get_description')
    def get_description(self):
        return self.service_metadata.getMetadataValue(
            self, 'syndication', 'teaser')

    def _get_source(self):
        c = self.aq_inner.aq_parent
        while True:
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
        return self.service_metadata.getMetadataValue(
            source, 'snn-np-settings', 'is_private')

    security.declareProtected(SilvaPermissions.AccessContentsInformation,
                              'idx_is_private')
    idx_is_private = is_private

    security.declareProtected(SilvaPermissions.AccessContentsInformation,
                              'get_subjects')
    def get_subjects(self):
        """Returns the subjects
        """
        return list(self._subjects or [])

    security.declareProtected(SilvaPermissions.AccessContentsInformation,
                              'subjects')
    subjects = get_subjects

    security.declareProtected(SilvaPermissions.AccessContentsInformation,
                              'idx_subjects')
    idx_subjects = get_subjects

    security.declareProtected(SilvaPermissions.AccessContentsInformation,
                              'get_target_audiences')
    def get_target_audiences(self):
        """Returns the target audiences
        """
        return list(self._target_audiences or [])
    
    security.declareProtected(SilvaPermissions.AccessContentsInformation,
                              'get_external_link')
    def get_external_link(self):
        return self._external_link
    
    security.declareProtected(SilvaPermissions.AccessContentsInformation,
                              'external_link')
    external_link = get_external_link

 
    security.declareProtected(SilvaPermissions.AccessContentsInformation,
                              'get_link_method')
    def get_link_method(self):
        return self._link_method

    security.declareProtected(SilvaPermissions.AccessContentsInformation,
                              'link_method')
    link_method = get_link_method
    
    security.declareProtected(SilvaPermissions.AccessContentsInformation,
                              'article_url')
    def article_url(self):
        """compute the url for this item.  Different from absolute_url, this
           will return the external link if settings dictacte"""
        if self._link_method == 'external_link':
            return self.external_link()
        return self.get_content().absolute_url()
    
    security.declareProtected(SilvaPermissions.AccessContentsInformation,
                              'target_audiences')
    target_audiences = get_target_audiences

    security.declareProtected(SilvaPermissions.AccessContentsInformation,
                              'idx_target_audiences')
    idx_target_audiences = get_target_audiences

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
        keywords = list(self._subjects)
        keywords.extend(self._target_audiences)
        #XXX not implemented for contentlayout
        #for now, add the title to get the tests to work
        keywords.extend(self.get_title().split())
        #keywords.extend(super(NewsItemVersion, self).fulltext())
        return " ".join(keywords)

    security.declareProtected(SilvaPermissions.AccessContentsInformation,
                              'publication_time')
    def publication_time(self):
        binding = self.service_metadata.getMetadata(self)
        return binding.get('silva-extra', 'publicationtime')

    security.declareProtected(SilvaPermissions.AccessContentsInformation,
                              'sort_index')
    def sort_index(self):
        dt = self.display_datetime()
        if dt:
            return datetime_to_unixtimestamp(dt)
        return None

    security.declareProtected(SilvaPermissions.AccessContentsInformation,
                              'format_time')
    def format_time(self,start,end=None, sep=' | '):
        """helper func to format the time to bethel's
           official standard"""
        def doTime1(t):
            a = t.AMPMMinutes()
            a = time_re.sub(time_replace,a)
            if a[0] == '0':
                return a[1:]
            return a
        def doTime2(ta,tb):
            a = doTime1(ta)
            b = doTime1(tb)
            #if the two times aren't on the same day
            if ta.parts()[0:3] != tb.parts()[0:3]:
                #XXX not sure what to do here?
                #there was an event which started at 6pm April 3 and
                # went through 6pm April 4.  The date was "6-4" with no
                # indication that the even spanned multiple days
                pass
            #same part of day (am or pm)
            if ta.ampm() == tb.ampm() and a not in ('noon','midnight'):
                return a[:-5] + u'\u2013' + b
            else:
                return a + u'\u2013' + b

        #first, if start has no time, return empty
        if start.hour() == 0 and start.minute() == 0:
            return ''
        if not end or start == end or (end.hour()==0 and end.minute() == 0):
            return sep + doTime1(start)
        else:
            return sep + doTime2(start,end)
        
    security.declareProtected(SilvaPermissions.AccessContentsInformation,
                              'format_date_line')
    def format_date_line(self, start, end=None, sep=' | '):
        """formats the date line like 
        May 18, 2010 | 5:43 p.m.
        for Bethel's news story style
        """
        if end is None or start.Date() == end.Date():
            time = self.format_time(start, sep=sep)
            return start.strftime('%B %d, %Y') + time
        else: 
            if start.Month() == end.Month() and start.year() == end.year():
                return start.strftime('%B %d - ') + end.strftime('%d, %Y')
            elif start.year() == end.year():
                return start.strftime('%B %d - ') + end.strftime('%B %d, %Y')
            else:
                return start.strftime('%B %d - ') + end.strftime('%B %d')
InitializeClass(NewsItemVersion)

class ViewNewsProperties(silvaforms.form.ZopeForm, baseforms.Form):
    """Form for viewing the news properties.  This is displayed in the
       right column of the news story template when previewing or
       in the layout editor.
       
       Note: we can't use zeam.form.silva.forms.ZMIForm (which is essentially
       what the base classes are) because ZMIForm requires ViewManagementScreens
    """
    
    grok.context(INewsItemVersion)
    grok.require("silva.ReadSilvaContent")
    
    prefix = 'newsproperties'
    ignoreRequest = True
    ignoreContent = False
    mode = DISPLAY
    dataManager = SilvaDataManager
    label = "News Properties"
    fields = silvaforms.Fields(INewsItemSchema)
    
class ViewNewsPropertiesTemplate(baseforms.form_templates.FormTemplate):
    """ViewNewsProperties has a custom template"""
    pt.view(ViewNewsProperties)

class SupportsEmptyValueEditAction(EditAction):
    """This is needed because zeam.form.ztk's EditAction passes when
       a text field's value is empty, rather than setting the value
       to empty/none/default, etc
       XXX: NOTE: this can be removed once the bug in zeam is fixed"""
    
    def applyData(self, form, content, data):
        for field in form.fields:
            value = data.get(field.identifier)
            if value is NO_VALUE and not field.required:
                value = data.getDefault(field)
            content.set(field.identifier, value)
        
class EditNewsProperties(silvaforms.form.ZopeForm, baseforms.Form):
    """Form for editing the news properties of a news item version.
       This is displayed in the 'edit properties' dialog in the layout
       editor
       
       We put this under the ISMILayer so it can take full advantage of
       automatic resource inclusion (css/js)
       
       Note: we can't use zeam.form.silva.forms.SilvaForm (or SMIForm)
       because it's __call__ wraps the form around a layout (the SMI layout).
       Since this is displayed in a popup, that is not desired.  It would
       be possible to use it anyways, but define a new (empty) layout, however
       that is too much work to have a form with it's own (empty) layout.
    """
    grok.context(INewsItemVersion)
    grok.layer(ISMILayer)
    grok.require("silva.ChangeSilvaContent")
    prefix = 'newsproperties'
    ignoreRequest = False
    ignoreContent = False
    dataManager = SilvaDataManager
    label = "Edit News Properties"
    fields = silvaforms.Fields(INewsItemSchema)
    actions = silvaforms.Actions(SupportsEmptyValueEditAction())
    
class EditNewsPropertiesTemplate(baseforms.form_templates.FormTemplate):
    """EditNewsProperties also has it's own template"""
    pt.view(EditNewsProperties)

class NewsPropertiesPortlet(silvaviews.Viewlet):
    """Portlet to display the news properties in the right
       column of the news story template ONLY when previewing the content.
       This is so the news properties can be displayed when previewing
       (since they aren't shown anywhere else, and the news properties
       tool is disabled when the content is published)
    """
    grok.viewletmanager(PropertiesPreviewProvider)
    grok.context(INewsItem)
    grok.require("silva.ReadSilvaContent")
    
    def render(self):
        """render the 'viewnewsproperties' browser view if the request is
         for the ++preview++ or ++layouteditor++.  'viewnewsproperties' displays
         the news properties as a zeam display form."""
        if IPreviewLayer.providedBy(self.request):
            ad = getMultiAdapter((self.context.get_previewable(), self.request),
                                 name='viewnewsproperties')
            return ad()
        #viewlets ALWAYS need to return a string or unicode
        return ""

class NewsItemViewMixin(object):
    """  Mixin to gather common code between the multiple
         news item views
    """
    
    def get_real_content(self):
        """sometimes this mixin is used as part of an ITemplateView, in which
           case the content (NewsItemVersion or whatever) is actually the
           'version' attribute, NOT the 'content' attribute
        """
        content = None
        if hasattr(self, 'content'):
            content = self.content
        elif hasattr(self, 'version'):
            #self.version (rather than self.content) happens when this mixin
            # is part of a silva.core.contentlayout.ITemplateView
            content = self.version
        return content
    
    @CachedProperty
    def article_date(self):
        content = self.get_real_content()
        article_date = content.display_datetime()
        if not article_date:
            article_date = content.publication_time()
        if article_date:
            news_service = getUtility(IServiceNews)
            return news_service.format_date(article_date)
        return u''

class NewsItemListItemView(NewsItemViewMixin, silvaviews.View):
    """ Render as a list items (search results)
    """
    grok.context(INewsItem)
    grok.name('search_result')

    @CachedProperty
    def article(self):
        return IMetadata(self.context)('syndication','teaser')

@grok.global_utility
class NewsItemTemplate(Template):
    """Custom Content Template for News Items"""
    grok.implements(INewsItemTemplate)
    grok.name('Products.SilvaNews.NewsItem.NewsItemTemplate')
    
    name = "News Item (standard)"
    description = __doc__
    icon = "www/newsitem-layout-icon.png"
    slotnames = ['newsitemcontent']
    
class NewsItemTemplateView(NewsItemViewMixin, TemplateView):
    grok.context(INewsItemTemplate)
    grok.name(u'')
    
@grok.subscribe(INewsItemVersion, IContentPublishedEvent)
def news_item_published(content, event):
    if content.display_datetime() is None:
        now = DateTime()
        content.set_display_datetime(now)

@grok.adapter(INewsItem)
@grok.implementer(INewsViewer)
def get_default_viewer(context):
    """Adapter factory to get the contextual news viewer for a news item
    """
    parents = context.aq_chain[1:]
    for parent in parents:
        if IRoot.providedBy(parent):
            return None
        if INewsViewer.providedBy(parent):
            return parent
        if INewsPublication.providedBy(parent):
            default = parent.get_default()
            if default and INewsViewer.providedBy(default):
                return default
    return None


from cgi import escape

from five import grok
from zope.interface import Interface, alsoProvides
from zope.schema.interfaces import ISet
from zope.schema import Set
from silva.core.layout.jquery.interfaces import IJQueryResources
from zeam.form.base.markers import INPUT, DISPLAY
from zeam.form.ztk.fields import (SchemaField, SchemaFieldWidget,
    registerSchemaField)
from silva.core import conf as silvaconf
from zeam.form.base.widgets import WidgetExtractor
from zeam.form.base.markers import NO_VALUE


def register():
    registerSchemaField(TreeSchemaField, ITree)


class ITree(ISet):
    """ Sequence schema interface
    """

    def get_tree(context):
        """get the selection tree"""


class Tree(Set):
    """ Sequence Field
    """
    grok.implements(ITree)

    def __init__(self, **kw):
        tree = kw.get('tree', None)
        if tree is None:
            raise ValueError('`tree` keyword argument required.')
        else:
            del kw['tree']

        if callable(tree):
            self.get_tree = tree
        else:
            self.tree = tree

        super(Tree, self).__init__(**kw)

    def get_tree(self, context):
        return self.tree


class TreeSchemaField(SchemaField):
    """ zeam schema field
    """


NOTCHECKED = 1 << 1
CHECKED = 1 << 2
UNDETERMINED = NOTCHECKED | CHECKED


def build_html_tree(node, vocabulary, value, _depth=0, _force_checked=False):
    status = NOTCHECKED
    if node.id() == 'root':
        html = ''
        for child in node.children():
            child_status, child_html = build_html_tree(
                child, vocabulary, value, _depth=1)
            status |= child_status
            html += child_html
        return status, html

    item = vocabulary.getTerm(node.id())

    if _force_checked or item.value in value:
        status = CHECKED

    html_children = ""
    if node.children():
        html_children = "<ul>"
        for child in node.children():
            child_status, child_html = build_html_tree(child, vocabulary, value,
                _depth=_depth+1, _force_checked=(status==CHECKED))
            status |= child_status
            html_children += child_html
        html_children += "</ul>"

    classes = set()

    if status == UNDETERMINED:
        classes.add('jstree-undetermined')
    elif status & CHECKED:
        classes.add('jstree-checked')
    else:
        classes.add('jstree-unchecked')

    if (UNDETERMINED == status or _depth <= 0) and node.children():
        classes.add('jstree-open')

    html = '<li id="%s" class="%s"><a href="#">%s</a>' % (
        escape(node.id(), True), " ".join(classes), escape(node.title()))
    html += html_children
    html += "</li>"
    return status, html


class ITreeResources(IJQueryResources):
    silvaconf.resource('jquery.jstree.js')
    silvaconf.resource('tree.css')
    silvaconf.resource('tree.js')


class TreeWidgetInput(SchemaFieldWidget):
    grok.adapts(TreeSchemaField, Interface, Interface)
    grok.name(str(INPUT))

    def update(self):
        alsoProvides(self.request, ITreeResources)
        super(TreeWidgetInput, self).update()

    def HTMLTree(self):
        field = self.component.get_field()
        tree = field.get_tree(self.form)
        vocabulary = field.value_type.vocabulary(self.form.context)
        status, html = build_html_tree(tree,
            vocabulary,
            self.inputValue().split('|'))
        return html

    def valueToUnicode(self, value):
        if value is not NO_VALUE:
            return u'|'.join(value)
        return u''


class TreeWidgetDisplay(TreeWidgetInput):
    grok.name(str(DISPLAY))


class TreeWidgetExtractor(WidgetExtractor):
    grok.adapts(TreeSchemaField, Interface, Interface)

    def extract(self):
        value, error = super(TreeWidgetExtractor, self).extract()
        if value is NO_VALUE:
            return value, error
        vocabulary = self.component.get_field().value_type.vocabulary(
            self.form.context)
        choices = set()
        for choice in value.split('|'):
            choices.add(vocabulary.getTerm(choice).value)
        return choices, error


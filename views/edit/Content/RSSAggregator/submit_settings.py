## Script (Python) "newsviewer_submit"
##bind container=container
##bind context=context
##bind namespace=
##bind script=script
##bind subpath=traverse_subpath
##parameters=
##title=
##
from Products.Formulator.Errors import ValidationError, FormValidationError

# I18N stuff
from Products.Silva.i18n import translate as _


model = context.REQUEST.model
view = context
try:
    result = view.form.validate_all(context.REQUEST)
except FormValidationError, e:
    return view.tab_edit(message_type="error", message=view.render_form_errors(e))

model.sec_update_last_author_info()

model.set_feeds(result['rss_feeds'])

m = _('Viewer data changed', 'silva_news')
msg = unicode(m)

return view.tab_edit(message_type="feedback", message=msg)

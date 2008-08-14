## Script (Python) "agendaviewer_submit"
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

if model.number_to_show_archive() != result['number_to_show_archive']:
    model.set_number_to_show_archive(result['number_to_show_archive'])

if model.days_to_show() != result['days_to_show']:
    model.set_days_to_show(result['days_to_show'])

for id, path in model.findfilters_pairs():
    if path in result['filters']:
        model.set_filter(path, 1)
    else:
        model.set_filter(path, 0)

m = _('Viewer data changed', 'silva_news')
msg = unicode(m)

return view.tab_edit(message_type="feedback", message=msg)

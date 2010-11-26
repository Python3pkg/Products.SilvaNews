## Script (Python) "tab_metadata_submit"
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
form = context.form
messages = []

try:
    result = form.validate_all(context.REQUEST)
except FormValidationError, e:
    m = _('Input form errors ${errors}',
          mapping={'errors':context.render_form_errors(e)})
    msg = unicode(m)
    return context.tab_edit(message_type="error", message=msg )

if model.subjects() != result['subjects']:
    model.set_subjects(result['subjects'])
    m = _('subjects changed', 'silva_news')
    msg = unicode(m)
    messages.append(msg)

if model.target_audiences() != result['target_audiences']:
    model.set_target_audiences(result['target_audiences'])
    m = _('target audiences changed', 'silva_news')
    msg = unicode(m)
    messages.append(msg)

if model.keep_to_path() != result['keep_to_path']:
    model.set_keep_to_path(result['keep_to_path']=='1')
    m = _('stick to path changed', 'silva_news')
    msg = unicode(m)
    messages.append(msg)


m = _('Settings changed for: ', 'silva_news')
msg = unicode(m)

msg = msg + u', '.join(messages)

return context.tab_edit(message_type="feedback", message=msg)

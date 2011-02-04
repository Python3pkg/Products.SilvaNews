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

model = context.REQUEST.model
form = context.form
messages = []

try:
    result = form.validate_all(context.REQUEST)
except FormValidationError, e:
    m = 'Input form errors' + context.render_form_errors(e)
    msg = unicode(m)
    return context.tab_edit(message_type="error", message=msg)

if model.subjects() != result['subjects']:
    model.set_subjects(result['subjects'])
    m = 'subjects changed'
    msg = unicode(m)
    messages.append(msg)

if model.target_audiences() != result['target_audiences']:
    model.set_target_audiences(result['target_audiences'])
    m = 'target audiences changed'
    msg = unicode(m)
    messages.append(msg)

if model.keep_to_path() != result['keep_to_path']:
    model.set_keep_to_path(result['keep_to_path']=='1')
    m = 'stick to path changed'
    msg = unicode(m)
    messages.append(msg)


m = 'Settings changed for: '
msg = unicode(m)

msg = msg + u', '.join(messages)

return context.tab_edit(message_type="feedback", message=msg)

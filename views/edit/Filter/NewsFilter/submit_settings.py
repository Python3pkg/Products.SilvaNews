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
form = context.settingsform
rssform = context.rssform
messages = []

try:
    result = form.validate_all(context.REQUEST)
except FormValidationError, e:
    return context.tab_edit(message_type="error", message='Input form errors %s' % context.render_form_errors(e))

try:
    rss_result = rssform.validate_all(context.REQUEST)
except FormValidationError, e:
    return context.tab_edit(message_type="error", message='RSS form errors %s' % context.render_form_errors(e))

if model.subjects() != result['subjects']:
    model.set_subjects(result['subjects'])
    messages.append('subjects changed')

if model.target_audiences() != result['target_audiences']:
    model.set_target_audiences(result['target_audiences'])
    messages.append('target audiences changed')

if model.show_agenda_items() != result['show_agenda_items']:
    model.set_show_agenda_items(result['show_agenda_items'])
    messages.append('show agendaitems changed')

if model.keep_to_path() != result['keep_to_path']:
    model.set_keep_to_path(result['keep_to_path'])
    messages.append('stick to path changed')

# RSS export disabled, might want to turn it on later
"""
if model.allow_rss_export() != result['allow_rss_export']:
    model.set_allow_rss_export(result['allow_rss_export'])
    messages.append('allow rss export changed')

if model.rss_description() != rss_result['rss_description']:
    model.set_rss_description(rss_result['rss_description'])
    messages.append('rss description changed')

if model.rss_link() != rss_result['rss_link']:
    model.set_rss_link(rss_result['rss_link'])
    messages.append('rss link changed')

if model.rss_copyright() != rss_result['rss_copyright']:
    model.set_rss_copyright(rss_result['rss_copyright'])
    messages.append('rss copyright changed')

if model.allow_rss_search() != rss_result['allow_rss_search']:
    model.set_allow_rss_search(rss_result['allow_rss_search'])
    messages.append('allow rss search changed')

if model.rss_search_description() != rss_result['rss_search_description']:
    model.set_rss_search_description(rss_result['rss_search_description'])
    messages.append('rss search description')
"""
return context.tab_edit(message_type="feedback", message="Settings changed for: %s" % (context.quotify_list(messages)))

##parameters=refs=None

request = context.REQUEST
model = request.model
view = context

from DateTime import DateTime
from Products.Formulator.Errors import FormValidationError

# Check whether there's any checkboxes checked at all...
if not refs:
    return view.tab_status(
        message_type='error', 
        message='Nothing was selected, so no approval was requested.')

try:
    result = view.tab_status_form.validate_all_to_request(request)
except FormValidationError, e:
    return view.tab_status(
        message_type="error", 
        message=view.render_form_errors(e),
        refs=refs)

publish_datetime = result['publish_datetime']
publish_now_flag = result['publish_now_flag']
expiration_datetime = result['expiration_datetime']
clear_expiration_flag = result['clear_expiration']

#if not publish_now_flag and not publish_datetime:
#    return view.tab_status(
#        message_type="error", 
#        message="First set a publish time")
 
now = DateTime()

msg = []
approved_ids = []
not_approved = []
not_approved_refs = []
no_date_refs = []

get_name = context.tab_status_get_name

for ref in refs:
    obj = model.resolve_ref(ref)
    if obj is None:
        continue
    if not obj.implements_versioning():
        not_approved.append((get_name(obj), 'not a versionable object'))
        not_approved_refs.append(ref)
        continue
    if not obj.get_unapproved_version():
        not_approved.append((get_name(obj), 'no unapproved version'))
        not_approved_refs.append(ref)
        continue
    if obj.is_version_approval_requested():
        not_approved.append((get_name(obj),'approval already requested'))
        not_approved_refs.append(ref)
        continue

    # check if the metadata description field is set for news items
    if hasattr(obj, 'implements_newsitem') and obj.implements_newsitem():
        version = getattr(obj, obj.get_unapproved_version())
        binding = context.service_metadata.getMetadata(version)
        if not binding.get('silva-extra', 'description', acquire=False):
            not_approved.append((get_name(obj), 
                                'description not filled in'))
            not_approved_refs.append(ref)
            continue

    # publish
    if publish_now_flag:
        obj.set_unapproved_version_publication_datetime(now)
    elif publish_datetime:
        obj.set_unapproved_version_publication_datetime(publish_datetime)
    elif not obj.get_unapproved_version_publication_datetime():
        # no date set, neither on unapproved version nor in tab_status form
        not_approved.append((get_name(obj), 'no publication time set'))
        no_date_refs.append(ref)
        continue
    # expire
    if clear_expiration_flag:
        obj.set_unapproved_version_expiration_datetime(None)
    elif expiration_datetime:
        obj.set_unapproved_version_expiration_datetime(expiration_datetime)

    message = '''\
Request for approval via a bulk request in the publish screen of /%s
(automatically generated message)''' % model.absolute_url(1)
    obj.request_version_approval(message)    
    approved_ids.append(get_name(obj))

if approved_ids:
    request.set('redisplay_timing_form', 0)
    msg.append('Request approval for: %s' % view.quotify_list(approved_ids))

if not_approved:
    msg.append('<span class="error">No request for approval on: %s</span>' % view.quotify_list_ext(not_approved))

if hasattr(context, 'service_messages'):
    context.service_messages.send_pending_messages()
    
return view.tab_status(message_type='feedback', message=('<br />'.join(msg)), refs=no_date_refs)

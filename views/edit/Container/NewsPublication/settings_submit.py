## Script (Python) "settings_submit"
##bind container=container
##bind context=context
##bind namespace=
##bind script=script
##bind subpath=traverse_subpath
##parameters=
##title=
##
view = context
request = view.REQUEST
model = request.model

message = 'Nothing changed.'
current_private = model.is_private()
is_private = request.has_key('is_private')

if is_private != current_private:
    model.set_private(is_private)
    message = 'Settings changed.'
    model.sec_update_last_author_info()

return view.tab_edit(message_type="feedback", message=message)

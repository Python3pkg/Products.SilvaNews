## Script (Python) "get_user_role"
##bind container=container
##bind context=context
##bind namespace=
##bind script=script
##bind subpath=traverse_subpath
##parameters=
##title=
##
model = context.REQUEST.model
user = context.REQUEST.AUTHENTICATED_USER
if user.has_role(['Editor', 'ChiefEditor', 'Manager'], model):
    return 'Editor'
elif user.has_role(['Author'], model):
    return 'Author'
elif user.has_role(['Reader'], model):
    return 'Reader'
else:
    return 'Other'

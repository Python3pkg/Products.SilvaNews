## Script (Python) "search"
##bind container=container
##bind context=context
##bind namespace=
##bind script=script
##bind subpath=traverse_subpath
##parameters=query
##title=
##
view = context
request = view.REQUEST
model = request.model

if not request.has_key('query') or not request['query']:
    return None

results = model.search_items(query)

## Script (Python) "render_helper"
##bind container=container
##bind context=context
##bind namespace=
##bind script=script
##bind subpath=traverse_subpath
##parameters=version
##title=
##
view = context

if view.REQUEST.has_key('query') and view.REQUEST['query']:
    return view.search_news()
elif view.REQUEST.has_key('view') and view.REQUEST['view'] == 'view_archive':
    return view.view_archive()
else:
    return view.view_news()

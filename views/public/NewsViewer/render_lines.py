## Script (Python) "render_lines"
##bind container=container
##bind context=context
##bind namespace=
##bind script=script
##bind subpath=traverse_subpath
##parameters=data
##title=
##
if data is None:
   return ''
#lines = data.split('\n\n')
return '<br>'.join(data)

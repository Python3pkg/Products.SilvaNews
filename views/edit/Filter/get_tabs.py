## Script (Python) "get_tabs"
##bind container=container
##bind context=context
##bind namespace=
##bind script=script
##bind subpath=traverse_subpath
##parameters=
##title=
##
# define name, id, up_id
return [('Sources', 'tab_edit', 'tab_edit'),
        ('Items', 'tab_edit_items', 'tab_edit'),
        ('Metadata', 'tab_metadata', 'tab_metadata'),
        ('Access', 'tab_access', 'tab_access'),
       ]

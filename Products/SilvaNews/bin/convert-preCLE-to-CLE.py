#!/usr/bin/python

#Move all plain article items to the bottom of the file, since they may reference
#other content (like images) which may not have been imported yet. Also remove
#flash objects and set the default status of all items to closed.

from lxml import etree

output = open("out.xml", "w")
tree = etree.parse("silva.xml")

contents = tree.xpath("/a:silva/a:*/a:content",
                     namespaces={"a": "http://infrae.com/ns/silva"})

def fixIt(node):
    for c in node:
        elements = c.xpath("*")

        for e in elements:
            fixIt(e)

            if e.tag.endswith("plainarticle"):
                c.remove(e)
                c.append(e)
            elif e.tag.endswith("unknown_content"):
                id = e.get("id")
                if id and (id.endswith(".swf") or id.endswith(".flv")):
                    c.remove(e)
                    print "warning: removing what appears to be flash content: %s" % id

fixIt(contents)

output.write(etree.tostring(tree, xml_declaration=True, encoding="utf-8").replace("<status>public</status>", "<status>closed</status>"))
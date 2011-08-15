# Copyright (c) 2002-2011 Infrae. All rights reserved.
# See also LICENSE.txt
# $Revision: 1.2 $

"""Simple generic tree implementation"""

class DuplicateIdError(RuntimeError):
    """Raised when an id is already in use"""

class Node:
    """A single tree node"""
    def __init__(self, id, title):
        self._id = id
        self._title = title
        self._children = []
        self._parent = None
        self._root = None

    def id(self):
        return self._id

    def title(self):
        return self._title

    def children(self):
        return self._children

    def parent(self):
        return self._parent

    def set_id(self, id):
        if id in self._root.getIds():
            raise DuplicateIdError('id already in use - %s' % id)
        del self._root._references[self._id]
        self._id = id
        self._root._references[id] = self

    def set_title(self, title):
        self._title = title

    def addChild(self, child):
        if child.id() in self._root.getIds():
            raise DuplicateIdError, 'id already in use - %s' % child.id()
        self._children.append(child)
        child._parent = self
        child._setRoot(self._root)

    def removeChild(self, child):
        for c in child.children():
            child.removeChild(c)
        del self._children[self._children.index(child)]
        self._root._delElement(child)
        del child._parent
        del child._root

    def _setRoot(self, root):
        self._root = root
        self._root._references[self._id] = self

    def getElements(self):
        """returns a list of all the elements, in order

            depth first
        """
        ret = []
        for el in self._children:
            ret.append(el)
            ret += el.getElements()
        return ret

    def find(self, id):
        if self._id == id:
            return self
        for child in self._children:
            match = child.find(id)
            if match:
                return match
        return None

    def get_subtree_ids(self, max_depth=None):
        results = [self._id]
        if max_depth is not None and max_depth <= 0:
            return results
        for el in self._children:
            results.extend(el.get_subtree_ids(
                max_depth=max_depth and (max_depth - 1)))
        return results

    def ancestors(self):
        current = self
        while current._parent is not None:
            yield current
            current = current._parent

    def ancestors_ids(self):
        for node in self.ancestors():
            yield node._id


class Root(Node):
    def __init__(self):
        Node.__init__(self, 'root', 'root')
        self._references = {'root': self}
        self._root = self

    def getElement(self, id):
        """returns an element by id"""
        return self._references[id]

    def getIds(self):
        """returns list of all used ids"""
        return self._references.keys()

    def _delElement(self, child):
        del self._references[child.id()]



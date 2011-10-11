from zope.interface import implements

from OFS.SimpleItem import SimpleItem
from Products.PageTemplates.PageTemplateFile import PageTemplateFile
from Products.PluginIndexes.interfaces import IPluggableIndex
from Products.PluginIndexes.common.util import parseIndexRequest
from Products.PluginIndexes.common import safe_callable

from BTrees.IIBTree import IISet, multiunion, difference
from BTrees.IIBTree import intersection, union
from BTrees.IOBTree import IOBTree
from BTrees.OIBTree import OIBTree
from BTrees.Length import Length

_marker = []

manage_addIntegerRangesIndexForm = \
    PageTemplateFile('www/add_integer_ranges_index.zpt', globals())

def manage_addIntegerRangesIndex(self, id, extra=None, REQUEST=None,
        RESPONSE=None, URL3=None, **kw):
    """Add a proxy index"""
    return self.manage_addIndex(id,
                                'IntegerRangesIndex',
                                REQUEST=REQUEST,
                                RESPONSE=RESPONSE,
                                URL1=URL3)


class IntegerRangesIndex(SimpleItem):
    """ Index a set of integer ranges:
        [(1,2), (12,23), (12, 22)]
    """
    implements(IPluggableIndex)
    meta_type = 'IntegerRangesIndex'

    def __init__(self, id, caller=None, extra=None):
        self.id = id
        self.caller = caller
        self.clear()
        self.__genid = 0

    def __len__(self):
        return self._length()

    def getId(self):
        """Return Id of index."""
        return self.id

    def clear(self):
        """Empty the index"""
        self._index = IOBTree() # {rangeid: [document_id, ...]}
        self._unindex = IOBTree() # {document_id: [rangeid, ...]}
        self._range_mapping = IOBTree() # {rangeid: range}
        self._reverse_range_mapping = OIBTree() # {range: rangeid}
        self._since_index = IOBTree() # {since: [rangeid,...]}
        self._until_index = IOBTree() # {until: [rangeid,...]}
        self._length = Length()
        self._unique_values_length = Length()

    def __get_range_id(self, range_):
        return self._reverse_range_mapping.get(range_, None)

    def __get_range(self, range_id):
        return self._range_mapping.get(range_id, None)

    def __index_range(self, range_):
        """ index range if needed and return the rangeid
        """
        range_id = self.__get_range_id(range_)
        if range_id is None:
            range_id = self.genid()
            # index range
            self._unique_values_length.change(1)
            self._range_mapping[range_id] = range_
            self._reverse_range_mapping[range_] = range_id
            # index range boundaries
            since, until = range_
            self.__insert_in_index_set(self._since_index, since, range_id)
            self.__insert_in_index_set(self._until_index, until, range_id)
        return range_id

    def __unindex_range(self, range_id):
        range_ = self.__get_range(range_id)
        if range_ is None:
            return None
        since, until = range_
        self.__remove_in_index_set(self._since_index, since, range_id)
        self.__remove_in_index_set(self._until_index, until, range_id)
        self._unique_values_length.change(-1)
        del self._range_mapping[range_id]
        del self._reverse_range_mapping[range_]
        return range_

    def genid(self):
        self.__genid += 1
        return self.__genid

    def getEntryForObject(self, document_id, default=_marker):
        """Get all information contained for 'document_id'."""
        if default is _marker:
            return self._unindex.get(document_id)
        else:
            return self._index.get(document_id, default)

    def getIndexSourceNames(self):
        """Get a sequence of attribute names that are indexed by the index.
        """
        return [self.id]

    def index_object(self, document_id, obj, threshold=None):
        """Index an object.

        'document_id' is the integer ID of the document.
        'obj' is the object to be indexed.
        'threshold' is the number of words to process between committing
        subtransactions.  If None, subtransactions are disabled.
        """
        new_ranges = self._get_object_data(obj, self.id)
        if new_ranges:
            new_set = IISet(map(self.__index_range, new_ranges))
        else:
            new_set = IISet()

        old_set = self._unindex.get(document_id, IISet())

        new_entries = difference(new_set, old_set)
        expired_entries = difference(old_set, new_set)

        if not (new_entries or expired_entries):
            # nothing to do, bail out !
            return 0
        for expired_entry in expired_entries:
            self.__remove_in_index_set(self._unindex, document_id,
                expired_entry)
            if self.__remove_in_index_set(self._index, expired_entry, \
                    document_id):
                # range is not used anymore, retire it
                self.__unindex_range(expired_entry)

        for new_entry in new_entries:
            if self.__insert_in_index_set(self._unindex, document_id,
                    new_entry):
                self._length.change(1)
            self.__insert_in_index_set(self._index, new_entry, document_id)

        return 1

    def unindex_object(self, document_id):
        """Remove the document_id from the index."""
        entries = self._unindex.get(document_id, _marker)
        if entries is _marker:
            return
        if isinstance(entries, int):
            entries = [entries]
        for expired_entry in entries:
            if self.__remove_in_index_set(self._index, expired_entry, \
                    document_id):
                # range is not used anymore, retire it
                self.__unindex_range(expired_entry)
        self._length.change(-1)
        del self._unindex[document_id]

    def __insert_in_index_set(self, index, key, value, set_type=IISet):
        """ Insert value in the index. If the key was not present and
        the index row was created it returns True
        """
        index_row = index.get(key, _marker)
        if index_row is _marker:
            index[key] = value
            return True
        if isinstance(index_row, set_type):
            index_row.insert(value)
            return False
        # it was an int
        index[key] = set_type((index_row, value,))
        return False

    def __remove_in_index_set(self, index, key, value, set_type=IISet):
        """ remove the value in the index, index row is a Set
        It returns true if the index row as been removed (The set was empty)
        """
        index_row = index.get(key, _marker)
        if index_row is _marker:
            return True
        if isinstance(index_row, IISet):
            index_row.remove(value)
            if len(index_row) == 0:
                del index[key]
                return True
            if len(index_row) == 1:
                index[key] = index_row[0]
            return False
        del index[key]
        return True

    def _apply_index(self, request):
        record = parseIndexRequest(request, self.id)
        try:
            qstart, qend = record.keys
        except TypeError:
            return None
        # start in inside range
        start = multiunion(self._since_index.values(max=qstart))
        end = multiunion(self._until_index.values(min=qstart))
        start_into = intersection(start, end)

        # end inside range
        start = multiunion(self._since_index.values(max=qend))
        end = multiunion(self._until_index.values(min=qend))
        end_into = intersection(start, end)

        # start before range and end after range
        start = multiunion(self._since_index.values(min=qstart))
        end = multiunion(self._until_index.values(max=qend))
        start_before_end_after = intersection(start, end)

        result = union(start_into, end_into)
        result = union(result, start_before_end_after)

        return multiunion(map(self._index.__getitem__, result)), (self.id,)

    def numObjects(self):
        """Return the number of indexed objects"""
        return self._length()

    def indexSize(self):
        """Return the size of the index in terms of distinct values"""
        return self._unique_values_length()

    def _get_object_data(self, obj, attr):
        # self.id is the name of the index, which is also the name of the
        # attribute we're interested in.  If the attribute is callable,
        # we'll do so.
        try:
            datum = getattr(obj, attr)
            if safe_callable(datum):
                datum = datum()
        except AttributeError:
            datum = _marker
        return datum


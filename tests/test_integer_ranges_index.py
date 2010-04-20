from Products.SilvaNews.indexing import IntegerRangesIndex
from datetime import datetime
import unittest


class Doc(object):
    def __init__(self, ranges):
        self.ranges = ranges

    def ranges(self):
        return self.ranges


def datetime_to_unixtimestamp(dt):
    return int(dt.strftime("%s"))

class TestCollectionIndex(unittest.TestCase):

    def setUp(self):
        self.cindex = IntegerRangesIndex('ranges')

    def _get_range(self, range_id):
        return self.cindex._IntegerRangesIndex__get_range(range_id)

    def test_indexing_a_document(self):
        now = datetime_to_unixtimestamp(datetime.now())
        r1 = (now, now + 60,)
        r2 = (now + 120, now + 240,)
        ranges = [r1, r2,]
        doc = Doc(ranges)
        docid = 1

        self.cindex.index_object(docid, doc)

        self.assertEquals(set(ranges),
            set(map(self._get_range, self.cindex._unindex[docid])))

        self.assertEquals(r1,
            self._get_range(self.cindex._since_index[now]))
        self.assertEquals(r2,
            self._get_range(self.cindex._since_index[now + 120]))

        self.assertEquals(r1,
            self._get_range(self.cindex._until_index[now + 60]))
        self.assertEquals(r2,
            self._get_range(self.cindex._until_index[now + 240]))


    def test_reindexing_a_document_removing_an_item(self):
        now = datetime_to_unixtimestamp(datetime.now())
        r1 = (now, now + 60,)
        r2 = (now + 120, now + 240,)
        r3 = (now, now + 3600)
        ranges = [r1, r2, r3]
        ranges2 = [r2, r3]
        doc1 = Doc(ranges)
        doc2 = Doc(ranges2)
        docid = 1
        
        # index document with ranges
        self.cindex.index_object(docid, doc1)

        self.assertEquals(3, len(self.cindex._unindex.get(docid)))
        self.assertEquals(set(ranges),
            set(map(self._get_range, self.cindex._unindex[docid])))

        # reindex document with ranges2
        self.cindex.index_object(docid, doc2)

        self.assertEquals(2, len(self.cindex._unindex.get(docid)))
        self.assertEquals(set(ranges2),
            set(map(self._get_range, self.cindex._unindex[docid])))


    def test_length(self):
        now = datetime_to_unixtimestamp(datetime.now())
        r1 = (now, now + 60,)
        r2 = (now + 120, now + 240,)
        r3 = (now, now + 3600)
        ranges = [r1, r2, r3]
        ranges2 = [r2, r3]
        doc1 = Doc(ranges)
        doc2 = Doc(ranges2)
        # adding 2 documents
        self.cindex.index_object(1, doc1)
        self.assertEquals(1, len(self.cindex))
        self.cindex.index_object(2, doc2)
        self.assertEquals(2, len(self.cindex))

        # adding an already indexed documents
        # nothing should change
        self.cindex.index_object(1, doc1)
        self.assertEquals(2, len(self.cindex))
        self.cindex.index_object(2, doc2)
        self.assertEquals(2, len(self.cindex))

        # unindexing documents
        self.cindex.unindex_object(2)
        self.assertEquals(1, len(self.cindex))
        self.cindex.unindex_object(1)
        self.assertEquals(0, len(self.cindex))

    def test_unofficial_size(self):
        now = datetime_to_unixtimestamp(datetime.now())
        r1 = (now, now + 60,)
        r2 = (now + 120, now + 240,)
        r3 = (now, now + 3600)
        ranges = [r1, r2, r3]
        ranges2 = [r2, r3]
        doc1 = Doc(ranges)
        doc2 = Doc(ranges2)
        # adding 2 documents
        self.cindex.index_object(1, doc1)
        self.cindex.index_object(2, doc2)
        self.assertEquals(2, self.cindex.numObjects())
        self.assertEquals(3, self.cindex.indexSize())
        doc1.ranges = [r2]
        self.cindex.index_object(1, doc1)
        self.assertEquals(2, self.cindex.numObjects())
        self.assertEquals(2, self.cindex.indexSize())
        self.cindex.unindex_object(1)
        self.cindex.unindex_object(2)
        self.assertEquals(0, self.cindex.numObjects())
        self.assertEquals(0, self.cindex.indexSize())


    def test_unindex_object(self):
        now = datetime_to_unixtimestamp(datetime.now())
        r1 = (now, now + 60,)
        r2 = (now + 120, now + 240,)
        ranges = [r1, r2,]
        doc = Doc(ranges)
        docid = 1

        self.cindex.index_object(docid, doc)
        indexed_ranges_ids = self.cindex._unindex[docid]
        self.cindex.unindex_object(docid)

        for range_id in indexed_ranges_ids:
            range_ = self._get_range(range_id)
            self.assertEquals(None, range_)

    def test_apply_index(self):
        now = 0
        r1 = (now, 60,)
        r2 = (now + 120, now + 240,)
        r3 = (now, now + 3600)
        r4 = (now, now + 180)
        r5 = (now - 120, now)
        doc1 = Doc([r1])
        doc2 = Doc([r2])
        doc3 = Doc([r3])
        doc4 = Doc([r4])
        doc5 = Doc([r5])
        doc0 = Doc([r1,r2,r3,r4,r5])
        self.cindex.index_object(1, doc1)
        self.cindex.index_object(2, doc2)
        self.cindex.index_object(3, doc3)
        self.cindex.index_object(4, doc4)
        self.cindex.index_object(5, doc5)
        self.cindex.index_object(0, doc0)

        result = self.query(now, now + 10)
        self.assertEquals(set([0,1,3,4,5]), result)

        result = self.query(-10000, -1000)
        self.assertEquals(set(), result)

        result = self.query(-100, now - 1)
        self.assertEquals(set([0, 5]), result)

        result = self.query(now - 120, now + 3600)
        self.assertEquals(set([0,1,2,3,4,5]), result)

        result = self.query(now + 200, now + 210)
        self.assertEquals(set([0,2,3]), result)


    def query(self, start, end):
        test_range = (start, end)
        (results, used) = self.cindex._apply_index(
            {'ranges': {'start': test_range[0], 'end': test_range[1]}})
        return set(results)


def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TestCollectionIndex))
    return suite

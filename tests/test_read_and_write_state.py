'''
Created on Aug 30, 2018

@author: bhoff
'''
import unittest
import tempfile
import os
import SynapseBucketMover
from nose.tools import assert_raises, assert_equal, assert_is_none, assert_is_not_none, assert_in, assert_false, assert_true

class Test(unittest.TestCase):


    def setUp(self):
        self.dir = tempfile.TemporaryDirectory()


    def tearDown(self):
        if self.dir is not None:
            os.remove(os.path.join(self.dir.name, "state.txt"))


    def testPersistence(self):
        state=SynapseBucketMover.readState(self.dir)
        assert_equal(0, state['filesProcessedCount'])
        assert_equal([], state['treePageMarker'])
        
        state['filesProcessedCount']=100
        state['treePageMarker']=[{'parentId':'syn123','nextPageToken':'abc'},{'parentId':'syn456','nextPageToken':'def'}]
        SynapseBucketMover.writeState(self.dir, state)
        readState = SynapseBucketMover.readState(self.dir)
        assert_equal(state, readState)

if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testPersistence']
    unittest.main()
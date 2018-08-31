'''
Created on Aug 30, 2018

@author: bhoff
'''
import unittest
import tempfile
import os
import SynapseBucketMover
from nose.tools import assert_raises, assert_equal, assert_is_none, assert_is_not_none, assert_in, assert_false, assert_true

def node(id):
    return (id, 'org.sagebionetworks.repo.model.FolderEntity')

def leaf(id):
    return (id, 'org.sagebionetworks.repo.model.FileEntity')

PAGE_SIZE=2

class Test(unittest.TestCase):    
        
    def setUp(self):
        self.tree = {node("n1"):
                      [{node("n2"):
                        [{leaf("f1"):None},
                         {leaf("f2"):None},
                         {node("n3"):
                            [{leaf("f3"):None},
                             {node("n4"):[{leaf("f4"):None},{leaf("f5"):None}]},
                             {leaf("f6"):None}]},
                         {leaf("f7"):None}
                         ]}
                      ]
                    }
                    
                    

    # This is an implementation of 'getChildren' for unit testing
    def getChildren(self, id, nextPageToken):
        return self.getChildrenInner(self.tree, id, nextPageToken)
     
    def getChildrenInner(self, tree, id, nextPageToken):
        for node in tree:
            if node[1]=='org.sagebionetworks.repo.model.FolderEntity':
                if node[0]==id:
                    childList = tree[node]
                    i=0
                    while nextPageToken is not None and i<len(childList) and childList[i].keys().__iter__().__next__()[0]!=nextPageToken:
                        i=i+1
                    page = []
                    while i<len(childList) and len(page)<PAGE_SIZE:
                        childNode=childList[i].keys().__iter__().__next__()
                        page.append({'id':childNode[0], 'type':childNode[1]})
                        i=i+1
                    if i<len(childList):
                        childNode=childList[i].keys().__iter__().__next__()
                        nextPageToken=childNode[0]
                    else:
                        nextPageToken = None
                    return {'page':page, 'nextPageToken':nextPageToken}
                else:
                    for child in tree[node]:
                        result = self.getChildrenInner(child, id, nextPageToken)
                        if len(result['page'])>0:
                            return result
            return {'page':[], 'nextPageToken':None}


    def tearDown(self):
        pass
    

    def testTraversal(self):
        result=SynapseBucketMover.nextLeaf([{'parentId':'n1'}], self.getChildren)
        assert_equal(result.get('id'), 'f1')
        result=SynapseBucketMover.nextLeaf(result['treePageMarker'], self.getChildren)
        assert_equal(result.get('id'), 'f2')
        result=SynapseBucketMover.nextLeaf(result['treePageMarker'], self.getChildren)
        assert_equal(result.get('id'), 'f3')
        result=SynapseBucketMover.nextLeaf(result['treePageMarker'], self.getChildren)
        assert_equal(result.get('id'), 'f4')
        result=SynapseBucketMover.nextLeaf(result['treePageMarker'], self.getChildren)
        assert_equal(result.get('id'), 'f5')
        result=SynapseBucketMover.nextLeaf(result['treePageMarker'], self.getChildren)
        assert_equal(result.get('id'), 'f6')
        result=SynapseBucketMover.nextLeaf(result['treePageMarker'], self.getChildren)
        assert_equal(result.get('id'), 'f7')
        result=SynapseBucketMover.nextLeaf(result['treePageMarker'], self.getChildren)
        assert_equal(result.get('id'), None)
       

if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testPersistence']
    unittest.main()
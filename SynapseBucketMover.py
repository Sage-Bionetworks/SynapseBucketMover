'''
Moves Synapse files from one bucket to another

This code processes a large tree of Synapse files.  As such it needs to show progress and gracefully
handle stopping unexpectedly and being restarted.  It is idempotent and it records its location in the
file hierarchy ('tree') in order to be able to be restarted.

Created on Aug 30, 2017

@author: bhoff
'''
import synapseclient
import argparse
import json
import os

# state is a dict
# key:  filesProcessedCount, value:  integer
# key:  treePageMarker, value:  list of dict's, for each dict:
#    key:  page, value: a page of children, as returned by the /entity/children API
#    key:  currentNode, value:  the integer index, >=0 within the aforementioned page
#    key:  parentId, value:  id of container containing the current page
#    key:  nextPageToken, value:  token for getting the subsequent page
def readState(persistenceFolder):
    try:
        with open(os.path.join(persistenceFolder.name, 'state.txt'), 'r') as myfile:
            data=myfile.read().replace('\n', '')
        return json.loads(data)
    except:
        return {'filesProcessedCount':0, 'treePageMarker':[]}

def writeState(persistenceFolder, state):
        with open(os.path.join(persistenceFolder.name, 'state.txt'), 'w') as myfile:
            myfile.write(json.dumps(state))


def processOneFile(synId):
    print('Processing '+synId)
    # TODO add code for processing the file
    
def getChildren(parentId, nextPageToken=None):
    global synapse
    entityChildrenRequest = {'parentId':parentId, 'includeTypes':['folder', 'file'], 'nextPageToken': nextPageToken}
    response = synapse.restPOST('/entity/children',body =json.dumps(entityChildrenRequest))
    return response
    
# Given the treePageMarker (the state of traversing the tree),
# return the next node and the updated treePageMarker
# Note:  getChildren is passed in to allow unit testing
def nextLeaf(treePageMarker, getChildren):
    if (not type(treePageMarker) is list):
        raise Exception('treePageMarker must be a list')
    if len(treePageMarker)<1:
        return {'id':None,'treePageMarker':treePageMarker}
    updatedTreePageMarker = treePageMarker[:]
     
    lastTreePageMarkerEntry = updatedTreePageMarker[-1]
    page = lastTreePageMarkerEntry.get('page')
    if page is None:
        page = []
    atLastPageElement = ('currentNode' in lastTreePageMarkerEntry and lastTreePageMarkerEntry['currentNode']+1>=len(page))
    if len(page)==0 or atLastPageElement:
        if len(page)>0 and atLastPageElement and lastTreePageMarkerEntry.get('nextPageToken') is None:
            page=[]
        else:
            entityChildrenResponse=getChildren(lastTreePageMarkerEntry['parentId'], lastTreePageMarkerEntry.get('nextPageToken'))
            page = entityChildrenResponse.get('page')
            if (page is None or len(page)==0) and entityChildrenResponse.get('nextPageToken')!=None:
                raise Exception("Empty page with next page token")
        if page is None or len(page)==0:
            # go up one level in the tree and navigate from there to the next leaf
            return nextLeaf(treePageMarker[0:len(treePageMarker)-1], getChildren)
        lastTreePageMarkerEntry['page']=page
        lastTreePageMarkerEntry['nextPageToken']=entityChildrenResponse.get('nextPageToken')
        lastTreePageMarkerEntry['currentNode'] = None
        
    if lastTreePageMarkerEntry['currentNode'] is None:
        nextIndex=0
    else:
        nextIndex=lastTreePageMarkerEntry['currentNode']+1
    lastTreePageMarkerEntry['currentNode']=nextIndex
        
    # at this point we have a page and a pointer in it
    # pointer can't be beyond because either (1) it's 0 and the page is non-empty or (2) it's less than the page length
    if nextIndex>=len(page):
        raise Exception('Index should not be beyond the end of the page.')
    child = page[nextIndex]
    
    # if the node is not a leaf then recurse down the tree
    if child['type'] != 'org.sagebionetworks.repo.model.FileEntity':
        updatedTreePageMarker.append({'parentId':child['id']})
        return nextLeaf(updatedTreePageMarker, getChildren)

    # OK, it's a leaf, return its id, along with the updated state
    return {'id':child['id'],'treePageMarker':updatedTreePageMarker}

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("-u","--synapseUser", required=True,
                        help="Synapse user name")
    parser.add_argument("-p","--synapsePassword", required=True,
                        help="Synapse password")
    parser.add_argument("-r", "--rootId", required=True, help="ID of root container (project or folder")
    parser.add_argument("-f", "--persistenceFolder", required=True, help="Folder on system in which to persist state")
    args = parser.parse_args()

    global synapse
    synapse = synapseclient.Synapse()
    synapse = synapseclient.login(args.synapseUser, args.synapsePassword,rememberMe=False)
    
    
    treePageMarker = [{'parentId':args.rootId, 'nextPageToken':None, 'page':[]}]
    
    while True:
        result=nextLeaf(treePageMarker, getChildren)
        node=result.get('id')
        if node is None:
            break
        print(node)
        treePageMarker=result['treePageMarker']



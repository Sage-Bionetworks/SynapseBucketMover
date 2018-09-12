'''
Moves Synapse files from one bucket to another

This code processes a large tree of Synapse files.  As such it needs to show progress and gracefully
handle stopping unexpectedly and being restarted.  It is idempotent and it records its location in the
file hierarchy ('tree') in order to be able to be restarted.

Created on Aug 30, 2018

@author: bhoff
'''
import json
import os
import argparse
import synapseclient
import boto3

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

def s3move(srcBucketName, srcKey, dstBucketName, dstKey):
    # use boto to move (NOT COPY) the file to the new bucket. Use sse=AES256
    # Turns out that to move you must copy, then delete the original
    s3Client.copy_object(CopySource={'Bucket': srcBucketName, 'Key': srcKey}, Bucket=dstBucketName, Key=dstKey, ServerSideEncryption='AES256')
    s3Delete(srcBucketName, srcKey)
    
def s3Delete(srcBucketName, srcKey):
    s3Client.delete_object(Bucket=srcBucketName, Key=srcKey)

def processOneFile(synId, destinationS3Bucket, newStorageLocationId):
    print('Processing '+synId)

    entityMeta=None
    newfh=None
    handles=syn.restGET("/entity/"+synId+"/filehandles")
    for i in range(len(handles['list'])):
        fh=handles['list'][i]
        if fh['storageLocationId']==newStorageLocationId:
            print("\tAlready processed "+synId+".  Skipping.")
            continue
        if entityMeta is None:
            entityMeta=syn.restGET("/entity/"+synId)
            fhid=entityMeta['dataFileHandleId']
        if fh['id'] == fhid:
            fhkey = fh[key]
            slash = fhkey.rfind("/")
            if slash < 0:
                raise Exception("Expected a '/' separator in "+fhkey)
            keyPrefixWithSlash=fhkey[:slash+1]
            keySuffixNoSlash=fhkey[slash+1:]
            if keySuffixNoSlash != fh['fileName']:
                raise Exception("Expected key suffix, "+keySuffixNoSlash+" to match fileName in file handle, "+fh['fileName'])
            # TODO Use mapping provided by Kenny to define a new file name, which is the suffix of the key
            newFileName=fh['fileName']
            newKey = keyPrefixWithSlash+newFileName
            # move the S3 file to the new bucket, using newKey as the destination
            s3move(fh['bucket'], fh['key'], destinationS3Bucket, newKey)
            newfhMeta={}
            for key in ['contentMd5','contentSize','contentType']:
                newfhMeta[key]=fh[key]
            newfhMeta['fileName']=newFileName
            newfhMeta['key']=newKey
            newfhMeta['bucketName']=destinationS3Bucket
            newfhMeta['storageLocationId']=newStorageLocationId
            # this will trigger the creation of a preview in the new bucket
            newfh=syn.restPOST('/externalFileHandle/s3',body =json.dumps(newfhMeta), endpoint='https://repo-prod.prod.sagebase.org/file/v1')
        else:
            s3Delete(fh['bucket'], fh['key'])
    
    if newfh is None:
        # nothing to do
        return
    
    # Annotate the current file version with 'unavailable'
    entityMeta['versionLabel']='Unavailable for Download'
    entityMeta = syn.restPUT("/entity/"+synId, body =json.dumps(entityMeta))
    # update the file with the new file handle, also changing the entity name to the new file name
    entityMeta['name']=newfh['fileName']
    entityMeta['dataFileHandleId']=newfh['id']
    entityMeta = syn.restPUT("/entity/"+synId, body =json.dumps(entityMeta))
    
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
    parser.add_argument("-s", "--storageLocationId", required=True, type=int, help="Target storage location id")
    parser.add_argument("-kid", "--awsKeyId", required=True, help="AWS Key ID")
    parser.add_argument("-ksec", "--awsKeySecret", required=True, help="AWS Key Secret")
    parser.add_argument("-m", "--maxNumberToProcess", type=int, help="Maximum number of files to process")
    args = parser.parse_args()

    global synapse
    synapse = synapseclient.Synapse()
    synapse = synapseclient.login(args.synapseUser, args.synapsePassword,rememberMe=False)
    global s3Client
    s3Client= boto3.client('s3', aws_access_key_id=args.awsKeyId, aws_secret_access_key=args.awsKeySecret)
    
    dstStorageLocation=syn.restGET("/storageLocation/"+str(args.storageLocationId))
    if dstStorageLocation['concreteType']!='org.sagebionetworks.repo.model.project.ExternalS3StorageLocationSetting':
        raise Exception('Expected org.sagebionetworks.repo.model.project.ExternalS3StorageLocationSetting but found '+dstStorageLocation['concreteType'])
    destinationS3Bucket=dstStorageLocation['bucket'] # TODO do we need to account for dstStorageLocation['baseKey']?
    
    state=readState(args.persistenceFolder)
    if (len(state['treePageMarker'])==0):
        state['treePageMarker']=[{'parentId':args.rootId, 'nextPageToken':None, 'page':[]}]
    initialCount=state['filesProcessedCount']
    
    treePageMarker = [{'parentId':args.rootId, 'nextPageToken':None, 'page':[]}]
    
    counter=0
    while args.maxNumberToProcess is None or counter<args.maxNumberToProcess:
        result=nextLeaf(treePageMarker, getChildren)
        node=result.get('id')
        if node is None:
            break
        processOneFile(node, destinationS3Bucket, args.storageLocationId)
        counter=counter+1
        treePageMarker=result['treePageMarker']
        state['filesProcessedCount']=initialCount+counter
        state['treePageMarker']=treePageMarker
        writeState(args.persistenceFolder, state)

    print("Processed "+str(counter)+" files.")


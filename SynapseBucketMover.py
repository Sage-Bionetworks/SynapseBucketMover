'''
Moves Synapse files from one bucket to another

Created on Aug 30, 2017

@author: bhoff
'''
import synapseclient
import argparse
import json
import os


# state is a dict
# key:  filesProcessedCount, value:  integer
# key:  treeMarker, value:  list of dict's, for each dict:
#    key:  parentId, value:  id of container
#    key:  nextPageToken, value:  token for page being processed
def readState(persistenceFolder):
    try:
        with open(os.path.join(persistenceFolder.name, 'state.txt'), 'r') as myfile:
            data=myfile.read().replace('\n', '')
        return json.loads(data)
    except:
        return {'filesProcessedCount':0, 'treeMarker':[{}]}

def writeState(persistenceFolder, state):
        with open(os.path.join(persistenceFolder.name, 'state.txt'), 'w') as myfile:
            myfile.write(json.dumps(state))

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("-u","--synapseUser", required=True,
                        help="Synapse user name")
    parser.add_argument("-p","--synapsePassword", required=True,
                        help="Synapse password")
    parser.add_argument("-r", "--rootId", required=True, help="ID of root container (project or folder")
    parser.add_argument("-f", "--persistenceFolder", required=True, help="Folder on system in which to persist state")
    args = parser.parse_args()

    syn = synapseclient.Synapse()
    syn = synapseclient.login(args.synapseUser, args.synapsePassword,rememberMe=False)



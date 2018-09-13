'''

Create sample files to move

Created on Aug 30, 2018

@author: bhoff
'''
import synapseclient
import argparse
import json
import os
import tempfile


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("-u","--synapseUser", required=True,
                        help="Synapse user name")
    parser.add_argument("-p","--synapsePassword", required=True,
                        help="Synapse password")
    parser.add_argument("-r", "--sourceProject", required=True, help="Project using 'original' bucket")
    parser.add_argument("-n", "--numberOfFiles", required=True, type=int, help="Number of files to create")
    args = parser.parse_args()

    global synapse
    synapse = synapseclient.Synapse()
    synapse = synapseclient.login(args.synapseUser, args.synapsePassword,rememberMe=False)
    
    MAX_FILES_PER_FOLDER=10
    # create 'n' files in sourceProject (say, 10 to a folder)
    folder=None
    folderCount=0
    filesInFolder=0
    for i in range(args.numberOfFiles):
        if folder is None or filesInFolder>=MAX_FILES_PER_FOLDER:
            # create folder
            folder = synapseclient.Folder(str(folderCount), parent=args.sourceProject)
            folder = synapse.store(folder)
            filesInFolder=0
            folderCount=folderCount+1
        # create file, upload to folder
        # just make an arbitrary string
        s=''
        for j in range(100):
            s=s+str(i)+' '
        filePath=os.path.join(tempfile.gettempdir(), str(i)+'.txt')
        with open(filePath, 'w') as myfile:
            myfile.write(s)
        file=synapseclient.File(filePath, parent=folder, annotations={'someAnnotName':'someAnnotValue'})
        file=synapse.store(file)
        filesInFolder=filesInFolder+1


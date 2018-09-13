'''

Delete all files, from Synapse and from S3

Created on Aug 30, 2018

@author: bhoff
'''
import synapseclient
import argparse
import json
import os
import tempfile
import boto3
from boto3 import client

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("-u","--synapseUser", required=True,
                        help="Synapse user name")
    parser.add_argument("-p","--synapsePassword", required=True,
                        help="Synapse password")
    parser.add_argument("-r", "--rootId", required=True, help="ID of root container (project or folder")
    parser.add_argument("-kid", "--awsKeyId", required=True, help="AWS Key ID")
    parser.add_argument("-ksec", "--awsKeySecret", required=True, help="AWS Key Secret")
    parser.add_argument("-awstoken", "--awsSessionToken", required=True, help="AWS MFA Session Token")
    parser.add_argument("-b1", "--bucket1", required=True, help="First bucket name")
    parser.add_argument("-b2", "--bucket2", required=True, help="Second bucket name")
    parser.add_argument("-d", "--dryrun", action='store_true', help="dry run")
    args = parser.parse_args()

    global synapse
    synapse = synapseclient.Synapse()
    synapse = synapseclient.login(args.synapseUser, args.synapsePassword,rememberMe=False)
    
    dryrun = args.dryrun

    for child in synapse.getChildren(args.rootId):
        if dryrun:
            print("Delete "+child['id']+" and all its descendents.")
        else:
            synapse.restDELETE("/entity/"+child['id']+"?skipTrashCan=true")
    print("Deleted all children of "+args.rootId+".")
    
    # TODO take baseKey into account
    client = boto3.client('s3', aws_access_key_id=args.awsKeyId, aws_secret_access_key=args.awsKeySecret, aws_session_token=args.awsSessionToken)
    for bucketName in [args.bucket1, args.bucket2]:
        print("\nDeleting from bucket "+bucketName)
        for key in client.list_objects(Bucket=bucketName)['Contents']:
            if not key['Key'].endswith("owner.txt"):
                print(key['Key'])
                if not dryrun:
                    client.delete_object(Bucket=bucketName, Key=key['Key'])
        
    
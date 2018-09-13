# SynapseBucketMover
Moves Synapse files from one bucket to another

##Upload some sample files for testing
First create a project with a private bucket, as described here https://docs.synapse.org/articles/custom_storage_location.html.  Now to generate, say, 25 test files:
```
docker run --rm -it  sagebionetworks/synapsebucketmover \
python UploadFiles.py -u <synapse-username> -p <synapse-password> -r <projectId> -n 25
```
Now create a second private bucket and create a storage location for the bucket.  Note the ID of the storage location object. If you created the private bucket through the Synapse web portal and do not know the storage location ID, then you can retrieve it programmatically using the Python client as follows:
```
>>> projectId='syn123456'
>>> syn.restGET("/projectSettings/"+projectId+"/type/upload")['locations']
```
where `projectId` is the Synapse ID of the project whose storage location ID is to be retrieved.

##Migrate the files
If not using MFA, enter your aws-key-id and aws-key-secret below, omitting -awstoken.  If you are using MFA, the credentials below include three strings you can get using the AWS CLI as follows:
```
aws sts get-session-token --serial-number arn:aws:iam::xxxxxxx --token-code xxxxx
```
Where the serial number is that of the MFA device and the token code is the 6 digit number it provides.  This will return three strings to use in -kid, -ksec and -awstoken, below.

```
docker run --rm -it -v /path/to/scratch/dir:/tempdir sagebionetworks/synapsebucketmover \
python SynapseBucketMover.py -u <synapse-username> -p <synapse-password> \
-r syn123456 -f /tempdir -s 1234 -kid <aws-key-id> -ksec <aws-key-secret>  -awstoken <session-token>
```
The `-r` parameter is the root (e.g. project) ID of the files to be updated.
The `-s` parameter is the ID of the storage location ID referencing the target S3 bucket. 

##Clean up
ONLY USE THIS ON TEST PROJECTS.  All files will be deleted from Synapse, the original S3 bucket and the target S3 bucket.
```
docker run --rm -it sagebionetworks/synapsebucketmover \
python DeleteAll.py -u <synapse-username> -p <synapse-password> \
-r syn123456 -kid <aws-key-id> -ksec <aws-key-secret> -awstoken <session-token>
```

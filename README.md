# SynapseBucketMover
Moves Synapse files from one bucket to another

##Upload some sample files for testing
First create a project with a private bucket.  Now to generate, say, 25 test files:
```
docker run --rm -it  sagebionetworks/synapsebucketmover \
python UploadFiles.py -u <synapse-username> -p <synapse-password> -r <projectId> -n 25
```
Now create a second private bucket and create a storage location for the bucket.  Note the ID of the storage location object.

##Migrate the files
If using MFA the credentials include 3 strings you can get using the AWS CLI:
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
The `-s` parameter is the ID of the storage location ID referencing the target S3 bucket.  If you created the private bucket through the Synapse web portal and do not know the storage location ID, then you can retrieve it programmatically using the Python client as follows:
```
>>> pid='syn123456'
>>> syn.restGET("/projectSettings/"+pid+"/type/upload")['locations']
```
where `pid` is the Synapse ID of the project whose upload location is to be retrieved.

##Clean up
ONLY USE THIS ON TEST PROJECTS.  All files will be deleted.
```
docker run --rm -it sagebionetworks/synapsebucketmover \
python DeleteAll.py -u <synapse-username> -p <synapse-password> \
-r syn123456 -kid <aws-key-id> -ksec <aws-key-secret> -awstoken <session-token>
```

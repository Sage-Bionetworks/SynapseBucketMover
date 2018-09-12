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
```
docker run --rm -it -v /path/to/scratch/dir:/tempdir sagebionetworks/synapsebucketmover \
python SynapseBucketMover.py -u <synapse-username> -p <synapse-password> \
-r syn123456 -f /tempdir -s 1234 -kid <aws-key-id> -ksec <aws-key-secret>
```
The `-r` parameter is the root (e.g. project) ID of the files to be updated.
the `-s` parameter is the ID of the storage location ID referencing the target S3 bucket

##Clean up
ONLY USE THIS ON TEST PROJECTS.  All files will be deleted.
```
docker run --rm -it sagebionetworks/synapsebucketmover \
python DeleteAll.py -u <synapse-username> -p <synapse-password> \
-r syn123456 -kid <aws-key-id> -ksec <aws-key-secret>
```

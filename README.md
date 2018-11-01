# SynapseBucketMover

Moves Synapse files from one AWS S3 bucket to another.

### What the Bucket Mover does

* The S3 file underlying each Synapse file under the given root container is moved into the bucket indicated by the given storage location.  (Note:  It is assumed that there is just one version of each Synapse file.  The process will stop if an unprocessed Synapse file with multiple versions is found.)
* The Synapse ID and 'created by' name of each file are unchanged.  The 'modified by' name of each file is that of the account used to run this program.
* The Synapse organization will not be changed.  All files will remain in their current project/folder hierarchy.
* On the page for each file you will see that its storage location has been updated.
* Each file will have a new version.  The previous version is updated with a comment, 'Unavailable for Download'.
* File annotations are preserved.
* Each new file is encrypted in the target bucket using AES256 server-side encryption.
* The file, and its preview, if any, are erased from the original bucket.
* Synapse creates a new file preview in the new bucket.

### Progress and restart

A file is written to `/path/to/scratch/dir/state.txt` (where `/path/to/scratch/dir` is a folder of your choice).  If the program is interrupted it can be restarted from where it left off, using the contents of this file to keep track of its location.  The file is a Python 'dict' and has a field 'filesProcessedCount' showing the total number of files processed, across all restarts of the program.

### TO DO
This program currently does not support storage locations which are sub-folders of their bucket.  This can be added if needed.

To test drive:

## Upload some sample files for testing
First create a project with a private bucket, [as described here](https://docs.synapse.org/articles/custom_storage_location.html).  Now to generate, say, 25 test files:

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

## Migrate the files
If not using MFA, enter your aws-key-id and aws-key-secret below, omitting -awstoken.  If you are using MFA, the credentials below include three strings you can get using the AWS CLI as follows:

```
aws sts get-session-token --serial-number arn:aws:iam::xxxxxxx --token-code xxxxx
```

Where the serial number is that of the MFA device and the token code is the 6 digit number it provides.  This will return three strings to use in -kid, -ksec and -awstoken, below.

Note:  Before running the following, make sure that no other person or system is modifying the files being processed.  A good practice is to remove any collaborators from the sharing settings for the project.

```
docker run --rm -it -v /path/to/scratch/dir:/tempdir sagebionetworks/synapsebucketmover \
python SynapseBucketMover.py -u <synapse-username> -p <synapse-password> \
-r syn123456 -f /tempdir -s 1234 -kid <aws-key-id> -ksec <aws-key-secret>  -awstoken <session-token>
```

The `-r` parameter is the root (e.g. project) ID of the files to be updated.
The `-s` parameter is the ID of the storage location ID referencing the target S3 bucket. 

## Clean up
ONLY USE THIS ON TEST PROJECTS.  All files will be deleted from Synapse, the original S3 bucket and the target S3 bucket.

```
docker run --rm -it sagebionetworks/synapsebucketmover \
python DeleteAll.py -u <synapse-username> -p <synapse-password> \
-r syn123456 -kid <aws-key-id> -ksec <aws-key-secret> -awstoken <session-token>
```

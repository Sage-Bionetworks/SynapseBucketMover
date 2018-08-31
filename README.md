# SynapseBucketMover
Moves Synapse files from one bucket to another

##To run
```
docker build -t synapse-bucket-mover .
docker run --rm -it -v /Users/bhoff/SynapseBucketMover:/tempdir synapse-bucket-mover \
python SynapseBucketMover.py -u synapse-username -p synapse-password -r synXXX -f /tempdir
```

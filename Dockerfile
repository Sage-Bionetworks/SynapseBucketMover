FROM python:3.6

RUN pip install nose
RUN pip install synapseclient

COPY . /SynapseBucketMover

WORKDIR /SynapseBucketMover

RUN nosetests tests

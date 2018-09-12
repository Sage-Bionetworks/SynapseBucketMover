FROM python:3.6

RUN pip install nose
RUN pip install synapseclient
RUN pip install boto3

COPY . /SynapseBucketMover

WORKDIR /SynapseBucketMover

RUN nosetests --nocapture tests

#!/usr/bin/env bash

BUILDS_DIR=/tmp/pinochle
ACCESS_KEY=$(grep aws_access_key_id ~/.aws/credentials | awk '{print $3}')
ACCESS_SECRET=$(grep aws_secret_access_key ~/.aws/credentials | awk '{print $3}')

if [ ! -z "$ACCESS_KEY" ]; then
  S3_ACCESS="--cache-type s3 --cache-s3-server-address phenom.n2kiq.dyndns.org:9876
  --cache-s3-access-key=$ACCESS_KEY --cache-s3-secret-key=$ACCESS_SECRET
  --cache-s3-bucket-name=gitlab-pinochle --cache-s3-insecure"
fi

#mkdir $BUILDS_DIR
#./gitlab-runner-linux-amd64 exec shell test --builds-dir=$BUILDS_DIR
#rm -rf $BUILDS_DIR

./gitlab-runner-linux-amd64 exec docker --docker-privileged $S3_ACCESS test

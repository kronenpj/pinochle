#!/usr/bin/env bash

BUILDS_DIR=/tmp/pinochle

#mkdir $BUILDS_DIR
#./gitlab-runner-linux-amd64 exec shell test --builds-dir=$BUILDS_DIR
#rm -rf $BUILDS_DIR

./gitlab-runner-linux-amd64 exec docker --docker-privileged test

#!/usr/bin/env bash

if [ -z "$VIRTUAL_ENV" ]; then
  . venv/bin/activate
fi

if [ "$1" == "" ]; then
  tox -p -- -m 'not hypothesis'
else
  tox -p "$@"
fi

# Exit if the test failed.
if [ $? == 1 ]; then
    exit $?
fi

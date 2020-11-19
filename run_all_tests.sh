#!/usr/bin/env bash

if [ -z "$VIRTUAL_ENV" ]; then
  . venv/bin/activate
fi

tox -p --notest -c tox.ini "$@"

if [ "$1" == "" ]; then
  tox -p -c tox.ini -- -m 'not hypothesis'
else
  tox -p -c tox.ini "$@"
fi

# Exit if the test failed.
if [ $? == 1 ]; then
    exit $?
fi

#!/usr/bin/env bash

PYVER=${PYVER:-py38}

#if [ -z "$VIRTUAL_ENV" ]; then
#  . venv/bin/activate
#fi

if [ "$1" == "" ]; then
  tox -e ${PYVER} -- -m 'not hypothesis'
else
  tox -e ${PYVER} "$@"
fi

exit $?

#!/usr/bin/env bash

PYVER=${PYVER:-py38}

if [ -z "$VIRTUAL_ENV" ]; then
  . venv/bin/activate
fi

tox -c tox.ini -e ${PYVER} --notest "$@"

if [ "$1" == "" ]; then
  tox -c tox.ini -e ${PYVER} -- -m 'not hypothesis'
else
  tox -c tox.ini -e ${PYVER} "$@"
fi

exit $?

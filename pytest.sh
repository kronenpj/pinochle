#!/usr/bin/env bash

if [ -z "$VIRTUAL_ENV" ]; then
  . .venv/bin/activate
fi

OPTIONS="$@"
if [ -z "$OPTIONS" ]; then
  AFTER="tests/"
else
  AFTER=""
fi

python -m pytest "$@" $AFTER

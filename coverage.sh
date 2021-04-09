#!/usr/bin/env bash

if [ -z "$VIRTUAL_ENV" ]; then
  . venv/bin/activate
fi

if [ -d src/pinochle/instance ]; then
  MOVED=1
  mv src/pinochle/instance src
fi

coverage run -m pytest -m 'not hypothesis' "$@"

coverage xml

if [ ! -z "$MOVED" ]; then
  mv src/instance src/pinochle
fi

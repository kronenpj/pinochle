#!/usr/bin/env bash

if [ -z "$VIRTUAL_ENV" ]; then
  . venv/bin/activate
fi

coverage run -m pytest -m 'not hypothesis' "$@"

#!/usr/bin/env bash

if [ -z "$VIRTUAL_ENV" ]; then
  . venv/bin/activate
fi

coverage report "$@"

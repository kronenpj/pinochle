#!/usr/bin/env bash

if [ -z "$VIRTUAL_ENV" ]; then
  . venv/bin/activate
fi

OPTIONS="$@"
if [ -z "$OPTIONS" ]; then
  AFTER="tests/"
else
  AFTER=""
fi

export COLLECT_VIDEO=${COLLECT_VIDEO-False}
export COLLECT_BROWSER_LOGS=${COLLECT_BROWSER_LOGS-False}
python -m pytest --runslow --runwip -m slow "$@" $AFTER

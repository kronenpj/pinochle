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

export COLLECT_VIDEO=${COLLECT_VIDEO-False}
export COLLECT_BROWSER_LOGS=${COLLECT_BROWSER_LOGS-False}
if [ -z "$SERVER_IP" ]; then
  _SUBNET=$(ip r | grep default | awk '{print $3}' | sed -E -e 's/\.[0-9]+?$//')
  export SERVER_IP=$(ip -4 a | grep $_SUBNET | awk '{print $2}' | sed -e 's%/24%%')
else
  export SERVER_IP=$SERVER_IP
fi
python -m pytest -x --runslow --runwip -m slow "$@" $AFTER

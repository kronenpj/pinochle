#!/usr/bin/env bash

PY_BIN=${1:-python3.9}

if [ -x /usr/bin/${PY_BIN} ];then
  PY=${PY_BIN}
else
  PY=/usr/bin/python3
fi

echo "Clearing and rebuilding .venv"
/usr/bin/${PY} -m venv .venv --clear --prompt pinochle

echo "Activating .venv"
source .venv/bin/activate

echo "Installing poetry"
pip3 install poetry

echo "Installing (development) requirements"
poetry install --no-root

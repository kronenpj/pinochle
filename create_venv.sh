#!/usr/bin/env bash

if [ -x /usr/bin/python3.9 ];then
  PY=python3.9
else
  PY=python3
fi

echo "Clearing and rebuilding .venv"
/usr/bin/${PY} -m venv .venv --clear --prompt pinochle
echo "Activating .venv"
source .venv/bin/activate
echo "Installing poetry"
pip3 install poetry
#pip install --use-feature=2020-resolver -r requirements.txt -r requirements-test.txt
echo "Installing (development) requirements"
poetry install --no-root

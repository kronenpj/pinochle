#!/usr/bin/env bash

if [ -x /usr/bin/python3.8 ];then
  PY=python3.8
else
  PY=python3
fi

/usr/bin/${PY} -m venv .venv --clear --prompt pinochle
#source venv/bin/activate
#pip install --use-feature=2020-resolver -r requirements.txt -r requirements-test.txt
/usr/bin/poetry install --no-root

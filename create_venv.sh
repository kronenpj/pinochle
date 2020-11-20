#!/usr/bin/env bash

/usr/bin/python3 -m venv venv --clear --prompt pinochle
source venv/bin/activate
pip install -r requirements.txt -r requirements-test.txt

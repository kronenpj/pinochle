@echo off

python3 -m venv .venv --clear --prompt pinochle
.venv\scripts\activate.bat
pip3 install poetry

poetry install --no-root

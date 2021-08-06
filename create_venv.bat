@echo off

echo "Clearing and rebuilding .venv"
python3 -m venv .venv --clear --prompt pinochle
echo "Activating .venv"
.venv\scripts\activate.bat
echo "Installing poetry."
pip3 install poetry

echo Installing development dependencies.
poetry install --no-root

@echo off

REM Create a virtual environment in the 'connexset' directory
python -m venv connexset

REM Activate the virtual environment
CALL connexset\Scripts\activate.bat

REM Install dependencies from requirements.txt
pip install -r requirements.txt

echo Virtual environment created and activated, dependencies installed.

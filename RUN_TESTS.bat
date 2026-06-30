@echo off
cd /d %~dp0
python -m pip install -r requirements.txt
python -m pip install -r requirements_dev.txt
python -m pytest tests
pause

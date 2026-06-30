@echo off
cd /d %~dp0
echo Installing optional AI model packages...
python -m pip install -r requirements_ai_install.txt
echo Done.
pause

@echo off
chcp 65001 >nul
cd /d %~dp0
python -m pip install --upgrade pip
python -m pip install playwright
python -m playwright install chromium
pause

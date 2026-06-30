@echo off
chcp 65001 >nul
cd /d %~dp0
set AUTO_SOURCE_LIVE=1
python -m streamlit run main.py
pause

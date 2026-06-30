@echo off
chcp 65001 >nul
cd /d "%~dp0"
set AUTO_SOURCE_LIVE=1
echo [AutoCommerceAI] 실제 웹 수집 모드로 실행합니다.
python -m streamlit run main.py
pause

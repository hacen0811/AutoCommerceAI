@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo [AutoCommerceAI] 일반 모드로 실행합니다.
python -m streamlit run main.py
pause

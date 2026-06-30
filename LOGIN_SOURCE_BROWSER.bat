@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo [AutoCommerceAI] 로그인 브라우저 실행
python tools\login_source_browser.py
pause

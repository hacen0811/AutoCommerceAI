@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo [AutoCommerceAI] Playwright 설치를 시작합니다.
python -m pip install --upgrade pip
python -m pip install playwright
python -m playwright install chromium
echo.
echo 설치가 끝났습니다.
pause

@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo [AutoCommerceAI] Playwright 테스트
python tools\test_playwright.py
pause

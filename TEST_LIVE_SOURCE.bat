@echo off
chcp 65001 >nul
cd /d %~dp0
title AutoCommerceAI Live Source 테스트

echo.
echo Playwright 설치/브라우저 상태를 확인합니다.
echo.
python scripts\test_live_source.py
pause

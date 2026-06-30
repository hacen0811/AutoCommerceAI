@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo ========================================
echo AutoCommerceAI 시작 메뉴
echo ========================================
echo 1. Playwright 설치
echo 2. Playwright 테스트
echo 3. 로그인 브라우저 열기
echo 4. 실제 웹 수집 모드 실행
echo 5. 일반 실행
echo.
set /p choice=번호를 입력하세요: 
if "%choice%"=="1" call INSTALL_PLAYWRIGHT.bat
if "%choice%"=="2" call TEST_PLAYWRIGHT.bat
if "%choice%"=="3" call LOGIN_SOURCE_BROWSER.bat
if "%choice%"=="4" call RUN_LIVE_SOURCE.bat
if "%choice%"=="5" call RUN_APP.bat

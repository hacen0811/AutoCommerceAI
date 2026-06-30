# Live Source Patch

추가 파일:
- INSTALL_LIVE_SOURCE.bat: Playwright + Chromium 설치
- LOGIN_SOURCE_BROWSER.bat: 도우인/타오바오/1688 로그인 세션 저장
- RUN_APP_LIVE.bat: 실제 웹 수집 모드로 앱 실행
- TEST_LIVE_SOURCE.bat: 실제 수집 연동 간단 테스트

사용 순서:
1. INSTALL_LIVE_SOURCE.bat 실행
2. LOGIN_SOURCE_BROWSER.bat 실행 후 필요한 사이트 로그인
3. RUN_APP_LIVE.bat 실행
4. 쇼츠 스튜디오에서 "실제 웹 수집 시도" 체크 후 패키지 생성

주의:
- 사이트 로그인/지역 제한/봇 차단으로 결과가 없을 수 있습니다.
- 수집 스크린샷은 exports/studio_video_sources_live 폴더에 저장됩니다.

# AutoCommerceAI 4.0 Playwright Source Collector

## 추가 기능
- 쇼츠 스튜디오 영상후보 탭에 실제 웹 수집 결과 영역 추가
- Playwright 설치 시 도우인/타오바오/1688 검색 페이지에서 링크 후보 수집 시도
- 사이트 로그인/차단/지역 제한이 있어도 앱이 멈추지 않도록 안전 처리
- 결과 저장: `exports/studio_video_sources_live/*.json`

## 사용 방법
1. 기본 실행은 기존과 같습니다.
   ```cmd
   python -m streamlit run main.py
   ```
2. 실제 웹 수집을 켜려면 먼저 설치합니다.
   ```cmd
   INSTALL_PLAYWRIGHT.bat
   ```
3. 실제 수집 모드로 실행합니다.
   ```cmd
   RUN_LIVE_SOURCE.bat
   ```
4. 도우인/타오바오가 로그인을 요구하면 열린 브라우저에서 로그인 후 다시 생성합니다.

## 주의
- 4.0은 자동 다운로드 전 단계입니다.
- 사이트 정책/로그인/지역 제한 때문에 실제 결과가 비어 있을 수 있습니다.
- 그래도 검색어·후보 URL·패키지 생성 기능은 계속 정상 작동합니다.

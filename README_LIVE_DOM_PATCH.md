# AutoCommerceAI Live DOM Patch

## 실행 순서

1. `INSTALL_PLAYWRIGHT.bat` 실행
2. `LOGIN_SOURCE_BROWSER.bat` 실행 후 도우인/타오바오/1688 접속 또는 로그인 확인
3. `RUN_LIVE_SOURCE.bat` 실행
4. 쇼츠 스튜디오 3.0에서 쿠팡 링크/상품명 입력 후 패키지 생성
5. `영상후보` 탭 확인

## 이번 패치 핵심

- 실제 브라우저 DOM에서 링크/이미지 후보를 읽습니다.
- 타오바오 구매내역/판매내역, 도우인 추천 메인, 로그인/피드백 링크를 제외합니다.
- 검색 페이지 스크린샷과 진단 JSON을 `exports/studio_video_sources_live`에 저장합니다.
- 로그인/차단/검색 결과 없음이어도 앱은 멈추지 않습니다.

## 직접 실행 명령

```cmd
cd /d "프로젝트 폴더 경로"
python -m pip install playwright
python -m playwright install chromium
set AUTO_SOURCE_LIVE=1
python -m streamlit run main.py
```

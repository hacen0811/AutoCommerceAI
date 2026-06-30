# AutoCommerceAI 실제 Playwright 패치

이번 패치는 `.bat` 파일이 실제로 포함되어 있으며, 각 배치 파일은 실행 위치를 자동으로 프로젝트 폴더로 보정합니다.

## 실행 순서

1. `INSTALL_PLAYWRIGHT.bat` 더블클릭
2. `TEST_PLAYWRIGHT.bat` 더블클릭
3. 필요하면 `LOGIN_SOURCE_BROWSER.bat` 더블클릭 후 도우인/타오바오 로그인
4. `RUN_LIVE_SOURCE.bat` 더블클릭
5. 쇼츠 스튜디오에서 `실제 웹 수집 시도` 체크 후 생성

## 직접 명령어

```cmd
cd /d "프로젝트폴더경로"
python -m pip install playwright
python -m playwright install chromium
set AUTO_SOURCE_LIVE=1
python -m streamlit run main.py
```

수집 결과는 `exports/studio_video_sources_live`에 JSON과 스크린샷으로 저장됩니다.

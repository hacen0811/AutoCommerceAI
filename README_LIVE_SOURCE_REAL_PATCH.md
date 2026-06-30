# AutoCommerceAI Live Source 실제 설치 패치

이번 패치에는 실제 `.bat` 파일이 포함되어 있습니다.

## 실행 순서

1. 압축을 풉니다.
2. 노란 폴더 `AutoCommerceAI_4.0_PlaywrightSourceCollector` 안으로 들어갑니다.
3. 아래 파일을 더블클릭합니다.

- `INSTALL_LIVE_SOURCE.bat`
- `TEST_LIVE_SOURCE.bat`
- `LOGIN_SOURCE_BROWSER.bat`
- `RUN_APP_LIVE.bat`

## CMD로 실행할 때

반드시 프로젝트 폴더 안에서 실행해야 합니다.
CMD 첫 줄이 `C:\Users\user>`이면 안 됩니다.

탐색기에서 프로젝트 폴더 주소창에 `cmd` 입력 후 Enter 하세요.

## 직접 명령

```cmd
python -m pip install playwright
python -m playwright install chromium
set AUTO_SOURCE_LIVE=1
python -m streamlit run main.py
```

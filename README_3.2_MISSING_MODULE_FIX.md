# AutoCommerceAI 3.2 Missing Module Fix

## 수정 내용
3.1 실행 시 발생한 오류를 수정했습니다.

오류:
`ModuleNotFoundError: app.ui.real_vision_mvp`

원인:
`main.py`가 존재하지 않는 UI 모듈을 import하고 있었습니다.

수정:
- 존재하지 않는 `real_vision_mvp` 메뉴/라우트 제거
- 쇼츠 스튜디오 3.0 라우팅 유지
- 데이터 가져오기/백업/복원 라우팅 유지

## 실행
`RUN_APP.bat` 더블클릭

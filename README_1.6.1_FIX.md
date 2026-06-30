# AutoCommerceAI 1.6.1 One Click Project Fix

## 수정 내용
- 원클릭 파이프라인 프로젝트 조회 안정화
  - ProjectSelector 추가
  - Repository 조회가 비어 보일 때 DB 직접 재조회

- 영상 저장 안정화
  - 중복 파일명 방지
  - 저장 파일 0MB 방지
  - 저장 실패 시 명확한 오류 발생

- 원클릭 화면 개선
  - 프로젝트 선택 표시
  - 영상 미등록 상태 안내
  - 실행 결과와 오류 표시 유지

## 하센님 실행 순서
1. 압축 해제
2. `python -m streamlit run main.py`
3. 🛒 제품 AI에서 프로젝트 확인
4. 🎬 영상관리에서 영상 업로드 후 `영상 저장`
5. ⚡ 원클릭 파이프라인에서 프로젝트 선택 후 실행

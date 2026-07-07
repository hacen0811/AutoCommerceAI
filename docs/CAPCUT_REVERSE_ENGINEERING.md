# CapCut Reverse Engineering

## 목표

AutoCommerceAI가 생성한 CapCut 프로젝트 ZIP을
CapCut에서 수정 없이 바로 열 수 있도록 만든다.

---

## 개발 원칙

- 실제 CapCut 샘플을 기준으로만 구현한다.
- 추측으로 필드를 추가하지 않는다.
- Builder 구조는 변경하지 않는다.
- project_builder.py는 오케스트레이터만 담당한다.
- 파일 하나씩 수정한다.
- 한 파일 완료 후 실행 확인한다.
- 실행 확인 후 커밋한다.
- 변경 후 이 문서를 업데이트한다.

---

## 현재 완료 상태

| 항목 | 상태 | 적용 여부 |
|---|---|---|
| Builder 구조 분리 | 완료 | 적용 |
| ProjectBuilder 오케스트레이터 | 완료 | 적용 |
| Material Registry | 완료 | 적용 |
| draft_content Top Level | 완료 | 적용 |
| material_refs | 분석 예정 | 미적용 |
| relationships | 분석 예정 | 미적용 |
| group_container | 분석 예정 | 미적용 |
| template 정보 | 분석 예정 | 미적용 |
| CapCut Import Test | 대기 | 미검증 |

---

## Sprint 43 계획

### Sprint 43-1

- Reverse Engineering 문서 생성
- 코드 수정 없음

### Sprint 43-2

- material_refs 분석
- 적용 파일 1개 선정
- 실행 확인
- Import Test

### Sprint 43-3

- relationships 분석
- 적용 파일 1개 선정
- 실행 확인
- Import Test

### Sprint 43-4

- group_container 분석
- 적용 파일 1개 선정
- 실행 확인
- Import Test

---

## Import Test 기록

| Sprint | 결과 | 비고 |
|---|---|---|
| 42-3 | JSON 생성 성공 | CapCut Import 미검증 |
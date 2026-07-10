# AutoCommerceAI CapCut Engine Progress

## 목표

AutoCommerceAI가 생성한 CapCut 프로젝트를
CapCut에서 수정 없이 바로 열 수 있도록 만드는 것을 목표로 한다.

---

# 완료

## Sprint 39

### Builder 분리

- [x] uuid_helper.py
- [x] material_builder.py
- [x] text_builder.py
- [x] segment_builder.py
- [x] track_builder.py
- [x] timeline_builder.py

---

## Sprint 40

### ProjectBuilder 오케스트레이터화

- [x] project_builder.py
- [x] Builder 호출 구조 정리
- [x] ZIP 생성 유지
- [x] 기존 기능 유지

---

## Sprint 41

### Builder 리팩터링

- [x] SegmentBuilder
- [x] TrackBuilder
- [x] TimelineBuilder

검증

- [x] 실행 확인
- [x] ZIP 생성 확인
- [x] 커밋 완료

---

## Sprint 42

### Material Registry

- [x] build_registry()
- [x] 기존 인터페이스 유지
- [x] Registry 구조 추가

---

# 현재 구조

CapCutProjectBuilder
    ↓
CapCutTimelineBuilder
    ↓
CapCutTrackBuilder
    ↓
CapCutSegmentBuilder
    ├── CapCutMaterialBuilder
    └── CapCutTextBuilder

---

# 다음 Sprint

## Sprint 42-2

실제 CapCut draft_content.json 비교

대상

- materials
- tracks
- canvas
- fps
- duration
- relationships

---

## Sprint 43

Material ID 연결

- material_id
- material_refs
- extra_material_refs

---

## Sprint 44

CapCut JSON 호환성 향상

---

## Sprint 45

CapCut Import 성공

---

# 개발 원칙

- Builder 구조는 변경하지 않는다.
- project_builder.py는 오케스트레이터만 담당한다.
- 파일 단위 전체 교체.
- 한 파일 완료 → 실행 확인 → 커밋.
- 기존 기능은 절대 깨지지 않도록 유지한다.
- 실제 CapCut 샘플을 기준으로 호환성을 개선한다.
# Sprint 2.1 - Vision Engine Stabilization

## 완료 내용
- YOLO Engine 안정화
  - GPU/CPU 자동 감지
  - 객체 중앙성 점수 추가
  - 실패 시 앱 중단 방지

- PaddleOCR Engine 안정화
  - OCR 텍스트 정규화
  - 중복 텍스트 제거
  - 상단/하단/중앙 영역 분류

- VisionScoreEngine 추가
  - Video AI + YOLO + OCR 점수 통합
  - 상품 후보 가점
  - 자막/텍스트 위험 감점
  - 밝기/대비/장면변화 반영

- SmartCut 2.0 적용
  - 후킹 컷
  - 썸네일 후보
  - 삭제 후보
  - 줌 후보
  - CapCut 타임라인 생성

## CapCut 기준 유지
- AI 음성 20 dB
- BGM 8 dB
- Pop 7 dB
- Click 8 dB
- Whoosh 6 dB

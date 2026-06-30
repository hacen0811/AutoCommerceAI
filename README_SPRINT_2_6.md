# Sprint 2.6 - One Click Pipeline

## 완료 내용
- WorkflowEngine 추가
  - Product Plan
  - Source Plan
  - Source Ranking
  - Real Vision
  - Auto Editor
  - Content Factory
  - CapCut Export

- PipelineState 추가
  - 단계별 상태 저장
  - 진행률 계산
  - 실패 단계 기록

- JobQueue 추가
  - 프로젝트 큐 추가
  - 상태 저장

- One Click Pipeline UI 추가
  - 프로젝트 선택 후 한 번에 실행
  - 진행률 표시
  - 단계별 상태 표시
  - 결과 JSON 확인

## 특징
YOLO/PaddleOCR 또는 영상이 없어도 가능한 단계는 계속 진행합니다.
실패한 단계는 오류로 기록하고, 나머지 단계는 실행합니다.

## CapCut 기준
- AI 음성 20 dB
- BGM 8 dB
- Pop 7 dB
- Click 8 dB
- Whoosh 6 dB

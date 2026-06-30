# AutoCommerceAI 1.7 FFmpeg Vision Fix

## 수정 내용
- MediaInfo 추가
  - ffprobe 우선 분석
  - ffprobe 미설치 시 OpenCV fallback
  - 파일명/크기/해상도/FPS/길이/방향 분석

- VideoAnalyzer 개선
  - 0MB가 아닌 영상의 기본 정보 표시 안정화
  - ffprobe 경고 메시지 개선

- VideoAIAnalyzer 개선
  - OpenCV 기반 프레임 분석 강화
  - ffprobe 없이도 샘플 프레임 추출 가능

- 시스템 체크 메뉴 추가
  - FFmpeg/ffprobe 설치 여부 확인
  - Windows 설치 안내 제공

## 하센님 실행 순서
1. 새 버전 실행
2. 🧰 시스템 체크에서 ffprobe 상태 확인
3. 영상관리에서 영상 기본 정보 확인
4. 원클릭 파이프라인 실행

## 참고
ffprobe가 없어도 OpenCV fallback으로 분석합니다.
다만 일부 영상 코덱은 Windows에서 OpenCV가 읽지 못할 수 있으므로 FFmpeg 설치를 권장합니다.

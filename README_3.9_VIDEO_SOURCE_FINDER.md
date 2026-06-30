# AutoCommerceAI 3.9 Video Source Finder

## 핵심 추가
- 쇼츠 스튜디오에 `영상후보` 탭 추가
- 쿠팡 링크/상품명 기반으로 도우인, 타오바오, 1688 영상 후보 TOP 추천
- 후보별 플랫폼, 검색어, 목적, 점수, URL 제공
- `exports/studio_video_sources/<상품명>/video_source_manifest.json` 저장
- Playwright 설치 상태 확인 및 다음 단계 자동 수집 준비

## 실행
```cmd
python -m streamlit run main.py
```

## 사용 흐름
1. 쇼츠 스튜디오 3.0 실행
2. 쿠팡 링크 입력
3. 상품명 입력 또는 쿠팡분석 결과 사용
4. 쇼핑쇼츠 패키지 생성
5. `영상후보` 탭에서 TOP 후보 확인
6. 후보 영상 저장 후 원본 영상으로 업로드하면 Vision/대본/CapCut 생성 진행

## 주의
도우인/타오바오는 로그인/지역/봇 차단이 있을 수 있어 3.9에서는 안전하게 후보 URL과 추천 점수를 먼저 제공합니다.
다음 단계에서 Playwright 로그인 세션 기반 실제 검색 결과 수집/다운로드 후보 자동 저장을 확장합니다.

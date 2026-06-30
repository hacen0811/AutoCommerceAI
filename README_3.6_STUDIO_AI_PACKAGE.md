# AutoCommerceAI 3.6 Studio AI Package

## 추가 기능
- 쇼츠 스튜디오 3.0에서 쿠팡 URL 식별값 자동 정리
- 원본 영상 기본 Vision 분석: 길이, 해상도, 비율, 샘플 프레임
- 타오바오/1688/도우인 검색 URL 자동 생성
- 타오바오 TOP10 / 도우인 TOP10 검색어 확장
- 15초/25초/35초 쇼핑쇼츠 대본 생성
- CapCut 편집안 + draft JSON 생성
- 유튜브 쇼츠 제목/설명/해시태그 생성
- 인스타 릴스 본문/해시태그 생성
- exports/studio_pipeline에 JSON/TXT/MD/CapCut draft 자동 저장

## 실행
```bat
python -m streamlit run main.py
```

## 사용 순서
1. 쇼츠 스튜디오 3.0 메뉴 선택
2. 쿠팡 링크 입력
3. 상품명 입력
4. 원본 영상 업로드
5. 쇼핑쇼츠 패키지 생성 클릭
6. 결과 탭에서 대본/CapCut/업로드 문구 복사

## 참고
현재 버전은 오프라인 템플릿 기반입니다. OpenAI/Gemini API 키를 연결하면 같은 구조에 실제 생성형 AI를 붙일 수 있습니다.

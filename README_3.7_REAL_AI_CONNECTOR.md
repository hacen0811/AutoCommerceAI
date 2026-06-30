# AutoCommerceAI 3.7 Real AI Connector

## 핵심 추가
- Shorts Studio 3.0에 실제 AI 연결 구조 추가
- `OPENAI_API_KEY`가 있으면 OpenAI로 대본/제목/본문/CapCut 팁 자동 생성
- `GEMINI_API_KEY`가 있으면 Gemini로 자동 생성
- API 키가 없거나 실패해도 기존 오프라인 템플릿으로 안전하게 생성
- Vision 분석 고도화: 영상 길이, 해상도, 9:16 여부, 밝기, 대비, 움직임 점수, 추천 후킹 시간
- UI에 `AI상태` 탭 추가
- API 키 설정용 BAT 파일 추가

## 실행
```cmd
python -m streamlit run main.py
```

## OpenAI 연결
`SET_OPENAI_KEY.bat` 실행 후 키 입력 → CMD/VS Code/Streamlit 완전 종료 후 재실행.

## Gemini 연결
`SET_GEMINI_KEY.bat` 실행 후 키 입력 → CMD/VS Code/Streamlit 완전 종료 후 재실행.

## 주의
- API 키가 없어도 오류가 나지 않습니다.
- 실제 영상 렌더링/CapCut 원클릭 열기 기능은 다음 버전에서 확장합니다.

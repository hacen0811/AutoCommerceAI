# AutoCommerceAI 1.2 Real Vision Runner

## 실행
```powershell
python -m pip install -r requirements.txt
python -m streamlit run main.py --server.address 127.0.0.1 --server.port 8502
```

## 실제 AI 모델 선택 설치
```powershell
python -m pip install -r requirements_ai_install.txt
```

## 핵심 변경
- Real Vision Runner 추가
- YOLO/PaddleOCR 설치 시 실제 실행
- 미설치 시 자동으로 Starter 분석으로 대체
- 분석 결과를 `exports/vision_results`에 JSON 저장
- 후킹 컷, 썸네일 후보, 자막 위치, CapCut 타임라인, 쇼츠 문구를 한 번에 확인

## 실사용 순서
1. 프로젝트 생성
2. 영상관리에서 원본 영상 업로드
3. AI 모델 연결에서 YOLO/PaddleOCR 상태 확인
4. Real Vision Runner 실행
5. CapCut 편집

## CapCut 기준
- AI 음성 20 dB
- BGM 8 dB
- Pop 7 dB
- Click 8 dB
- Whoosh 6 dB

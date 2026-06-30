# Git 시작 가이드

## 1. Git 저장소 만들기
```powershell
git init
git add .
git commit -m "AutoCommerceAI 1.1 Git Ready"
```

## 2. GitHub에 올리기
GitHub에서 새 저장소를 만든 뒤 아래 명령을 실행하세요.

```powershell
git remote add origin <GitHub 저장소 주소>
git branch -M main
git push -u origin main
```

## 3. 테스트 실행
```powershell
python -m pip install -r requirements_dev.txt
python -m pytest tests
```

또는 `RUN_TESTS.bat` 실행.

## 4. AI 모델 선택 설치
```powershell
python -m pip install -r requirements_ai_install.txt
```

## 주의
영상 파일, DB, AI 모델 파일은 Git에 올리지 않도록 `.gitignore`에 제외했습니다.

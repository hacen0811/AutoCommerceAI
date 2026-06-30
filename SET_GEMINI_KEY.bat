@echo off
set /p KEY=Gemini API Key 입력: 
setx GEMINI_API_KEY "%KEY%"
echo.
echo 저장 완료. CMD/VS Code/Streamlit을 모두 껐다가 다시 실행하세요.
pause

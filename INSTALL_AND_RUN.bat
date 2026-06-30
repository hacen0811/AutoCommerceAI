@echo off
chcp 65001 >nul
title AutoCommerceAI 설치 및 실행

echo Python 패키지를 설치합니다.
python -m pip install -r requirements.txt

echo AutoCommerceAI를 실행합니다.
python -m streamlit run main.py

pause

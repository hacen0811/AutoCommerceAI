@echo off
cd /d %~dp0
python -m pip install -r requirements.txt
python -m streamlit run main.py --server.address 127.0.0.1 --server.port 8502
pause

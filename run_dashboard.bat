@echo off
echo Starting PopUpSim Dashboard ...
cd /d "%~dp0"
streamlit run popupsim\frontend\dashboard.py --server.port=8051
pause

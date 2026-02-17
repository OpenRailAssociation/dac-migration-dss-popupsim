@echo off
echo Starting PopUpSim Dashboard ...
cd /d "%~dp0"
uv run streamlit run popupsim\frontend\dashboard.py --server.port=8051
pause

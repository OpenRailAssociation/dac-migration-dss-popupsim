@echo off
echo Starting PopUpSim Dashboard V2...
cd /d "%~dp0"
streamlit run popupsim\frontend\dashboard_v2.py --server.port=8052


pause

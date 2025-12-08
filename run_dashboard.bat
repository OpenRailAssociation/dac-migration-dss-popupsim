@echo off
REM PopUpSim Dashboard Launcher
REM Starts the Streamlit dashboard for viewing simulation results

echo Starting PopUpSim Dashboard...
echo.
echo Dashboard will open in your browser at http://localhost:8501
echo Press Ctrl+C to stop the dashboard
echo.

uv run streamlit run popupsim/frontend/streamlit_dashboard.py

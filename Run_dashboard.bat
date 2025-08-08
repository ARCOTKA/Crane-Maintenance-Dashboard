@echo off
REM This batch script runs a Streamlit application named dashboard.py

ECHO Starting the Streamlit dashboard...

REM The following command assumes that 'streamlit' is in your system's PATH.
streamlit run "dashboard.py"

ECHO.
ECHO Streamlit server has been stopped.
PAUSE

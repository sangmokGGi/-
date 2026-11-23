@echo off
cd /d "%~dp0"
echo ===============================
echo  MODUFIT V3 - Windows Launcher
echo ===============================
echo Installing/checking packages...
py -m pip install -r requirements.txt
if errorlevel 1 (
  echo Installation failed. Check Python 3.13 with: py --version
  pause
  exit /b 1
)
echo Starting MODUFIT at http://localhost:8501
py -m streamlit run app.py
pause

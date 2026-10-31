@echo off
cd /d "%~dp0"
if exist "..\..\..\..\..\.venv\Scripts\python.exe" (
  "..\..\..\..\..\.venv\Scripts\python.exe" start_preview.py
  exit /b
)
where py >nul 2>nul
if %errorlevel%==0 (
  py -3 start_preview.py
) else (
  python start_preview.py
)
pause

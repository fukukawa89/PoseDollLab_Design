@echo off
setlocal
title O22F7 PLA - Assembly Animation
if exist "%~dp0..\..\..\..\..\.venv\Scripts\python.exe" (
  "%~dp0..\..\..\..\..\.venv\Scripts\python.exe" "%~dp0start_preview.py" --assembly %*
  goto :done
)
where py >nul 2>nul
if not errorlevel 1 (
  py -3 "%~dp0start_preview.py" --assembly %*
  goto :done
)
python "%~dp0start_preview.py" --assembly %*
:done
set "preview_result=%errorlevel%"
if not "%preview_result%"=="0" pause
exit /b %preview_result%

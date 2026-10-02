@echo off
setlocal
set "PD_O21_OUT=%~1"
if not defined PD_O21_OUT exit /b 2
call "D:\ProgramFiles\Microsoft Visual Studio\2022\Community\VC\Auxiliary\Build\vcvars64.bat" >nul
if errorlevel 1 exit /b 1
cd /d "%~dp0.."
if not exist "%PD_O21_OUT%" mkdir "%PD_O21_OUT%"
set "PD_O21_SRC=Hardware\PoseDoll44\bench\revO21\firmware_source"
cl /nologo /std:c11 /W4 /WX /O2 /I "%PD_O21_SRC%" "%PD_O21_SRC%\raw46.c" "%PD_O21_SRC%\test_raw46.c" /Fo:"%PD_O21_OUT%\\" /Fe:"%PD_O21_OUT%\codec_test.exe"
if errorlevel 1 exit /b 1
pushd "%PD_O21_OUT%"
codec_test.exe
if errorlevel 1 exit /b 1
popd
cl /nologo /std:c11 /W4 /WX /O2 /I "%PD_O21_SRC%" "%PD_O21_SRC%\raw46.c" "%PD_O21_SRC%\session.c" "%PD_O21_SRC%\test_session.c" /Fo:"%PD_O21_OUT%\\" /Fe:"%PD_O21_OUT%\session_test.exe"
if errorlevel 1 exit /b 1
"%PD_O21_OUT%\session_test.exe"
exit /b %errorlevel%

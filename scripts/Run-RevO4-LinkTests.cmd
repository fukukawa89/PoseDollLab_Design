@echo off
setlocal
set "PD_REPO=%~dp0.."
set "PD_OUT=%~1"
if not defined PD_OUT exit /b 2
if exist "%PD_OUT%\pdr4_golden.bin" exit /b 3
call "D:\ProgramFiles\Microsoft Visual Studio\2022\Community\VC\Auxiliary\Build\vcvars64.bat" >nul
if errorlevel 1 exit /b 1
cd /d "%PD_REPO%"
if not exist "%PD_OUT%" mkdir "%PD_OUT%"
cl /nologo /std:c11 /W4 /WX /I Firmware\PoseDollFullBody\revO4 Firmware\PoseDollFullBody\revO4\remote_link.c Firmware\PoseDollFullBody\revO4\test_remote_link.c /Fo:"%PD_OUT%\\" /Fe:"%PD_OUT%\remote_link_test.exe"
if errorlevel 1 exit /b 1
"%PD_OUT%\remote_link_test.exe" "%PD_OUT%\pdr4_golden.bin"
exit /b %errorlevel%

@echo off
setlocal
set "PD_CN_OUT=%~1"
if not defined PD_CN_OUT exit /b 2
call "D:\ProgramFiles\Microsoft Visual Studio\2022\Community\VC\Auxiliary\Build\vcvars64.bat" >nul
if errorlevel 1 exit /b 1
cd /d "%~dp0.."
if not exist "%PD_CN_OUT%" mkdir "%PD_CN_OUT%"
cl /nologo /std:c11 /W4 /WX /O2 /I Firmware\PoseDollFullBody\revO5CN Firmware\PoseDollFullBody\revO5CN\mt6701_trial.c Firmware\PoseDollFullBody\revO5CN\test_mt6701_trial.c /Fo:"%PD_CN_OUT%\\" /Fe:"%PD_CN_OUT%\mt6701_trial_test.exe"
if errorlevel 1 exit /b 1
"%PD_CN_OUT%\mt6701_trial_test.exe"
exit /b %errorlevel%

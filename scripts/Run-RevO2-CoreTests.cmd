@echo off
setlocal
set "PD_REPO=%~dp0.."
set "PD_OUT=%~1"
if not defined PD_OUT exit /b 2
if exist "%PD_OUT%\golden_pd41.bin" (echo Refusing stale golden output & exit /b 3)
call "D:\ProgramFiles\Microsoft Visual Studio\2022\Community\VC\Auxiliary\Build\vcvars64.bat" >nul
if errorlevel 1 exit /b 1
cd /d "%PD_REPO%"
if not exist "%PD_OUT%" mkdir "%PD_OUT%"
cl /nologo /std:c11 /W4 /WX /I Firmware\PoseDollFullBody\main Firmware\PoseDollFullBody\main\pd41_core.c Firmware\PoseDollFullBody\tests\core_test.c /Fo:"%PD_OUT%\\" /Fe:"%PD_OUT%\core_test.exe"
if errorlevel 1 exit /b 1
"%PD_OUT%\core_test.exe" "%PD_OUT%\baseline_golden.bin"
if errorlevel 1 exit /b 1
cl /nologo /std:c11 /W4 /WX /I Firmware\PoseDollFullBody\main /I Firmware\PoseDollFullBody\revO2\main Firmware\PoseDollFullBody\main\pd41_core.c Firmware\PoseDollFullBody\revO2\main\pd41_gateway.c Firmware\PoseDollFullBody\revO2\tests\gateway_test.c /Fo:"%PD_OUT%\\" /Fe:"%PD_OUT%\gateway_test.exe"
if errorlevel 1 exit /b 1
"%PD_OUT%\gateway_test.exe" "%PD_OUT%\golden_pd41.bin"
if errorlevel 1 exit /b 1
cl /nologo /std:c11 /W4 /WX /I Firmware\PoseDollFullBody\main /I Firmware\PoseDollFullBody\revO2\main Firmware\PoseDollFullBody\main\pd41_core.c Firmware\PoseDollFullBody\revO2\main\pd41_session.c Firmware\PoseDollFullBody\revO2\tests\session_test.c /Fo:"%PD_OUT%\\" /Fe:"%PD_OUT%\session_test.exe"
if errorlevel 1 exit /b 1
"%PD_OUT%\session_test.exe"
exit /b %errorlevel%

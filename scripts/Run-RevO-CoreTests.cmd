@echo off
setlocal
set "PD_REPO=%~dp0.."
call "D:\ProgramFiles\Microsoft Visual Studio\2022\Community\VC\Auxiliary\Build\vcvars64.bat" >nul
if errorlevel 1 exit /b 1
cd /d "%PD_REPO%"
if not exist .local\revO-core mkdir .local\revO-core
cl /nologo /std:c11 /W4 /WX /I Firmware\PoseDollFullBody\main /I Firmware\PoseDollFullBody\revO\main Firmware\PoseDollFullBody\main\pd41_core.c Firmware\PoseDollFullBody\revO\main\pd41_gateway.c Firmware\PoseDollFullBody\revO\tests\gateway_test.c /Fo:.local\revO-core\ /Fe:.local\revO-core\gateway_test.exe
if errorlevel 1 exit /b 1
.local\revO-core\gateway_test.exe .local\revO-core\golden_pd41.bin
exit /b %errorlevel%

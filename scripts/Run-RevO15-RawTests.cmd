@echo off
setlocal
call "D:\ProgramFiles\Microsoft Visual Studio\2022\Community\VC\Auxiliary\Build\vcvars64.bat" >nul
if errorlevel 1 exit /b 1
if not exist ".local\revO15-core" mkdir ".local\revO15-core"
cl /nologo /std:c11 /W4 /WX /O2 /I Firmware\PoseDollFullBody\revO15 Firmware\PoseDollFullBody\revO15\raw46.c Firmware\PoseDollFullBody\revO15\test_raw46.c /Fo:.local\revO15-core\ /Fe:.local\revO15-core\raw46_test.exe
if errorlevel 1 exit /b 1
.local\revO15-core\raw46_test.exe .local\revO15-core\golden.bin
exit /b %ERRORLEVEL%

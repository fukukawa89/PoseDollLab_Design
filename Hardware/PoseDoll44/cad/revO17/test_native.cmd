@echo off
call "D:\ProgramFiles\Microsoft Visual Studio\2022\Community\VC\Auxiliary\Build\vcvars64.bat" >nul
if errorlevel 1 exit /b 1
cl /nologo /std:c11 /W4 /WX /O2 /I Firmware\PoseDollFullBody\revO17 Firmware\PoseDollFullBody\revO17\raw46.c Firmware\PoseDollFullBody\revO17\test_raw46.c /FoHardware\PoseDoll44\generated\revO17\ /FeHardware\PoseDoll44\generated\revO17\test_raw46.exe
if errorlevel 1 exit /b 1
Hardware\PoseDoll44\generated\revO17\test_raw46.exe Hardware\PoseDoll44\generated\revO17\codec_fixture.bin
if errorlevel 1 exit /b 1
cl /nologo /std:c11 /W4 /WX /O2 /I Firmware\PoseDollFullBody\revO17 Firmware\PoseDollFullBody\revO17\session.c Firmware\PoseDollFullBody\revO17\test_session.c /FoHardware\PoseDoll44\generated\revO17\ /FeHardware\PoseDoll44\generated\revO17\test_session.exe
if errorlevel 1 exit /b 1
Hardware\PoseDoll44\generated\revO17\test_session.exe
exit /b %errorlevel%

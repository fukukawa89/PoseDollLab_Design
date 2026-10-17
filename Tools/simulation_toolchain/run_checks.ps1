$ErrorActionPreference = 'Stop'
$freecadPython = 'D:\ProgramFiles\FreeCAD\bin\python.exe'
if (-not (Test-Path -LiteralPath $freecadPython)) { throw 'FreeCAD Python was not found at the configured path.' }
& $freecadPython -X utf8 (Join-Path $PSScriptRoot 'verify_toolchain.py')
if ($LASTEXITCODE -ne 0) { throw 'Toolchain verification failed; inspect the latest run logs.' }
& $freecadPython -X utf8 (Join-Path $PSScriptRoot 'summarize_toolchain.py')
if ($LASTEXITCODE -ne 0) { throw 'Verification report generation failed.' }

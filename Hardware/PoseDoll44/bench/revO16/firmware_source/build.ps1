param([ValidateSet('G0','BODY')][string]$Role='G0',[Parameter(Mandatory=$true)][string]$BuildRoot,[string]$Defaults)
$ErrorActionPreference='Stop'
$taskRoot=(Resolve-Path -LiteralPath $PSScriptRoot).Path
$env:IDF_PATH='D:/ProgramFiles/esp/v6.1/esp-idf'
$env:IDF_TOOLS_PATH='C:/Espressif/tools'
$env:IDF_PYTHON_ENV_PATH='C:/Espressif/tools/python/v6.1/venv'
$env:ESP_ROM_ELF_DIR='C:/Espressif/tools/esp-rom-elfs/20241011'
$env:IDF_COMPONENT_LOCAL_STORAGE_URL='file://C:/Espressif/tools'
$env:PYTHONUTF8='1'
$env:IDF_PY_BUILD_JOBS='4'
$env:ESP_IDF_VERSION='6.1'
$env:IDF_VERSION='6.1.0'
$env:PATH='C:/Espressif/tools/python/v6.1/venv/Scripts;C:/Espressif/tools/cmake/4.0.3/bin;C:/Espressif/tools/ninja/1.12.1;C:/Espressif/tools/xtensa-esp-elf/esp-15.2.0_20251204/xtensa-esp-elf/bin;C:/Espressif/tools/riscv32-esp-elf/esp-15.2.0_20251204/riscv32-esp-elf/bin;'+$env:PATH
$BuildRoot=[IO.Path]::GetFullPath($BuildRoot)
$roleBuild=Join-Path $BuildRoot $Role
$taskDefaults=if ($Defaults) { (Resolve-Path -LiteralPath $Defaults).Path } else { Join-Path $taskRoot "sdkconfig.$Role.defaults" }
if ($Defaults -and (Test-Path -LiteralPath (Join-Path $roleBuild 'sdkconfig'))) { throw 'Paired defaults require a fresh BuildRoot so an old peer MAC cannot be reused.' }
New-Item -ItemType Directory -Path $roleBuild -Force | Out-Null
Push-Location $taskRoot
try {
 & "$env:IDF_PYTHON_ENV_PATH/Scripts/python.exe" "$env:IDF_PATH/tools/idf.py" -B "$roleBuild" "-DSDKCONFIG=$roleBuild/sdkconfig" "-DSDKCONFIG_DEFAULTS=$taskDefaults" build
 exit $LASTEXITCODE
} finally { Pop-Location }

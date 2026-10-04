[CmdletBinding()]
param(
 [ValidateSet('All','Initialize','CAD','Electronics','Firmware','OfflineTests','Reports')][string]$Stage='All',
 [string]$Python='',
 [string]$KiCadPython='D:/ProgramFiles/KiCad/10.0/bin/python.exe'
)
$ErrorActionPreference='Stop'
$repoRoot=(Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '..')).Path
if(!$Python){$Python=Join-Path $repoRoot '.venv/Scripts/python.exe'}
function Invoke-Checked([string]$Program,[string[]]$CommandArgs){
 & $Program @CommandArgs
 if($LASTEXITCODE -ne 0){throw "Command failed: $Program (exit $LASTEXITCODE)"}
}
Push-Location $repoRoot
try {
 if($Stage -eq 'Initialize'){
  Invoke-Checked $Python @('scripts/freeze_revo_baseline.py')
  Invoke-Checked $Python @('scripts/prepare_revo.py')
  return
 }
 if(!(Test-Path 'Hardware/PoseDoll44/mechanical_manifest/desktop_revO.json')){throw 'Run -Stage Initialize first.'}
 if($Stage -in @('All','Electronics')){
  Invoke-Checked $KiCadPython @('-X','utf8','scripts/build_revo_electronics.py')
 }
 if($Stage -in @('All','CAD')){
  Invoke-Checked $Python @('-X','utf8','Hardware/PoseDoll44/tools/run_cad.py','Hardware/PoseDoll44/cad/revO/export_joints.py')
  Invoke-Checked $Python @('-X','utf8','scripts/study_revo.py')
  Invoke-Checked $Python @('-X','utf8','Hardware/PoseDoll44/tools/run_cad.py','Hardware/PoseDoll44/cad/revO/export_layouts.py')
  Copy-Item -LiteralPath 'Hardware/PoseDoll44/cad/revO/review.template.html' -Destination 'Hardware/PoseDoll44/generated/revO/RevO_Design_Review.html' -Force
 }
 if($Stage -in @('All','Firmware')){Invoke-Checked $Python @('-X','utf8','scripts/build_revo_firmware.py')}
 if($Stage -in @('All','OfflineTests')){Invoke-Checked $Python @('-X','utf8','scripts/verify_revo.py')}
 if($Stage -in @('All','Reports')){Invoke-Checked $Python @('-X','utf8','scripts/report_revo.py')}
 Write-Host 'Rev O design iteration built. Inspect FAIL/NOT_RUN engineering gates; build success is not manufacturing release.'
} finally {Pop-Location}

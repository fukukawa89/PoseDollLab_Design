[CmdletBinding()]
param([switch]$NoBrowser,[ValidateRange(1024,65535)][int]$Port=8874,[ValidateSet('revO3','revO2','revO','revN')][string]$Revision='revO3',[ValidatePattern('^[A-Za-z0-9_-]+$')][string]$RunId)
$ErrorActionPreference='Stop'
$repoRoot=(Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '..')).Path
$root=Join-Path $repoRoot 'Hardware/PoseDoll44'
if($Revision -in @('revO3','revO2')){
 if(!$RunId){
  $latestPath=Join-Path $root "verification/$Revision/latest.json"
  $latest=Get-Content -Raw -LiteralPath $latestPath | ConvertFrom-Json
  if($latest.execution_status -ne 'PASS_EXECUTION_ONLY'){throw "Latest execution is incomplete. Use an explicitly reviewed -RunId or finish the run first."}
  $RunId=$latest.run_id
 }
 $pageRel="generated/$Revision/runs/$RunId/review.html"
 $assets=@((Join-Path $root $pageRel),(Join-Path $root "generated/$Revision/runs/$RunId/joint/mesh.json"),(Join-Path $root "generated/$Revision/runs/$RunId/packaging_scene.json"))
}else{
 $pageRel=if($Revision -eq 'revO'){'generated/revO/RevO_Design_Review.html'}else{'generated/revN/RevN_Chest_Review.html'}
 $assets=if($Revision -eq 'revO'){@((Join-Path $root $pageRel),(Join-Path $root 'generated/revO/layout_data.json'),(Join-Path $root 'generated/revO/joints/M6/mesh.json'))}else{@((Join-Path $root $pageRel),(Join-Path $root 'generated/revN/manny/meshes.bin'),(Join-Path $root 'generated/revN/quinn/meshes.bin'))}
}
$page=Join-Path $root $pageRel
$url="http://127.0.0.1:$Port/$pageRel"
foreach($asset in $assets){if(!(Test-Path -LiteralPath $asset)){throw "Local export missing: $asset. Git does not include large meshes; restore or generate them first."}}
$expected=[IO.File]::ReadAllBytes($page)
function Test-Viewer{
 $client=New-Object System.Net.WebClient
 try{$actual=$client.DownloadData($url);return [Convert]::ToBase64String($actual).Equals([Convert]::ToBase64String($expected))}catch{return $false}finally{$client.Dispose()}
}
if(!(Test-Viewer)){
 $socket=New-Object System.Net.Sockets.TcpClient
 try{$socket.Connect('127.0.0.1',$Port);$used=$true}catch{$used=$false}finally{$socket.Dispose()}
 if($used){throw "Port $Port belongs to another server. Choose -Port; no process was stopped."}
 $python=Join-Path $repoRoot '.venv/Scripts/python.exe'
 if(!(Test-Path -LiteralPath $python)){$python=(Get-Command python.exe -ErrorAction Stop).Source}
 $logs=Join-Path $repoRoot '.local/viewer';New-Item -ItemType Directory -Path $logs -Force | Out-Null
 $process=Start-Process -FilePath $python -ArgumentList @('-m','http.server',"$Port",'--bind','127.0.0.1') -WorkingDirectory $root -WindowStyle Hidden -RedirectStandardOutput (Join-Path $logs 'stdout.log') -RedirectStandardError (Join-Path $logs 'stderr.log') -PassThru
 $ready=$false
 foreach($i in 1..20){Start-Sleep -Milliseconds 300;if(Test-Viewer){$ready=$true;break};if($process.HasExited){break}}
 if(!$ready){throw "Viewer did not start. See $logs"}
 @{pid=$process.Id;root=$root;url=$url} | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $logs 'server.json') -Encoding utf8
}
Write-Host $url
if(!$NoBrowser){Start-Process $url}

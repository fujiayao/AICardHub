$ErrorActionPreference='Stop'
$repo=[IO.Path]::GetFullPath((Split-Path -Parent $PSScriptRoot))
$stateFile=Join-Path $repo '.local\services.json'
if(-not (Test-Path -LiteralPath $stateFile)){Write-Output '没有本项目记录的运行进程。';return}
$processes=@(Get-CimInstance Win32_Process)
$records=@(Get-Content -LiteralPath $stateFile -Raw|ConvertFrom-Json)
foreach($record in $records){
 $rootProcess=$processes|Where-Object ProcessId -eq $record.pid|Select-Object -First 1
 if(-not $rootProcess){continue}
 $recordedStart=if($record.started_at -is [DateTime]){[DateTimeOffset]$record.started_at}else{[DateTimeOffset]::Parse([string]$record.started_at)}
 $created=[DateTimeOffset]$rootProcess.CreationDate
 if([Math]::Abs(($created-$recordedStart).TotalSeconds) -gt 60){Write-Output "$($record.name)进程标识已变化，跳过。";continue}
 if($rootProcess.Name -notmatch '^(uv|node|cmd|python|pwsh|powershell)\.exe$'){Write-Output "$($record.name)进程类型未匹配，跳过。";continue}
 $tree=[Collections.Generic.List[object]]::new()
 $tree.Add($rootProcess)
 for($index=0;$index -lt $tree.Count;$index++){
  foreach($child in @($processes|Where-Object ParentProcessId -eq $tree[$index].ProcessId)){
   if($child.CreationDate -ge $rootProcess.CreationDate){$tree.Add($child)}
  }
 }
 # Validate a live service descendant against this checkout before stopping its tree.
 $matched=$false
 foreach($process in $tree){
  $command=[string]$process.CommandLine
  if($command.IndexOf($repo,[StringComparison]::OrdinalIgnoreCase) -ge 0){$matched=$true}
 }
 if(-not $matched){Write-Output "$($record.name)路径无法确认属于本项目，保留进程。";continue}
 for($index=$tree.Count-1;$index -ge 0;$index--){
  $current=Get-CimInstance Win32_Process -Filter "ProcessId=$($tree[$index].ProcessId)" -ErrorAction SilentlyContinue
  if($current -and $current.CreationDate -eq $tree[$index].CreationDate){Stop-Process -Id $current.ProcessId -ErrorAction SilentlyContinue}
 }
 Write-Output "$($record.name)已停止。"
}
Write-Output '只处理本项目记录且创建时间和路径匹配的进程；未删除数据。'

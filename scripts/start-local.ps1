param([switch]$SkipInstall, [switch]$NoOpen, [switch]$DemoModel)
$ErrorActionPreference = 'Stop'
$repo = Split-Path -Parent $PSScriptRoot
$state = Join-Path $repo '.local'
$null = New-Item -ItemType Directory -Path $state -Force
$uvCommand = Get-Command uv.exe -ErrorAction SilentlyContinue
$uv = if ($uvCommand) { $uvCommand.Source } else { Join-Path $env:USERPROFILE '.local\bin\uv.exe' }
if (-not (Test-Path -LiteralPath $uv)) { throw '未找到uv，请先安装uv和Python3.12。' }
$pnpm = (Get-Command pnpm.cmd -ErrorAction Stop).Source
if (-not (Test-Path -LiteralPath (Join-Path $repo 'server\.env'))) { throw '请先根据server/.env.example配置本机数据库。' }
function Invoke-Checked([string]$Directory, [string]$Executable, [string[]]$Arguments) {
 Push-Location -LiteralPath $Directory
 try {
  & $Executable @Arguments
  if ($LASTEXITCODE -ne 0) { throw "准备失败：$Executable $($Arguments -join ' ')" }
 } finally { Pop-Location }
}
if (-not $SkipInstall) {
 Invoke-Checked (Join-Path $repo 'server') $uv @('sync','--frozen')
 foreach ($app in @('h5','admin')) { Invoke-Checked (Join-Path $repo "apps\$app") $pnpm @('install','--frozen-lockfile') }
}
Invoke-Checked (Join-Path $repo 'server') $uv @('run','alembic','upgrade','head')
Invoke-Checked (Join-Path $repo 'server') $uv @('run','python','-m','app.seed')
$services = @(
 @{Name='api'; Port=8000; Directory=(Join-Path $repo 'server'); Exe=$uv; Args=@('run','uvicorn','app.main:app','--host','127.0.0.1','--port','8000')},
 @{Name='scheduler'; Port=0; Directory=(Join-Path $repo 'server'); Exe=$uv; Args=@('run','python','-m','app.scheduler')},
 @{Name='h5'; Port=5173; Directory=(Join-Path $repo 'apps\h5'); Exe=$pnpm; Args=@('dev','--host','127.0.0.1','--port','5173','--strictPort')},
 @{Name='admin'; Port=5174; Directory=(Join-Path $repo 'apps\admin'); Exe=$pnpm; Args=@('dev','--host','127.0.0.1','--port','5174','--strictPort')}
)
$records = [Collections.Generic.List[object]]::new()
$modelEnvironment = @{}
foreach ($name in @('LLM_MODE','LLM_FALLBACK_ENABLED','LLM_TERTIARY_ENABLED')) {
 $modelEnvironment[$name] = [Environment]::GetEnvironmentVariable($name, 'Process')
}
if ($DemoModel) {
 $env:LLM_MODE='fake'
 $env:LLM_FALLBACK_ENABLED='false'
 $env:LLM_TERTIARY_ENABLED='false'
}
try {
foreach ($service in $services) {
 $busy = if ($service.Port -gt 0) { Get-NetTCPConnection -LocalPort $service.Port -State Listen -ErrorAction SilentlyContinue } else { Get-CimInstance Win32_Process -Filter "Name='python.exe'" | Where-Object { $_.CommandLine -match '-m\s+app\.scheduler' } }
 if ($busy) { Write-Output "$($service.Name)已有服务，保留现有进程。"; continue }
 $process = Start-Process -FilePath $service.Exe -ArgumentList $service.Args -WorkingDirectory $service.Directory -WindowStyle Hidden -PassThru -RedirectStandardOutput (Join-Path $state "$($service.Name).out.log") -RedirectStandardError (Join-Path $state "$($service.Name).err.log")
 $created=(Get-CimInstance Win32_Process -Filter "ProcessId=$($process.Id)").CreationDate
 $records.Add([pscustomobject]@{name=$service.Name;pid=$process.Id;port=$service.Port;started_at=$created.ToUniversalTime().ToString('o')})
}
} finally {
 foreach ($name in $modelEnvironment.Keys) { [Environment]::SetEnvironmentVariable($name,$modelEnvironment[$name],'Process') }
}
if ($records.Count -gt 0) {
 $stateFile = Join-Path $state 'services.json'
 $old = if (Test-Path -LiteralPath $stateFile) { @(Get-Content -LiteralPath $stateFile -Raw | ConvertFrom-Json) } else { @() }
 $retained = @($old | Where-Object { $_.name -notin @($records | ForEach-Object name) })
 ConvertTo-Json -InputObject @($retained + $records.ToArray()) -Depth 4 | Set-Content -LiteralPath $stateFile -Encoding utf8
}
$deadline = (Get-Date).AddSeconds(50)
$ready = $false
do {
 try {
  $health = Invoke-RestMethod -Uri 'http://127.0.0.1:8000/health' -TimeoutSec 2
  $h5 = Invoke-WebRequest -UseBasicParsing -Uri 'http://127.0.0.1:5173/card/demo' -TimeoutSec 2
  $admin = Invoke-WebRequest -UseBasicParsing -Uri 'http://127.0.0.1:5174' -TimeoutSec 2
  $ready = $health.status -eq 'ok' -and $h5.StatusCode -eq 200 -and $admin.StatusCode -eq 200
 } catch { Start-Sleep -Milliseconds 500 }
} until ($ready -or (Get-Date) -ge $deadline)
if (-not $ready) { throw '服务未全部就绪，请查看.local下服务日志。' }
if ($DemoModel -and $health.llm_mode -ne 'fake') { throw '当前已有真实模型服务。先停止本项目服务，再使用-DemoModel启动自动验收模式。' }
Write-Output '本地服务已就绪：'
Write-Output '访客名片：http://127.0.0.1:5173/card/demo'
Write-Output '员工入口：http://127.0.0.1:5173/login'
Write-Output '管理后台：http://127.0.0.1:5174'
Write-Output '演示账号请查看server/local-credentials.json。'
Write-Output "当前模型运行方式：$($health.llm_mode)"
if (-not $NoOpen) { Start-Process 'http://127.0.0.1:5173/card/demo' }

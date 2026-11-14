param([switch]$SkipInstall, [switch]$NoOpen)
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
 @{Name='h5'; Port=5173; Directory=(Join-Path $repo 'apps\h5'); Exe=$pnpm; Args=@('dev','--host','127.0.0.1','--port','5173','--strictPort')},
 @{Name='admin'; Port=5174; Directory=(Join-Path $repo 'apps\admin'); Exe=$pnpm; Args=@('dev','--host','127.0.0.1','--port','5174','--strictPort')}
)
$records = [Collections.Generic.List[object]]::new()
foreach ($service in $services) {
 $busy = Get-NetTCPConnection -LocalPort $service.Port -State Listen -ErrorAction SilentlyContinue
 if ($busy) { Write-Output "$($service.Name)端口$($service.Port)已有服务，保留现有进程。"; continue }
 $process = Start-Process -FilePath $service.Exe -ArgumentList $service.Args -WorkingDirectory $service.Directory -WindowStyle Hidden -PassThru -RedirectStandardOutput (Join-Path $state "$($service.Name).out.log") -RedirectStandardError (Join-Path $state "$($service.Name).err.log")
 $records.Add([pscustomobject]@{name=$service.Name;pid=$process.Id;port=$service.Port;started_at=(Get-Date).ToUniversalTime().ToString('o')})
}
if ($records.Count -gt 0) { $records | ConvertTo-Json -AsArray | Set-Content -LiteralPath (Join-Path $state 'services.json') -Encoding utf8 }
$deadline = (Get-Date).AddSeconds(50)
$ready = $false
do {
 try {
  $health = Invoke-RestMethod -Uri 'http://127.0.0.1:8000/health' -TimeoutSec 2
  $h5 = Invoke-WebRequest -Uri 'http://127.0.0.1:5173/card/demo' -TimeoutSec 2
  $admin = Invoke-WebRequest -Uri 'http://127.0.0.1:5174' -TimeoutSec 2
  $ready = $health.status -eq 'ok' -and $h5.StatusCode -eq 200 -and $admin.StatusCode -eq 200
 } catch { Start-Sleep -Milliseconds 500 }
} until ($ready -or (Get-Date) -ge $deadline)
if (-not $ready) { throw '服务未全部就绪，请查看.local下三个服务的日志。' }
Write-Output '本地服务已就绪：'
Write-Output '访客名片：http://127.0.0.1:5173/card/demo'
Write-Output '员工入口：http://127.0.0.1:5173/login'
Write-Output '管理后台：http://127.0.0.1:5174'
Write-Output '演示账号请查看server/local-credentials.json。'
if (-not $NoOpen) { Start-Process 'http://127.0.0.1:5173/card/demo' }

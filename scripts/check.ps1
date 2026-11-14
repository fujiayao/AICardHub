param([switch]$E2E)
$ErrorActionPreference = 'Stop'
$repo = Split-Path -Parent $PSScriptRoot
$uvCommand = Get-Command uv.exe -ErrorAction SilentlyContinue
$uv = if ($uvCommand) { $uvCommand.Source } else { Join-Path $env:USERPROFILE '.local\bin\uv.exe' }
$pnpm = (Get-Command pnpm.cmd -ErrorAction Stop).Source
function Check([string]$Directory, [string]$Executable, [string[]]$Arguments) {
 Push-Location -LiteralPath $Directory
 try {
  & $Executable @Arguments
  if ($LASTEXITCODE -ne 0) { throw "检查未通过：$($Arguments -join ' ')" }
 } finally { Pop-Location }
}
$server = Join-Path $repo 'server'
Check $server $uv @('run','ruff','check','app','tests')
Check $server $uv @('run','ruff','format','--check','app','tests')
Check $server $uv @('run','mypy','app')
Check $server $uv @('run','pytest','-q')
Check $server $uv @('run','alembic','heads')
foreach ($app in @('h5','admin')) {
 $directory = Join-Path $repo "apps\$app"
 Check $directory $pnpm @('lint')
 Check $directory $pnpm @('typecheck')
 Check $directory $pnpm @('build')
}
Check (Join-Path $repo 'apps\h5') $pnpm @('test','--run')
if ($E2E) { Check $server $uv @('run','python','../e2e/local_acceptance.py') }
Write-Output '本次指定的检查全部通过。'

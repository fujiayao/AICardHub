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
Check $server $uv @('run','python','../scripts/check-contract.py')
Check $server $uv @('run','ruff','check','app','tests')
Check $server $uv @('run','ruff','format','--check','app','tests')
Check $server $uv @('run','mypy','app')
$modelVariables = @('LLM_MODE','LLM_API_KEY','LLM_FALLBACK_API_KEY','LLM_TERTIARY_API_KEY','LLM_FALLBACK_ENABLED','LLM_TERTIARY_ENABLED')
$savedModelEnvironment = @{}
foreach ($name in $modelVariables) { $savedModelEnvironment[$name] = [Environment]::GetEnvironmentVariable($name, 'Process') }
try {
 $env:LLM_MODE = 'fake'
 $env:LLM_API_KEY = ''
 $env:LLM_FALLBACK_API_KEY = ''
 $env:LLM_TERTIARY_API_KEY = ''
 $env:LLM_FALLBACK_ENABLED = 'false'
 $env:LLM_TERTIARY_ENABLED = 'false'
 Check $server $uv @('run','pytest','-q')
} finally {
 foreach ($name in $modelVariables) { [Environment]::SetEnvironmentVariable($name, $savedModelEnvironment[$name], 'Process') }
}
Check $server $uv @('run','alembic','heads')
foreach ($app in @('h5','admin')) {
 $directory = Join-Path $repo "apps\$app"
 Check $directory $pnpm @('lint')
 Check $directory $pnpm @('typecheck')
 Check $directory $pnpm @('build')
}
Check (Join-Path $repo 'apps\h5') $pnpm @('test','--run')
if ($E2E) {
 $health = Invoke-RestMethod -Uri 'http://127.0.0.1:8000/health' -TimeoutSec 3
 if ($health.llm_mode -ne 'fake') { throw '自动业务验收需要演示模型。请先停止本项目服务，再用start-local.ps1 -DemoModel启动；真实模型验收使用e2e/responses_acceptance.py。' }
 Check $server $uv @('run','python','../e2e/local_acceptance.py')
 $previousFlag = [Environment]::GetEnvironmentVariable('AICARD_LLM_MODE','Process')
 try {
  $env:AICARD_LLM_MODE='fake'
  Check (Join-Path $repo 'e2e\browser') $pnpm @('test')
 } finally { [Environment]::SetEnvironmentVariable('AICARD_LLM_MODE',$previousFlag,'Process') }
}
Write-Output '本次指定的检查全部通过。'

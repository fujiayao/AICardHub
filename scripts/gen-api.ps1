$ErrorActionPreference = 'Stop'
$repo = Split-Path -Parent $PSScriptRoot
$uvCommand = Get-Command uv.exe -ErrorAction SilentlyContinue
$uv = if ($uvCommand) { $uvCommand.Source } else { Join-Path $env:USERPROFILE '.local\bin\uv.exe' }
Push-Location -LiteralPath (Join-Path $repo 'server')
try {
 & $uv run python -m app.export_openapi ../contracts/openapi.json
 if ($LASTEXITCODE -ne 0) { throw 'OpenAPI导出失败' }
 & $uv run python ../scripts/check-contract.py
 if ($LASTEXITCODE -ne 0) { throw '契约检查失败' }
} finally { Pop-Location }
foreach ($entry in @(@('h5','generate:api'),@('admin','gen:api'))) {
 Push-Location -LiteralPath (Join-Path $repo ('apps\'+$entry[0]))
 try {
  & pnpm.cmd $entry[1]
  if ($LASTEXITCODE -ne 0) { throw "前端接口生成失败：$($entry[0])" }
 } finally { Pop-Location }
}

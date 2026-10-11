$ErrorActionPreference = "Stop"

$projectRoot = Split-Path -Parent $PSScriptRoot
$frontendRoot = Join-Path $projectRoot "frontend"

if (-not (Get-Command npm -ErrorAction SilentlyContinue)) {
    throw 'npm was not found. Install Node.js 20 or newer first.'
}

if (-not (Test-Path (Join-Path $frontendRoot "node_modules"))) {
    Write-Host "首次启动，正在安装前端依赖..." -ForegroundColor Cyan
    & (Join-Path $PSScriptRoot 'setup-frontend.ps1')
}

Write-Host "前端地址：http://127.0.0.1:5173" -ForegroundColor Green
npm --prefix $frontendRoot run dev

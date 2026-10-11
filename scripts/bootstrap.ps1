param(
    [switch]$SkipBackend,
    [switch]$SkipFrontend
)

$ErrorActionPreference = 'Stop'

$projectRoot = Split-Path -Parent $PSScriptRoot
Set-Location -LiteralPath $projectRoot

Write-Host 'Preparing the distributed library project...' -ForegroundColor Cyan

if (-not (Test-Path -LiteralPath '.env')) {
    Copy-Item -LiteralPath '.env.example' -Destination '.env'
    Write-Host 'Created .env from .env.example.' -ForegroundColor Yellow
}

& (Join-Path $PSScriptRoot 'import-data.ps1')

if (-not $SkipBackend) {
    & (Join-Path $PSScriptRoot 'setup-backend.ps1')
}

if (-not $SkipFrontend) {
    & (Join-Path $PSScriptRoot 'setup-frontend.ps1')
}

& (Join-Path $PSScriptRoot 'verify-data.ps1')

Write-Host ''
Write-Host 'Bootstrap completed.' -ForegroundColor Green
Write-Host 'Start APIs with: .\scripts\start-backend.ps1'
Write-Host 'Start the web UI in another terminal with: .\scripts\start-frontend.ps1'

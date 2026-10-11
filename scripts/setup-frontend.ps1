$ErrorActionPreference = 'Stop'

$projectRoot = Split-Path -Parent $PSScriptRoot
$frontendRoot = Join-Path $projectRoot 'frontend'

if (-not (Get-Command npm -ErrorAction SilentlyContinue)) {
    throw 'npm was not found. Install Node.js 20 or newer first.'
}

if (Test-Path -LiteralPath (Join-Path $frontendRoot 'package-lock.json')) {
    npm --prefix $frontendRoot ci
} else {
    npm --prefix $frontendRoot install
}

if ($LASTEXITCODE -ne 0) {
    throw 'Frontend dependency installation failed.'
}

Write-Host 'Frontend environment is ready.' -ForegroundColor Green

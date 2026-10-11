$ErrorActionPreference = 'Stop'

$projectRoot = Split-Path -Parent $PSScriptRoot
Set-Location -LiteralPath $projectRoot

if (-not (Test-Path -LiteralPath '.venv\Scripts\python.exe')) {
    throw 'Run .\scripts\setup-backend.ps1 first.'
}

& '.\.venv\Scripts\python.exe' -m pytest '.\backend\tests' -q

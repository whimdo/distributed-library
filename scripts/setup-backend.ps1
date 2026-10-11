$ErrorActionPreference = 'Stop'

$projectRoot = Split-Path -Parent $PSScriptRoot
Set-Location -LiteralPath $projectRoot

$pythonLauncher = $null
if (Get-Command py -ErrorAction SilentlyContinue) {
    $pythonLauncher = @('py', '-3')
} elseif (Get-Command python -ErrorAction SilentlyContinue) {
    $pythonLauncher = @('python')
} else {
    throw 'Python 3 was not found. Install Python 3.11 or newer first.'
}

if ($pythonLauncher.Count -eq 2) {
    & $pythonLauncher[0] $pythonLauncher[1] -m venv --upgrade-deps .venv
} else {
    & $pythonLauncher[0] -m venv --upgrade-deps .venv
}
if ($LASTEXITCODE -ne 0) {
    throw 'Failed to create or refresh the Python virtual environment.'
}

& '.\.venv\Scripts\python.exe' -m pip install --upgrade pip
if ($LASTEXITCODE -ne 0) {
    throw 'Failed to upgrade pip in the virtual environment.'
}

& '.\.venv\Scripts\python.exe' -m pip install -r '.\backend\requirements.txt'

if ($LASTEXITCODE -ne 0) {
    throw 'Backend dependency installation failed.'
}

Write-Host 'Backend environment is ready.'

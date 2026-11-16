param([switch]$Reports)
$ErrorActionPreference = 'Stop'
$program = 'FGMappingEngineering'
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$venv = Join-Path $env:LOCALAPPDATA "$program\venv"
$python = py -3.12 -c 'import sys; print(sys.executable)'
if ($LASTEXITCODE -ne 0) { throw 'Python 3.12 is required.' }
& $python -m venv $venv
& (Join-Path $venv 'Scripts\python.exe') -m pip install --disable-pip-version-check -r (Join-Path $root 'requirements-lock.txt')
if ($LASTEXITCODE -ne 0) { throw 'Pinned Qt installation failed.' }
Write-Host "Development environment: $venv"

if ($Reports) {
    & (Join-Path $venv 'Scripts\python.exe') -m pip install --disable-pip-version-check -r (Join-Path $root 'requirements-reports.txt')
    if ($LASTEXITCODE -ne 0) { throw 'Optional report dependency installation failed.' }
}

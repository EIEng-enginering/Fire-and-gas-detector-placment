$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$python = Join-Path $env:LOCALAPPDATA 'FGMappingEngineering\venv\Scripts\python.exe'
if (-not (Test-Path $python)) {
    Write-Host 'No virtual environment. Run setup.ps1 to create it.'
    exit 1
}
& (Join-Path $root 'run.ps1')

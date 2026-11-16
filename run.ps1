$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$python = Join-Path $env:LOCALAPPDATA 'FGMappingEngineering\venv\Scripts\python.exe'
if (-not (Test-Path $python)) { throw 'Run setup.ps1 first.' }
$env:PYTHONPATH = Join-Path $root 'src'
$env:PYTHONDONTWRITEBYTECODE = '1'
& $python -B -m fgmapping

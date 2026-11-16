param([string]$Python = 'python')
$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$run = Join-Path $root ('TEST_RESULTS\WINDOWS_' + (Get-Date -Format 'yyyyMMdd_HHmmss'))
New-Item -ItemType Directory -Path $run | Out-Null
$env:PYTHONPATH = (Join-Path $root 'src') + ';' + $root
$env:PYTHONDONTWRITEBYTECODE = '1'
if ($env:QT_QPA_PLATFORM -eq 'offscreen') { throw 'Real Windows Qt platform required; offscreen is not acceptance.' }
Push-Location $root
try {
    & $Python -B tools/run_tests.py 2>&1 | Tee-Object -FilePath (Join-Path $run 'suites.txt')
    if ($LASTEXITCODE -ne 0) { throw 'Tests failed. Preserve results; do not weaken tests.' }
    & $Python -B tools/windows_smoke.py $run 2>&1 | Tee-Object -FilePath (Join-Path $run 'qt_smoke.txt')
    if ($LASTEXITCODE -ne 0) { throw 'Windows Qt smoke failed.' }
    Write-Host "Evidence: $run. Complete manual Windows checks before acceptance."
} finally { Pop-Location }

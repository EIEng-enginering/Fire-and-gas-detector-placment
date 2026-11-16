# Run candidate source
Use a NEW folder. Do not overwrite existing software or use client data.

Windows11, Python3.12:
1. Review setup.ps1, then run `./setup.ps1` under your organisation's permitted PowerShell policy.
2. Run `./run.ps1` (or RUN_LOCAL.ps1). No execution-policy bypass is required or recommended by this pack.
3. Open `examples/SYNTHETIC_WP02_MODULE.fgcase` to inspect the saved geometry, two detectors, equipment/zones and synthetic path-integral history.
4. For new synthetic cases, use Case > New case, then Load synthetic module. Explicit candidate schema2 upgrade prompts first; it is not compatible with the original schema1-only program. Backups are retained.

Tests, from source root:
```
$env:PYTHONPATH = "$PWD\src;$PWD"
$env:PYTHONDONTWRITEBYTECODE = '1'
python -B tools/run_tests.py
```
This runs separate suite processes and writes a new TEST_RESULTS run. Python must have optional reporting packages for report acceptance tests: install `requirements-reports.txt` in the same development venv, or run `setup.ps1 -Reports`. Missing report packages are a failure, not silently skipped.

Linux software verification:
```
PYTHONPATH=src:. PYTHONDONTWRITEBYTECODE=1 python -B tools/run_tests.py
PYTHONPATH=src:. QT_QPA_PLATFORM=offscreen python -B tools/capture_ui.py
PYTHONPATH=src:. python -B tools/benchmark_visibility.py
PYTHONPATH=src:. python -B tools/candidate_mutation_probe.py
```
Offscreen capture is not Windows acceptance. Use a fresh source copy for demo generation (`tools/synthetic_programme_demo.py`) because it refuses to overwrite existing example/exports. Existing generated outputs are supplied in OUTPUT_SAMPLES/SYNTHETIC_STUDY.

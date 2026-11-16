# Run Rev D source
Extract the whole ZIP into a NEW development folder; keep contracts beside src. Target: Windows11, Python3.12, PySide6 6.12.0. This is a source distribution; no built EXE/installer or fully offline dependency wheelhouse is supplied. Once dependencies are installed, the demonstrated application runs offline. Installation may need an authorised package source or your own approved offline wheels.

1. Review setup.ps1, then run `./setup.ps1 -Reports` under permitted organisation policy. Do not bypass execution policy. Reporting dependencies are pinned separately.
2. Run `./run.ps1` (or RUN_LOCAL.ps1).
3. Case > Open case: examples/SYNTHETIC_REV_D_STUDY.fgcase. See USER_GUIDE.md and docs/REV_D_IMPLEMENTATION.md.

From the extracted source root:
```
python -B tools/run_tests.py
```
The driver sets PYTHONPATH, runs unit/integration/acceptance in separate processes and records raw logs. Missing dependencies fail rather than silently skipping tests.

Executed Linux commands:
```
PYTHONPATH=src:. QT_QPA_PLATFORM=offscreen python -B tools/rev_d_workflow.py
PYTHONPATH=src:. python -B tools/rev_d_numerical_benchmarks.py
PYTHONPATH=src:. python -B tools/rev_d_mutations.py
```
The workflow creates unique case/output paths by default. Explicit existing report destinations are refused; do not overwrite prior evidence. It writes three REV_D_WORKFLOW theme screenshots. All parameters in that tool and fixture JSON are synthetic software examples, not study recommendations.

On authorised Windows use docs/REV_D_WINDOWS_CHECKLIST.md and `tools/windows_acceptance.ps1 -Python <development-python.exe>`. Real Qt Windows platform is required. Windows symlink tests may require approved privileges/Developer Mode; do not skip or weaken them. Native Windows acceptance remains pending.

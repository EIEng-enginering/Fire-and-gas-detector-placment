# Run Rev C source
Extract to a NEW local development folder. Use synthetic data only. Windows11/Python3.12/PySide6 6.12.0 is the target; executed evidence here is Linux offscreen.

1. Review setup.ps1 and run `./setup.ps1 -Reports` under your permitted organisation policy. Do not bypass execution policy. Optional report dependencies are pinned separately; the viewer/core do not require them, but report acceptance tests do.
2. Run `./run.ps1` or RUN_LOCAL.ps1.
3. Open examples/SYNTHETIC_REV_C_CONNECTED.fgcase. Read USER_GUIDE.md for filters, forms, paste preview, history, imports and reports.

From a source-root development environment, run `python -B tools/run_tests.py`; it sets PYTHONPATH and runs unit, integration and acceptance separately. All report packages must be present; missing packages fail clearly rather than being silently skipped.

Linux executable evidence commands:
```
PYTHONPATH=src:. PYTHONDONTWRITEBYTECODE=1 python -B tools/run_tests.py
PYTHONPATH=src:. QT_QPA_PLATFORM=offscreen python -B tools/rev_c_workflow.py
PYTHONPATH=src:. QT_QPA_PLATFORM=offscreen python -B tools/virtual_detector_benchmark.py
PYTHONPATH=src:. python -B tools/field_convergence.py
PYTHONPATH=src:. python -B tools/rev_c_mutations.py
```
The workflow tool creates uniquely named output/case files by default and refuses overwriting explicit destinations. The supplied named example/report set is the executed final demonstration. Qt offscreen evidence does not satisfy Windows acceptance.

For Windows use docs/REV_C_WINDOWS_CHECKLIST.md and tools/windows_acceptance.ps1 with the exact development Python executable. That smoke tool requires the real Windows Qt platform. It has not run here. POSIX symlink tests require reviewed Windows-specific prerequisites/equivalents; do not conceal platform failures.

# Run Rev F source
Rev F executed on Windows 11 / Python 3.12.10 / PySide6 6.12.0: `python -B tools/run_tests.py` gives 200/201 unless Developer Mode or symlink privilege is available (then expected 201/201). Run tools/windows_acceptance.ps1 -Python <venv python.exe>; it stops after the suites if any test fails. Optional native Excel read-back: `python -B tools/rev_f_literal_report.py <new folder>` then `powershell -File tools/rev_f_office_check.ps1 -ReportDir <folder> -OutDir <new folder> -Part Excel` under a watchdog. Dense benchmark: `python -B tools/rev_f_dense_benchmark.py`. Mutants: `python -B tools/rev_f_mutations.py`.

# Rev E instructions (inherited)
Extract the FULL ZIP to a NEW local development folder. Keep src and contracts/tools together. Target Windows11/Python3.12/PySide6 6.12.0. This is runnable source, not an EXE/installer; dependencies and their pinned lists are included as requirements, not bundled wheels. Dependency installation may require an authorised package source or your approved offline wheelhouse.

1. Review setup.ps1, then `./setup.ps1 -Reports` under organisation policy. Do not bypass execution policy.
2. Launch `./run.ps1` or RUN_LOCAL.ps1.
3. Open examples/SYNTHETIC_REV_E_STUDY.fgcase. See USER_GUIDE.md for import/revision examples.

From the extracted source root: `python -B tools/run_tests.py`. It sets PYTHONPATH and runs suites separately. Report dependencies must be present; missing dependencies fail clearly.

Executed Linux demonstrations:
```
PYTHONPATH=src:. QT_QPA_PLATFORM=offscreen python -B tools/rev_e_workflow.py
PYTHONPATH=src:. python -B tools/rev_e_benchmarks.py
PYTHONPATH=src:. python -B tools/rev_e_mutations.py
```
The UI workflow creates unique output/case paths by default, refuses explicit existing destinations and writes example CSV/XLSX/revision JSON plus screenshots. Its generated source templates are synthetic examples, not engineering recommendations. Schema3 example includes the earlier schema3 preparation capabilities. New cases require explicit geometry/study schema enablement before those capabilities.

Windows: review docs/REV_E_WINDOWS_CHECKLIST.md, then run tools/windows_acceptance.ps1 with your exact development python.exe. Real Windows Qt and approved symlink prerequisites are required. Offscreen evidence does not satisfy Windows acceptance.

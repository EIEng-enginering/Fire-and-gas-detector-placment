# Rev F full pack
- Rev F additions: services/case.py fsync_file; closing() fixes; tests/integration/test_windows_portability_rev_f.py; tests/acceptance/test_dense_scene_rev_f.py; tools/rev_f_mutations.py, rev_f_dense_benchmark.py, rev_f_literal_report.py, rev_f_office_check.ps1; docs/REV_F_*.md; docs/REV_E_BASELINE (Rev E root docs); TEST_RESULTS/REV_F_* (box baseline, Windows evidence, mutants, benchmarks, failures, final summary); ORIGINAL_ARCHIVES/REV_E_PREDECESSOR_REFERENCE.json.

# Rev E full pack (inherited description)
- src/fgmapping: complete runnable Python/PySide6 source, prior features and new preparation/reconciliation/spatial/report code.
- contracts: original owner manifest and schema1, candidate schemas2/3; no new migration.
- requirements*.txt, pyproject.toml, setup.ps1, run.ps1, RUN_LOCAL.ps1: pinned dependency specifications and launch/setup source. Dependencies are not bundled wheels; no EXE/installer.
- tests:190 tests in separate unit/integration/acceptance suites.
- tools: unchanged earlier tools plus rev_e_workflow.py, rev_e_benchmarks.py, rev_e_mutations.py, test/pack/Windows drivers.
- examples: synthetic source templates CSV/XLSX, explicit geometry revision JSON, saved SYNTHETIC_REV_E_STUDY.fgcase and earlier fixtures.
- OUTPUT_SAMPLES/REV_E_STUDY: final JSON/Excel/Word/PDF/ZIP reports; exact source assets and full values in normalized JSON.
- screenshots/REV_E_BULK_PREVIEW.png, REV_E_REVISION_PREVIEW.png, REV_E_WORKFLOW_{grey,dark,light}.png: actual executed Qt Linux offscreen windows.
- TEST_RESULTS: baseline/intermediate/final/fresh logs, mutations, benchmarks, report renders and final summary index.
- docs: unchanged owner standards/specification/decisions/risks, new Rev E notes, prior notes and preserved root-doc baselines.
- ORIGINAL_ARCHIVES: exact WP01/takeover and Rev B/C/D ZIPs.
- PROJECT_STATE.md/NEXT_WORK_PROMPT.txt: exact continuation checkpoint.
- SOURCE_FILES.json, PACK_SCAN.json, SHA256SUMS.txt: source change list, pack scan and all-file hashes.

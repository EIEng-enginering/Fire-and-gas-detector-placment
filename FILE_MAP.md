# Rev G additions
- **Schema and contracts:** contracts/migrations/0004_coverage.sql (schema 4).
- **Domain:** src/fgmapping/domain/detector_library.py, coverage_setup.py.
- **Engine:** src/fgmapping/engine/coverage.py (FG-FLAME-GEO/1.0, FG-GAS-GEO/1.0) and scenario_coverage.py (FG-SCENARIO/1.0, FG-OPTIONS/1.0). optimisation.py gains base_votes.
- **Services:** src/fgmapping/services/coverage.py, scenario_coverage.py, coverage_report.py and heatmap.py. Coverage-aware changes in basis, findings, reporting, workspace and preparation.
- **UI:** src/fgmapping/ui/coverage_dialogs.py (Coverage menu); viewer.py heatmap and FOV overlay.
- **Examples:**
  - examples/library/STARTER_DETECTOR_LIBRARY_EXAMPLE_VALUES.csv/.xlsx
  - examples/wellhead_coverage/ (case, summary, scenarios/options JSON, full report with figures and manifest)
- **Tools:**
  - tools/build_starter_library.py
  - tools/build_wellhead_coverage_example.py
  - tools/capture_wellhead_coverage_app.py
- **Tests:**
  - tests/unit/test_coverage_engine.py
  - tests/unit/test_scenario_coverage.py
  - tests/integration/test_coverage_rev_g.py
  - tests/integration/test_wellhead_coverage_rev_g.py
- **Screenshots:** screenshots/REV_G/ (box offscreen and WINDOWS_REAL).
- **Test results:** TEST_RESULTS/REV_G/ (box and Windows suite evidence).
- **Docs:** docs/REV_G_COVERAGE_METHOD.md, docs/REV_G_TRACEABILITY.md, the USER_GUIDE coverage section, and the docs/EXAMPLE_WELLHEAD_MODULE.md coverage section.

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

- examples/SYNTHETIC_WELLHEAD_MODULE.fgcase plus the examples/wellhead/ inputs (geometry JSON, register CSV/XLSX, zones, basis, build summary): SYNTHETIC 3D wellhead module example. See docs/EXAMPLE_WELLHEAD_MODULE.md.
- tools/build_wellhead_example.py (generator), tools/render_wellhead_preview.py (matplotlib preview, tool-only), tools/capture_wellhead_app.py (real-app screenshots).
- screenshots/WELLHEAD_MODULE_*.png are matplotlib previews. screenshots/WELLHEAD_APP_LINUX_OFFSCREEN_*.png and WELLHEAD_APP_WINDOWS_*.png are executed application windows.
- TEST_RESULTS/WELLHEAD_EXAMPLE/: box and Windows suite evidence for the example, including the preserved first Windows failure.

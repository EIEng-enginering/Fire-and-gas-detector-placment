# Project state — Rev G (coverage) checkpoint
18 November 2026 (AWST, UTC+8). v0.7.0a1. Engineer-reviewed results - not independently certified.

## Rev G status (owner approval 18 Nov 2026 09:58 AWST: "I as the owner approved evething and build everthing that make the full program")
Q1–Q10 and F01–F10 are APPROVED (docs/DECISIONS_REV_A.md). The synthetic-only, calculation-blocked and no-Git rules are lifted. Git commit and push to main is authorised; force-push is not.

<!-- REV_G_MILESTONES -->
- **M1 Detector library: DONE.**
  - Library entries use contract fg-detector-library/1.
  - Library import from CSV/XLSX.
  - Explicit per-detector assignment, as required by F03.
  - A starter library of EXAMPLE VALUES in examples/library.
  - UI: Coverage > Import library / Detector library / Assign.
- **M2 Flame geographic coverage: DONE.** Method FG-FLAME-GEO/1.0, schema 4 (coverage_run).
  - The readiness gate reports READY or BLOCKED per zone.
  - Each run is stored with its input hash.
  - Staleness is tracked and convergence is checked.
- **M3 Viewer and results: DONE.**
  - Heatmap overlay of a stored run in the 3D viewer: plan slice, colour by votes, legend with label.
  - FOV wireframes from the library contour; a per-zone results table; coverage findings (stale, below target, convergence).
  - Offscreen UI test (tests/integration/test_wellhead_coverage_rev_g.py).
- **M4 Geographic gas: DONE.** FG-GAS-GEO/1.0: point detectors and open-path detectors (receivers from EQUIPMENT records) against a user design cloud. Applied to the wellhead gas zones.
- M5 Scenario coverage and optimisation: NOT STARTED.
- **M6 Reports: DONE.**
  - services/coverage_report.py writes JSON/XLSX/DOCX/PDF plus heatmap PNGs (services/heatmap.py) and a MANIFEST of SHA-256 hashes.
  - Every output is labelled 'Engineer-reviewed results - not independently certified' and carries an EXAMPLE warning when example data are used.
  - Reports go to a new folder only; nothing is overwritten.
- **Wellhead example: DONE** (examples/wellhead_coverage, 0.5 m grid, refinement check). It uses EXAMPLE library values and EXAMPLE targets, so the results are illustrative only.
<!-- /REV_G_MILESTONES -->

Method: docs/REV_G_COVERAGE_METHOD.md. Deviations: DEVIATIONS.md G1–G5.

---
# (Previous) Rev F checkpoint
16 November 2026 (AWST, UTC+8). v0.6.0a1. DEVELOPMENT BUILD / UNVERIFIED.

## Current implementation
Rev F is the first native Windows execution and Windows portability revision. Starting from the preserved Rev E ZIP (SHA256 7d56b4b2…cdf732e8), all 753 Rev E hashes verified on the Linux box and on Windows, and the untouched 190-test suite was rerun on both before edits: Linux 190/190 PASS; native Windows 11 / Python 3.12.10 / PySide6 6.12.0 **98 of 190 ERROR** (fsync on read-only descriptors; unclosed SQLite connections locking files). Rev E had never actually run on Windows.

Fixes: write-capable `fsync_file()` for all durability flushes; `contextlib.closing` for every SQLite connection opened with a context manager in src, three inherited test files and the pack builder. New: 10 Windows-portability regression tests (Windows semantics emulated on POSIX, native on Windows), 3 deliberate mutants (caught on Linux and Windows), dense-lattice broadphase benchmark against the independent oracle (+1 acceptance test), native Excel literal-text read-back tooling. Engine/geometry/calculation code, migrations, owner manifest and tolerances unchanged.

Rev F baseline suite (before the wellhead example): 201 tests (87 unit / 105 integration / 9 acceptance). Linux: 201/201 PASS. Windows: 200/201 — `test_symlink_alias_fenced` fails with WinError 1314 because this PC has no Developer Mode/symlink privilege; the test was not altered or skipped. Real-Qt (`windows` platform) smoke and the Rev E integrated Qt workflow passed on Windows; native Excel showed literal `=` text and zero formulas. Word COM read-back hung and was not completed. Manual Windows items (keyboard, DPI/multi-monitor, human visual Office/PDF review, human cancellation/file-lock scenarios) were not performed. See TEST_RESULTS/REV_F_FINAL_SUMMARY.json and docs/REV_F_WINDOWS_CHECKLIST.md.

## Addendum: SYNTHETIC wellhead module example
`examples/SYNTHETIC_WELLHEAD_MODULE.fgcase` (docs/EXAMPLE_WELLHEAD_MODULE.md) is an illustrative 3D offshore wellhead module. It contains:
- 116 box components; scene sha256 ef65fc6f…53c2
- 23 CANDIDATE detectors
- 17 equipment records
- 3 fire zones and 3 gas zones
- a basis that is NOT SUPPLIED throughout

It was built through the services by tools/build_wellhead_example.py. Readiness input is BLOCKED and engineering calculation is BLOCKED. No mounts, performance data or coverage are included.

Suite: 206 tests (87 unit / 110 integration / 9 acceptance).
- Linux: 206/206 PASS.
- Windows: the first run had 2 problems. The new byte-compare test failed on CRLF generator output; that run is preserved. The generator was then fixed to write LF.
- Windows rerun: 205/206. The only failure is the known `test_symlink_alias_fenced` (WinError 1314, no symlink privilege); that test is unaltered.
- The real Windows Qt app opened the example and screenshots were captured.

## Logical stopping point
Windows portability defects found by the first native run are fixed and regression-guarded. Engineering calculation stays BLOCKED. Not WP02–WP12 acceptance, qualification or release.

## Exact next action
Verify SHA256SUMS.txt; rerun tools/run_tests.py unchanged on Linux and Windows. On Windows, enable Developer Mode (or grant SeCreateSymbolicLinkPrivilege) under organisation policy and rerun tools/windows_acceptance.ps1 to clear the symlink prerequisite without changing the test. Diagnose the Word COM hang with Word visible (or inspect Study.docx/PDF manually in Word/Acrobat). Perform the manual checklist items in docs/REV_F_WINDOWS_CHECKLIST.md. Review register/component column truncation seen in real-Qt screenshots. Then the independent follow-on: richer preparation templates/zone import and source metadata, explicit anchor redeclaration review, report histories/dependency graph, parser hardening. Review Q1–Q10/F01–F10 before treating any as approved.

Engineering response/coverage/optimisation acceptance, real manufacturer data, live AI/integrations, independent WP12 qualification and release remain blocked pending legitimate method/data/permissions and owner review. Git commit/push of this revision was separately authorised by the owner; no publication, release, client processing or engineering sign-off is authorised.

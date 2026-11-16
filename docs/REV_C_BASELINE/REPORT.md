# Development report Rev C
16 November 2026. v0.3.0a1. DEVELOPMENT BUILD / UNVERIFIED.

No repository/branch/base commit. No commits, merges, pushes, public deployment, live AI, paid calls, client processing or engineering release.

Rev B baseline was verified before edits: 272 file hashes and 85 unchanged tests (53 unit/30 integration/2 acceptance). Original WP01 protection tests remain unchanged. Final fresh-extraction suite: 65 unit + 54 integration + 4 acceptance = 123/123, zero failures/skips. Full evidence is in TEST_RESULTS/REV_C_FINAL_SUMMARY.json. Tests run in separate processes on Linux Python3.12.14/PySide6 6.12.0; Windows NOT RUN.

DONE AND VERIFIED IN THIS ENVIRONMENT: connected actual Qt form/edit/filter/copy/paste/undo workflow; virtual detector/equipment/zone grids; detector removal and references; marker/register atomic edits; import append/replace/source retention; case cross-runtime native lock, live legacy lock refusal, process-kill and injected save failures; fingerprints; concentration/time analytic and convergence tests; asynchronous report completion/cancellation; all-format record/finding QA; actual three-theme screenshots; Word/PDF rendering and visual inspection.

The actual detector grid was exercised with 10,000 cached rows. Measured first-paint/filter timings are in REV_C_10000_DETECTORS_FINAL.json; they are Linux offscreen observations, not Windows performance guarantees. Two deliberately broken new implementations (writer fence and undo state) were caught; previous numerical oracles remain intact. The piecewise field benchmark approaches its independent 8.71 ppm*m reference as documented.

Named source additions: services/workspace.py, file_lock.py, paste.py, import_review.py, findings.py, report_job.py; ui/worksheet.py; domain/pose.py; engine/concentration.py; focused tests, actual workflow/benchmark/mutation and Windows-gated tools. Extended existing case, register UI, reporting and calculation services. Schema2 itself is unchanged.

DONE BUT NOT VERIFIED ON WINDOWS: native Windows locks, launch/setup scripts, real Qt/DPI/clipboard/rendering, Windows crash cleanup and supplied acceptance driver. Automatic Windows stale-PID cleanup remains disabled conservatively.

NOT DONE: complete WP02–WP12 acceptance, qualified detector response/coverage, robust industrial CAD/STEP/self-intersections, full production reporting/UX/history, live optional integrations, independent engineering qualification/release. All owner decisions remain proposed. See current implementation/traceability notes and OPEN_ISSUES for precise limits.

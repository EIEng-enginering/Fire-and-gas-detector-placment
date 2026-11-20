# Changelog
16 November 2026 - Rev A / v0.1.0a1: Created isolated development foundation, engineering design/spec, risk register, owner decision register, first source and tests, synthetic example and evidence pack. No updates to other applications. No Git actions.

16 November 2026 - Rev B / v0.2.0a1: Preserved/retested WP01; candidate geometry/schema/viewer/import; register and detector-edit services; independent mesh oracle/BVH/visibility; synthetic gas/scenario/layout exercises; five-format register reporting and QA; offline replay and proposal contracts; no engineering qualification or Git actions. See docs/IMPLEMENTATION_REV_B.md for precise scope and defects.

16 November 2026 - Rev C / v0.3.0a1: Connected virtual register workflow, typed forms, atomic workspace history/paste/removal, reviewed append/replace import, evidence/findings, zone/orientation annotations, cancellable report UI with figure, synthetic exercise UI, native writer/save recovery hardening, implementation fingerprints and concentration/time field benchmarks. Original 85 tests preserved; full/fresh results indexed in REV_C_FINAL_SUMMARY.json. Windows and engineering qualification pending.

# Rev D — 0.4.0a1
Six further executable areas: component mounting, geometric target inspection, structured basis/readiness, report schedules/comparison/embedded PDF fonts, restore-as-new and Windows probe preparation, synthetic performance preparation/link/draft review. Explicit candidate schema3.168 tests vs123 untouched baseline; actual Qt workflow and all-format exports. Windows/engineering qualification remain pending.

# Rev E —0.5.0a1
Bulk CSV/XLSX preparation, explicit geometry revision reconciliation, scene broadphase and independent oracles, source/mount review reporting and literal Excel strings, six recovery fault tests.190 tests; actual Qt workflow; full checkpoint pack. No migration/dependency change or engineering acceptance.

# Rev F — 0.6.0a1
First native Windows 11 execution. Untouched Rev E suite: 98/190 errors on Windows. Fixed read-only-descriptor fsync (new fsync_file) and unclosed SQLite connections (contextlib.closing in src, three inherited tests and pack builder). Added Windows-portability regression tests, Rev F mutants, dense-lattice independent benchmark/test and native Excel literal read-back tooling. 201 tests: Linux 201/201, Windows 200/201 (symlink privilege). No migration/dependency/engine change or engineering acceptance.

# Rev F addendum: SYNTHETIC 3D wellhead module example
Adds a reproducible SYNTHETIC offshore wellhead module example study (WHM-01). It is about 30×20 m with a cellar deck (0.0), a wellhead/mezzanine grating (+4.5) and an upper deck (+9.0). Contents:
- 8 well slots with wellhead, tree, valve, choke and flowline envelopes
- production/test manifold and headers
- wireline/intervention area
- north and west blast walls
- escape-route markers
- 23 candidate detectors: 8 FLAME, 12 POINT_GAS, 3 OPEN_PATH
- 17 equipment records
- 3 fire zones and 3 gas zones

It is built only through the app's service paths (`tools/build_wellhead_example.py`). It ships with matplotlib previews and real-app screenshots on Linux offscreen and Windows `windows` Qt. Documentation is in docs/EXAMPLE_WELLHEAD_MODULE.md. A new integration test, tests/integration/test_wellhead_example.py (5 tests), brings the suite to 206.

The first Windows run failed honestly on CRLF text output from the generator. The generator now writes LF bytes, and `.gitattributes` pins the example inputs to `-text`. Readiness input is BLOCKED and engineering calculation stays BLOCKED.

# Rev G — 0.7.0a1 (owner-approved coverage program, 18 Nov 2026)
<!-- REV_G_CHANGELOG -->
- **M1/M2.**
  - Schema 4 (migration 0004_coverage.sql).
  - Detector library contract, with CSV/XLSX import, immutable-by-ID entries and an EXAMPLE starter library.
  - Explicit library assignment per detector, including the open-path receiver.
  - Per-zone coverage setup contract.
  - Flame geographic coverage engine: FOV + contour + line of sight against the 3D geometry, extended cylinder target, weighted voting fractions, exclusions, convergence and sensitivity.
  - Geographic gas engine: sphere/ellipsoid design cloud, point detector and open-path LEL·m.
  - The readiness gate reports READY when inputs are complete.
  - Runs are stored with their input hash and staleness is tracked.
  - New tests: 22 unit (known-answer) and 6 integration.
- **M3/M4/M6 and the wellhead example.**
  - Viewer heatmap and FOV overlay, results table, and coverage findings.
  - Coverage report in JSON/XLSX/DOCX/PDF with heatmap figures and a hash manifest.
  - The normalised snapshot lists coverage runs.
  - Implementation hashes no longer depend on line endings (CRLF and LF give the same hash).
  - New tools: tools/build_wellhead_coverage_example.py and tools/capture_wellhead_coverage_app.py.
  - New test module test_wellhead_coverage_rev_g.py (7 tests).
- **M5.**
  - engine/scenario_coverage.py and services/scenario_coverage.py: scenario sets and layout options stored as reproducible runs, with staleness.
  - optimisation.enumerate_layouts gains the optional base_votes argument; its default behaviour is unchanged.
  - coverage.runs() now returns only zone runs.
  - The report includes the studies.
  - Docs: REV_G_TRACEABILITY.md, USER_GUIDE coverage section, method §4a–4c, wellhead example section.
  - New tests: test_scenario_coverage.py (6) and WellheadStudies (3).
<!-- /REV_G_CHANGELOG -->

# Rev H — 0.7.0a1 + review fixes (20 Nov 2026)
Fixes for independent review findings F01–F25 (docs/FIX_DISPOSITION_REV_H.md):
- Exact free cell measure (box union) and bounded mesh measure; winding-number membership; mesh-based exclusions.
- The detector frame matches the mount rotation. The standoff is limited to the detector's own mount. The eps-consistent broadphase is now used.
- The GRID AGREEMENT vocabulary replaces CONVERGED.
- Transitive implementation fingerprints, a sensitivity flag in the envelope, and per-run scene snapshots for historical figures.
- A lifecycle ledger: COMPUTED - UNREVIEWED / ENGINEER REVIEWED / INDEPENDENTLY VERIFIED / REVIEW INVALIDATED.
- A central compatibility gate; safe export paths with staged publish; literal spreadsheet text; import resource guards; finite validation.
- The FOV outline now comes from the response predicate. Clipped-cell heatmaps.
- Landscape report layouts with tblGrid widths; local Decimal contexts.
- Options now run at the zone-run grid in a worker with cancellation.

New tests: 46 (25 unit, 21 integration). Updated expectations, documented: CONVERGED → GRID AGREEMENT; method version 1.1; label text. The wellhead example was regenerated. No migration change. No git actions.

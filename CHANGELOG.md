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

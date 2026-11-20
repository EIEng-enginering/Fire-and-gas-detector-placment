# REVIEW README — Fire & Gas Mapping Engineering System, Rev G (v0.7.0a1)

This file is for an external code or AI reviewer. It is the entry point to this review pack. Start here, then read `PROJECT_STATE.md`, `docs/REV_G_COVERAGE_METHOD.md` and `docs/REV_G_TRACEABILITY.md`.

All results are **"Engineer-reviewed results – not independently certified"**. No conformity with any standard (ISA-TR84.00.07, DNV-RP-A102, ISO 13702) is claimed. The detector library and the wellhead example use **EXAMPLE VALUES** and must be replaced with verified manufacturer data before any project use.

## 1. What the program is
- A desktop application in Python 3.12 and PySide6 for placing fire and gas detectors and computing their coverage on 3D facility geometry. Cases are SQLite `.fgcase` files with an append-only audit log, undo/redo, backups and recovery.
- Pure-Python geometry engine (no numpy), with a mesh BVH, segment/triangle line of sight and an AABB broadphase.
- **Rev G** adds:
  - an explicit detector library;
  - per-zone coverage setup and a readiness gate;
  - flame and geographic gas coverage engines;
  - a 3D heatmap and field-of-view overlay;
  - scenario coverage and candidate layout options;
  - JSON/XLSX/DOCX/PDF coverage reports.
- Schema 4 (`contracts/migrations/0004_coverage.sql`).
- Owner approval of the design decisions is recorded in `docs/DECISIONS_REV_A.md`.

## 2. Layout map
| Path | Content |
|---|---|
| `src/fgmapping/domain/` | Contracts and validation: `detector_library.py`, `coverage_setup.py`, `scene.py`, `pose.py`, `study_basis.py` |
| `src/fgmapping/engine/` | Calculation code, Qt-free: `coverage.py`, `scenario_coverage.py`, `optimisation.py`, `scenarios.py`, `mesh_visibility.py`, `spatial.py`, `geometry.py`, `detection.py` (gate entry points) |
| `src/fgmapping/services/` | Case persistence and workflows: `coverage.py` (gate, runs, hashes), `scenario_coverage.py`, `coverage_report.py`, `heatmap.py`, `workspace.py` (undoable edits, STALE marking), `basis.py` (readiness), `findings.py`, `reporting.py` |
| `src/fgmapping/ui/` | Qt UI: `main.py`, `coverage_dialogs.py` (Coverage menu), `viewer.py` (3D viewer, heatmap and FOV painting) |
| `contracts/` | Owner manifest, schemas and migrations 0001–0004, `candidate_manifest.json` (migration hashes) |
| `tests/unit`, `tests/integration`, `tests/acceptance` | 250 tests. Rev G tests: `unit/test_coverage_engine.py`, `unit/test_scenario_coverage.py`, `integration/test_coverage_rev_g.py`, `integration/test_wellhead_coverage_rev_g.py` |
| `tools/` | `run_tests.py`, example builders (`build_wellhead_example.py`, `build_wellhead_coverage_example.py`, `build_starter_library.py`), capture scripts, earlier benchmarks and mutation tools |
| `examples/` | `SYNTHETIC_WELLHEAD_MODULE.fgcase` (base); `wellhead_coverage/` (coverage case, summary, scenarios/options JSON, full `WELLHEAD_COVERAGE_REPORT/` with pdf/docx/xlsx/json, figures and MANIFEST); `library/` (EXAMPLE starter library) |
| `docs/` | Master specification, decisions (APPROVED), risk register, `REV_G_COVERAGE_METHOD.md`, `REV_G_TRACEABILITY.md`, `EXAMPLE_WELLHEAD_MODULE.md`, earlier revision notes |
| `TEST_RESULTS/` | Suite logs. `TEST_RESULTS/REV_G/` holds the Rev G box (Linux) and Windows evidence; older folders are earlier revisions |
| `screenshots/REV_G/` | `BOX_OFFSCREEN_*` (Linux offscreen Qt) and `WINDOWS_REAL/` (real Windows Qt platform) |
| Root docs | `PROJECT_STATE.md`, `CHANGELOG.md`, `DEVIATIONS.md`, `USER_GUIDE.md`, `FILE_MAP.md`, `NEXT_WORK_PROMPT.txt`, `HOW_TO_RUN.md` |
| `GIT_INFO.txt`, `SHA256SUMS.txt` | Commit, branch and remote, and hashes of every file in this pack |

## 3. Install and run
```
python3.12 -m venv venv && venv/bin/pip install -r requirements-lock.txt -r requirements-reports.txt   # PySide6 6.12.0, openpyxl, python-docx, reportlab, pypdf
python -B tools/run_tests.py                       # runs unit / integration / acceptance separately; evidence goes to TEST_RESULTS/<utc>/
QT_QPA_PLATFORM=offscreen python -B tools/run_tests.py   # headless Linux
PYTHONPATH=src python -B -m fgmapping              # launch the UI (Windows: run.ps1)
python tools/build_wellhead_coverage_example.py NEW_FOLDER --grid 0.5 --refine 2   # rebuild the example (about 2.5 min)
```
Recorded results:
- Linux (box): 250/250 pass.
- Windows 11: 249/250. The one failure is `test_symlink_alias_fenced`, which fails with WinError 1314 because the PC has no symlink privilege. That test is unaltered.

## 4. Where the coverage engine lives
- **Flame, FG-FLAME-GEO/1.0** (`engine/coverage.py`):
  - `detector_frame` and `flame_geometry_ok` (FOV half-angles plus contour range);
  - `Obstructions` (LOS, inside tests);
  - `discretise` (clipped, volume-weighted cells);
  - `target_points` (point or cylinder target);
  - `_flame_votes`, `_fractions`;
  - `zone_coverage` (convergence, sensitivity).
- **Gas, FG-GAS-GEO/1.0** (`engine/coverage.py`): `_gas_votes`, `chord_length` (exact ellipsoid chord), `_ellipsoid_semi`.
- **Gate, envelope and hashes** (`services/coverage.py`): `gather`, `coverage_readiness`, `prepare_run`, `compute`, `store_run`, `run_currency`. The engine entry points `engine/detection.py: engineering_flame_coverage` and `engineering_gas_coverage` refuse incomplete inputs.
- **Scenarios, FG-SCENARIO/1.0** (`engine/scenario_coverage.py: scenario_coverage`): aggregated in exact Decimal by `engine/scenarios.aggregate`.
- **Options, FG-OPTIONS/1.0** (`engine/scenario_coverage.py: layout_options`): uses `engine/optimisation.enumerate_layouts` with `base_votes`.
- **Study services:** `services/scenario_coverage.py`. This includes the before/after baseline layout fingerprint check.
- **Reports:** `services/coverage_report.py` and `services/heatmap.py` (PIL plan slices).

## 5. Methods (summary; full text in `docs/REV_G_COVERAGE_METHOD.md`)
- **FG-FLAME-GEO/1.0:**
  1. The zone box is split at the user grid spacing into VOLUME cells or SLICES. Each cell is weighted by its actual clipped volume or area.
  2. Cells inside obstructing solids, or inside basis-excluded components, are excluded and reported.
  3. At each cell a target is placed: a point, or a cylinder of rings × levels.
  4. A detector votes when enough of the target points meet all three tests, with the required fraction set by `min_visible_fraction`:
     - inside the horizontal and vertical FOV half-angles;
     - within the contour range at that off-axis angle (linear interpolation, zero beyond the table), multiplied by sqrt(Q_target/Q_rated) only if INVERSE_SQUARE is explicitly chosen;
     - with an unobstructed segment from detector to target, applying the standoff. Coplanar or indeterminate rays count as blocked.
  5. The kooN fraction is the weight of cells with at least k votes divided by the eligible weight.
  6. Convergence compares against the grid refined by a factor of 2 or 3 within a user tolerance. Results are deterministic.
- **FG-GAS-GEO/1.0:** a geographic design cloud (sphere or ellipsoid of user size and %LEL) is centred at each cell.
  - **Point detector:** votes if it is inside the cloud and the cloud %LEL is at least its alarm threshold.
  - **Open path:** votes if (%LEL/100) × chord length of the beam inside the cloud is at least its LEL·m threshold. A beam that is obstructed, or whose length is outside the library path range, makes the detector inoperative and raises a BLOCKING finding.
  - This is not a dispersion calculation.
- **Run storage:** every run stores the full input envelope: setup, library entries, detector poses, receivers, scene hash, exclusions, and SHA-256 of the implementation files (line-ending neutral). It also stores the input hash, method version, result and per-cell samples. Currency is decided by recomputing the hash; any edit makes the run STALE.

## 6. Wellhead example results (EXAMPLE library values and EXAMPLE targets — illustrative only, not for design)

Settings: 0.5 m VOLUME grid with refinement 2; 2ooN voting; flame target 450 kW methane point; gas cloud a 5 m sphere at 100 %LEL.

| Zone | Method | Eligible m³ | 0ooN | 1ooN | 2ooN | 1ooN vs 0.90 | 2ooN vs 0.80 | Convergence |
|---|---|---|---|---|---|---|---|---|
| FZ-MANIFOLD | FG-FLAME-GEO/1.0 | 271.7 | 0.7 % | 99.3 % | 79.2 % | MEETS USER TARGET | BELOW USER TARGET | CONVERGED |
| FZ-WELLBAY | FG-FLAME-GEO/1.0 | 1338.6 | 6.5 % | 93.5 % | 85.9 % | MEETS USER TARGET | MEETS USER TARGET | CONVERGED |
| FZ-WIRELINE | FG-FLAME-GEO/1.0 | 123.1 | 0.2 % | 99.8 % | 86.5 % | MEETS USER TARGET | MEETS USER TARGET | CONVERGED |
| GZ-MANIFOLD | FG-GAS-GEO/1.0 | 271.7 | 70.4 % | 29.6 % | 0.6 % | BELOW USER TARGET | BELOW USER TARGET | CONVERGED |
| GZ-MODULE | FG-GAS-GEO/1.0 | 5023.6 | 84.8 % | 15.2 % | 2.0 % | BELOW USER TARGET | BELOW USER TARGET | CONVERGED |
| GZ-WELLBAY | FG-GAS-GEO/1.0 | 1338.6 | 63.8 % | 36.2 % | 4.7 % | BELOW USER TARGET | BELOW USER TARGET | CONVERGED |

- **Scenario set** (19 EXAMPLE scenarios): frequency-weighted detected fraction 0.242.
- **Layout options, FZ-MANIFOLD 2ooN:** the existing layout gives 0.753. Adding CAND-MF-1 gives 0.906, and adding CAND-MF-1 plus CAND-MF-3 gives 0.974. These are proposals only.
- **Finding:** the GD-OP-01 and GD-OP-02 beams are obstructed by the stair towers ST-MZ and ST-UD, so those two detectors are inoperative.

## 7. Known limitations and open items
- Scene and evidence data are still SYNTHETIC-only; there is no PROJECT data class yet. All geometry is closed triangle meshes, and the example uses box envelopes only.
- Detector field of view:
  - a single off-axis contour, with no separate horizontal and vertical tables;
  - no atmospheric attenuation, contamination or false-alarm modelling, and no response time;
  - gratings obstruct as solids unless they are declared non-obstructing.
- Gas is a geographic design cloud only; there is no dispersion (CE-06) and no time dependence.
- Scenarios are single points with user frequencies. There is no risk weighting or uncertainty, and no SIL or availability credit.
- The layout options search is exhaustive and limited to 16 candidates.
- Performance: the engine is pure Python on one thread, taking about 2.5 min for the whole wellhead example at 0.5 m with refinement.
- Manual Windows checks (DPI, multi-monitor, human review of the Office and PDF output) are not done. The symlink-privilege test fails on the PC.
- See also `DEVIATIONS.md` (G1–G8), `OPEN_ISSUES.md` and `docs/DESIGN_ISSUES_AND_RISK_REGISTER_REV_A.md`.

## 8. Specific questions for the reviewer
1. **Geometry and line of sight:**
   - Is `mesh_visibility` segment/triangle intersection correct, including grazing, edge and vertex hits and the coplanar ValueError path?
   - Is `Obstructions.inside` correct? It uses an AABB shortcut for boxes and ray parity with a skewed ray otherwise; are non-box meshes handled?
   - Are the BVH and broadphase conservative, so that no blocking triangle is ever missed?
2. **Detector frame and FOV:**
   - Check the azimuth convention (X toward Y) and the elevation and roll handling in `detector_frame`.
   - Is the horizontal/vertical half-angle decomposition in `flame_geometry_ok` correct, including near ±90° elevation?
   - Is the off-axis angle used for the contour the true angle from the boresight?
3. **Voting maths:**
   - Is `_fractions` right that kooN means at least k votes, the sum over cells is weighted, and 0ooN + 1ooN = 1?
   - Is the required_voting_fraction selection correct?
   - Are per-detector fractions computed correctly?
4. **Discretisation and convergence:**
   - Is the clipped cell weighting at zone edges exact?
   - Is the convergence criterion (absolute change in each fraction at refinement 2 or 3 against the tolerance) meaningful? Should it be Richardson-type extrapolation?
   - Is excluding cells by their centre point (inside a solid) acceptable, or should it be by partial volume?
5. **Fire target:**
   - Is the standoff application sound?
   - Is cylinder sampling with `min_visible_fraction` sound?
   - Is the reach pre-filter `reach + extent` conservative?
   - Is the INVERSE_SQUARE scaling sqrt(Q/Q_rated) applied in the right direction?
6. **Gas open-path integration:**
   - Is `chord_length` correct for every case: segment inside, partly inside, tangent, or a zero-length beam?
   - Is (%LEL/100) × chord the right LEL·m measure for a uniform cloud?
   - Are the threshold epsilon and the treatment of an obstructed beam (detector inoperative for the whole zone) appropriate?
7. **Reproducibility and staleness:** does the input envelope capture every input that affects the result? Could a run be shown as CURRENT when the inputs actually changed?
8. **Gate and honesty:**
   - Can any path produce coverage without an explicit library entry?
   - Is any certification claimed anywhere?
   - Are the EXAMPLE warnings present in every output (UI, report, figures)?
9. **Scenarios and options:**
   - Is the Decimal aggregation exact?
   - Is the Pareto filter correct?
   - Are existing votes credited correctly in `base_votes`?
   - Is it impossible for the baseline layout to be mutated?
10. **Test coverage gaps:** what important cases are untested? Examples: non-box meshes in the inside test, rotated frames, ellipsoid open path at oblique angles, slices plus cylinder targets, cancellation mid-run, very large zones, UI threading.
11. **Code quality:** check error handling, any thread-safety issue in the background run (`ui/coverage_dialogs.run_coverage`), and SQL or JSON contract validation gaps.

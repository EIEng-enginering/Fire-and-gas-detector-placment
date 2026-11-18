# Rev G coverage method (FG-FLAME-GEO/1.0, FG-GAS-GEO/1.0)

**Engineer-reviewed results – not independently certified.**

The results depend entirely on the detector data the user enters, the zones, the target fire or design cloud, and the geometry. The example library values shipped with the program must be replaced by verified manufacturer data before any project use. No independent certification has been carried out.

The owner approved this work on 18 Nov 2026 (docs/DECISIONS_REV_A.md). Code locations:
- **Engine:** `src/fgmapping/engine/coverage.py` (pure Python, deterministic, no Qt)
- **Entry points:** `engine/detection.py` (`engineering_flame_coverage` and `engineering_gas_coverage`)
- **Services:** `services/coverage.py`
- **Contracts:** `domain/detector_library.py` (fg-detector-library/1) and `domain/coverage_setup.py` (fg-coverage-setup/1)
- **Schema:** `contracts/migrations/0004_coverage.sql` (schema 4)

## 1. Inputs (all supplied by the user; nothing is defaulted)

| Input | Where | Gate |
|---|---|---|
| Facility geometry (closed meshes, SI metres) | geometry scene | `FACILITY_GEOMETRY` |
| Fire/gas zone (AABB) | FIRE_ZONE / GAS_ZONE records | `NO_COVERAGE_SETUP` |
| Study basis (exclusions, references) | study_basis | `STUDY_BASIS` |
| Zone setup | coverage_setup (fg-coverage-setup/1) | `CRITERION_REFERENCE` |
| Library entry per detector | detector_library plus explicit detector_library_assignment | `LIBRARY_ENTRY_NOT_ASSIGNED`, `LIBRARY_TYPE_MISMATCH` |
| Fuel and fire size consistency | library vs setup | `FUEL_MISMATCH`, `FIRE_SIZE_MISMATCH` |
| Detector orientation | detector_details | `ORIENTATION` |
| Open-path receiver | assignment (record ID or XYZ) | `RECEIVER` |

The zone setup covers the grid, VOLUME or SLICES mode, voting, the per-zone user targets, the convergence check, and the target fire or design cloud.

When fire size differs from the library's rated fire, the user must explicitly select `INVERSE_SQUARE` scaling, which applies range × √(Q_target/Q_rated). Otherwise the run is blocked.

`readiness()` reports `engineering_calculation_status = READY` only when every configured zone is READY. A schema-3 case stays BLOCKED until it is upgraded to schema 4.

## 2. Flame geographic coverage (CE-03/CE-04)

1. **Discretisation.** The zone AABB is cut into cells of the grid spacing h. In VOLUME mode the cells are 3D; in SLICES mode they are plan cells at user elevations.
   - Boundary cells are clipped to the zone and weighted by their actual clipped volume (m³) or area (m²), not by point count.
2. **Exclusions.**
   - A cell whose centre is inside an obstructing solid is excluded and reported as `excluded_measure.inside_obstruction`.
   - A cell inside a component listed in the basis exclusions is excluded and reported as `excluded_component`.
   - Excluded components do not obstruct.
3. **Target fire.** The fire's base is at the cell centre.
   - **POINT:** a single point.
   - **CYLINDER:** diameter D and height H, sampled at `levels` heights. Each level has a centreline point and `rings` points on the circle, so an extended fire is tested rather than a single ray.
4. **Detector response to a target point** requires all of the following:
   - **(a) Field of view.** The point is in front of the detector, and its horizontal and vertical angular offsets in the detector frame are within half the library FOV. The frame is built from azimuth, elevation and roll; roll rotates the right/up axes about the forward axis.
   - **(b) Range.** Distance ≤ R(θ)·s, where θ is the off-axis angle and R is the library contour table, linearly interpolated, with R = 0 beyond the last row. s is 1, or √(Q_target/Q_rated) when INVERSE_SQUARE is selected.
   - **(c) Line of sight.** The segment from the detector, offset by `standoff_m` along the ray, to the point is not blocked by any obstructing mesh.
     - Obstruction uses the CE-02 MV-1 segment/triangle test with a BVH per component and an AABB broadphase per scene.
     - Grazing (coplanar) rays are indeterminate and counted as blocked. They are reported as `indeterminate_rays`.
     - Components declared `NON_OBSTRUCTING_ANNOTATION`, detector markers and basis-excluded components do not obstruct. Undeclared components obstruct, which is conservative.
5. **Detector response to the fire.** The detector responds when (visible responding target points) ÷ (all target points) ≥ `min_visible_fraction`.
6. **Votes.** The votes for a cell equal the number of responding detectors.
   - 0ooN = weighted eligible measure with exactly 0 votes ÷ eligible measure.
   - kooN (k = 1, 2, 3) = weighted eligible measure with ≥ k votes ÷ eligible measure.
   - Each detector's individual fraction is reported.
   - Each user target per zone (1ooN/2ooN/3ooN) is reported as MEETS or BELOW USER TARGET, or as NO USER TARGET.
7. **Convergence (F08).** With refinement r = 2 or 3, the zone is recomputed at h/r. The absolute fraction deltas are reported as CONVERGED or NOT CONVERGED against the user tolerance.
   - An optional ±10 % range sensitivity is also available.

## 3. Geographic gas mapping (CE-05). This is a geographic design-cloud method, not dispersion.

1. **Design cloud.** A sphere (diameter) or an axis-aligned ellipsoid (three full diameters) is centred at each cell centre, with a user-set uniform concentration in %LEL.
   - Cells inside solids are excluded.
2. **Point detector.** It detects when it lies inside the cloud and the cloud %LEL is at or above its alarm threshold (%LEL).
3. **Open-path detector.** It detects when (%LEL/100) × chord ≥ the alarm threshold in LEL·m.
   - The chord is the exact length of the TX→RX segment inside the ellipsoid.
   - The detector is inoperative, with a BLOCKING finding, when the beam is obstructed or its length is outside the library min/max path length.
4. **Voting and targets** work as for flame.
5. **Physical limits.** Gas permeability and flow are not modelled. A point detector inside a fixed design cloud is not a claim that it detects a real leak. Scenario or dispersion data are needed for that (spec §4 Gas detection).

## 4. Reproducibility and storage

Each run stores the following in `coverage_run`:
- `input_json`: the complete envelope, including zone, setup, detectors, the library entries used, scene SHA-256, exclusions, method version, software version and implementation file hashes
- `input_hash`: the SHA-256 of `input_json`
- `result_json` and `samples_json` (the per-cell votes used for heatmaps)
- `actor`, UTC time, and the label

A run is CURRENT only while the recomputed input envelope still hashes to `input_hash`. Workspace edits also mark runs STALE, and undo restores currency. A result is never stored if its inputs changed during the calculation.

Ordering is deterministic: detectors are sorted by ID and cells are visited in grid order.

## 5. Known limits

- **Geometry and occlusion:** geometry is closed triangle meshes. Gratings currently obstruct like solids unless declared `NON_OBSTRUCTING_ANNOTATION`; no partial transparency is modelled.
- **Not modelled:** atmospheric attenuation, detector obscuration from contamination, sun or blackbody false-alarm effects, and response time.
- **Contour:** a single cone-type contour versus off-axis angle, with FOV clipping. Separate horizontal and vertical contour tables are not yet supported.
- **Computation:** pure Python on one thread. Large zones at fine grids take minutes; see the benchmark in the test results.
- **Standards:** no standards conformity (ISA-TR84.00.07, DNV-RP-A102, ISO 13702) is claimed. Licensed review is required.

# Rev G traceability (0.7.0a1)

All Rev G results carry the label "Engineer-reviewed results - not independently certified". The results depend entirely on the detector library data, zones, targets and geometry the user enters. The starter library and the wellhead example use EXAMPLE VALUES, which must be replaced with verified manufacturer data before any project use.

| Spec item | Implementation | Tests (known answer unless noted) | Open / limits |
|---|---|---|---|
| F03 explicit detector data, no generic cone | domain/detector_library.py; services/coverage.py add/import/assign; migration 0004 | test_coverage_engine (library contract); test_coverage_rev_g (immutable IDs, CSV=XLSX, explicit assignment, type checks) | Real manufacturer data to be entered by the user |
| CE-03 fire target and visibility | engine/coverage.py flame_geometry_ok, _flame_votes, target_points (point or cylinder), standoff, INVERSE_SQUARE only if explicitly selected | sector area, cone volume, wall shadow, lens voting, FOV, inverse-square ×4, cylinder partial obstruction | Single off-axis contour; no attenuation or false-alarm modelling |
| CE-04 weighted geographic and voting coverage, convergence | discretise (clipped cell weights), _fractions, convergence by refinement, sensitivity 0.9/1.1 | exact slice and volume fractions, excluded component 4.0 m², determinism; wellhead example CONVERGED at 0.5 m against 0.25 m | Error bound is empirical (refinement delta) |
| CE-05 point and open-path gas (geographic) | _gas_votes, chord_length (exact ellipsoid chord), beam-path validity and obstruction | sphere, ellipsoid, chord, open-path band 3/20, obstructed or overlong beam | A design cloud, not dispersion (CE-06 dispersion not implemented) |
| CE-07 scenario aggregation (partial) | engine/scenario_coverage.scenario_coverage; services/scenario_coverage.run_scenarios | test_scenario_coverage (fraction exactly 0.6, solid flagged, cloud override); wellhead studies (stored, reproducible, stale on edit, refusals) | No risk weighting, uncertainty, response time or SIL credit |
| CE-08 constrained optimisation without baseline mutation | engine/scenario_coverage.layout_options; optimisation.enumerate_layouts(base_votes); layout fingerprint check | Pareto known answer, existing-vote credit, refusals; layout unchanged after runs | At most 16 candidates (exhaustive) |
| CE-09 staleness | input envelope hash (setup, library, detectors, scene, implementation hashes; line-ending neutral) recomputed for currency; workspace edits mark runs STALE | stale after detector edit (zone and study runs); shipped example CURRENT with this code | No incremental recomputation |
| Readiness gate (replaces the hard refusal) | services/coverage.gather/coverage_readiness; basis.readiness at schema 4; detection.engineering_*_coverage | gate refusals; schema-3 cases still BLOCKED (old tests unchanged) | n/a |
| Viewer heatmap, FOV, results (M3) | ui/viewer.py paint_coverage/paint_fov; ui/coverage_dialogs.py | offscreen UI test; Windows real-Qt captures | Manual DPI and multi-monitor review not done |
| Reports (M6) | services/coverage_report.py, services/heatmap.py | outputs, manifest hashes, label, EXAMPLE warning, no overwrite, deterministic content hash, heatmap pixel colours | Human visual review of the Office/PDF output |

Software tests are software evidence only. They are not independent certification, and no standards conformity is claimed.

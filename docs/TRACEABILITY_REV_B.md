# Candidate requirement to executable evidence
Original matrix retained in REQUIREMENTS_TRACEABILITY_REV_A.md.

| Requirement | Production source | Test or executed tool | Result boundary |
|---|---|---|---|
| GEO-01 frames | domain/scene.py | unit/test_scene.py, test_transform_visibility.py | Software known answers only |
| GEO-02 reproducible imports | services/mesh_import.py | unit/test_scene.py; integration/test_geometry_store.py; test_registers_calculations.py | OBJ/ASCII STL only |
| CASE-04 explicit migration | services/geometry.py | integration/test_geometry_store.py | Candidate schema2, original schema1 unchanged |
| CASE-05 history | services/geometry.py | test_undo_redo_reopen, test_immutable_ledger, test_linked_detector_history.py | Scene and linked detector edit undo/redo; other commands pending |
| UI-01/02/03 | ui/main.py, viewer.py, register_model.py | tools/capture_ui.py, check_virtual_register.py, theme unit test | Linux offscreen; Windows not run |
| GEO-03/04 | engine/mesh_visibility.py | test_mesh_visibility.py; independent_triangle_oracle.py | Coplanar refused; no engineering qualification |
| GEO-05 | finite target visibility | tools/benchmark_visibility.py | Symmetric constructive example only |
| FLM-01 | engine/detection.py | test_missing_physics_always_refused | Engineering coverage unavailable |
| FLM-03 math | synthetic_weighted_votes | test_voting_denominators | Supplied synthetic Boolean responses only |
| GAS-01/02 math | UniformDesignCloud | test_gas_point_boundary, test_gas_integral_known_answer, test_thin_and_diagonal_cloud | Not dispersion or detector coverage |
| REP-01/02 | services/reporting.py | acceptance/test_synthetic_reports.py, OUTPUT_SAMPLES, render QA | Development register reports only |
| SCN-01 | engine/scenarios.py | test_exact_decimal_vs_independent_fraction | Aggregation only |
| OPT-01/02 | engine/optimisation.py | test_exhaustive_known_optimum_and_baseline_immutable | Tiny synthetic solver only |
| SEC-02/03 | ai/gateway.py | unit/test_optional_boundaries.py | Offline replay; live transport absent |
| INT-01 | integrations/proposals.py | Interfaces.test_coordinate_inference_forbidden | No live integration |
| ENG-01/02 | docs/QUALIFICATION_READINESS.md | Refusal gates plus readiness register | BLOCKED |
| SEC-01 | tools/build_return_pack.py | PACK_SCAN.json, SHA256SUMS, fresh extraction tests | Development return pack only |

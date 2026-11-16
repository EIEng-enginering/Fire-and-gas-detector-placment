# Development report Rev B
16 November 2026. v0.2.0a1. DEVELOPMENT BUILD / UNVERIFIED.

Branch/base commit: none; no authorised repository. Committed, pushed, merged, published: NO.

## Test result
Untouched WP01 baseline: 10 unit + 8 integration + 1 acceptance = 19/19, zero skipped/failed. Original tests remain byte-identical.
Candidate: 53 unit + 30 integration + 2 acceptance = 85/85, zero skipped/failed on Linux Python3.12.14. Fresh-extraction result and final logs are indexed in TEST_RESULTS/FINAL_SUMMARY.json. Tests run as separate suite processes.

Executed supplementary evidence: exact-rational independent triangle oracle (250 constructed comparisons); 3 deliberately broken candidate implementations caught by assertions; original geometry mutation caught; multiresolution half-square target visibility (16,64,256,1024 samples), each 0.5; 10,000-row extra-register virtual model; actual Linux Qt6.12 offscreen three-theme screenshots and interaction assertions; synthetic example save/reopen; all five report formats generated; every report row/field compared with snapshot; corrupt Excel coordinate refused; DOCX/PDF rendered and visually checked.

Failures encountered are retained and explained in docs/IMPLEMENTATION_REV_B.md. Numerical tests were not relaxed. An order-dependent backup test was strengthened to select and inspect saved and working backups separately, adding unsaved-edit preservation coverage.

## Delivered software
Candidate 13-component synthetic scene, SI frame transforms, additive opt-in schema2 and backups, bounded OBJ/ASCII STL worker, raw source embedding, interactive CPU 3D viewer, equipment/zone records, detector XYZ/orientation editing, scene undo/redo, mesh BVH/finite-target visibility, strict physical-data refusal, uniform-cloud ppm*m exercise, exact Decimal scenario aggregation, tiny exhaustive optioneering, normalized register report exporters/QA, offline replay gateway and synthetic P&ID proposal contract. Precise file map and package-by-package status are in FILE_MAP.md and docs/IMPLEMENTATION_REV_B.md.

## Acceptance disposition
DONE AND VERIFIED: only the explicitly executed Linux software checks above.
DONE BUT NOT VERIFIED ON WINDOWS: candidate Qt application, Windows launch/setup scripts and all platform-specific behaviour.
NOT DONE: complete WP02–WP12 acceptance, full CAD/worksheet/report product scope, manufacturer-specific detector response, qualified F&G coverage, live optional integrations/AI, independent engineering qualification or release.

The shared-ID detector coordinate/geometry transaction and persisted undo/redo are implemented and tested. Next priorities are full virtual register editing/undo, explicit general placement relationships, import review and CAD diagnostics. Owner Q1–Q10/F01–F10 remain PROPOSED. Missing approved manufacturer data, licensed methods, real Windows access and independent reviewer block engineering promotion.

Return contains actual source, tests, raw successes/failures, synthetic case/outputs, screenshots, source change inventory, original archives, state/resume prompt and SHA256 checksums. No source commit or production deployment is implied.

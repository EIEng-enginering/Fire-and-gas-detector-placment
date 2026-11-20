# Known limitations and unresolved blockers — Rev H (20 Nov 2026)

Status: DEVELOPMENT / UNVERIFIED. COMPUTED - UNREVIEWED development results - not independently verified.

## Method limitations (stated, not defects)
- Coverage fractions are sampled-cell fractions: one representative free point per cell, weighted by the cell's free measure. The free measure is exact for axis-aligned box solids; for other closed meshes it comes from adaptive bisection (depth 4) with a rigorous error bound that is reported.
- The two-grid check is agreement only. It is not an error bound or a convergence proof (no Richardson extrapolation).
- Extended fire targets use an equal-weight sampled-point visible fraction. It is not projected area, a view factor or a radiometric response (F14 scope). A justified model is OPEN.
- Gas uses a geographic design cloud, not dispersion. There is no time dependence (CE-06).
- Coplanar/indeterminate rays are treated as blocked (conservative).
- The standoff ignores only the detector's own declared mount component. Without a mount record, LOS starts at the detector.
- Open/non-manifold meshes obstruct sight but exclude no volume; this is reported as a finding.
- The fingerprint closure is a static AST import scan (dynamic imports are not seen; none are used in the closures).
- The layout options search is exhaustive and limited to 16 candidates (65,536 layouts). It is cancellable but uses no incidence bitsets.
- Engineer reviews can be recorded only through the service API (`services/lifecycle.record_review`); there is no UI dialog. No run in the example has a review record.

## Data / authority blockers (unchanged)
- Detector library entries are EXAMPLE VALUES; no verified manufacturer data (OI-003).
- Targets and scenario frequencies are EXAMPLE/user values. No licensed ISA-TR84.00.07 / DNV-RP-A102 content was used (OI-002).
- SYNTHETIC data class only; there is no PROJECT data class.
- No engineering certification, independent verification or safety release exists.

## Performance
- Same host (8 vCPU Intel Xeon, Linux), same scene and grid (0.5 m, refinement 2), sequential runs: Rev G 152.0 s vs Rev H 178.8 s (+17.6 %). The extra time is spent on exact cell measures and representative-point search. No speed-up is claimed. See TEST_RESULTS/REV_H/05_BENCHMARK.

## Pending checks
- Human review of the DOCX/XLSX in Word/Excel on Windows (only LibreOffice renders were inspected).
- DPI/multi-monitor manual checks.
- On Windows, test_symlink_alias_fenced still needs the symlink privilege (WinError 1314). The test is unaltered.

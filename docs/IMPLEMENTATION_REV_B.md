# Candidate implementation Rev B
16 November 2026. v0.2.0a1. DEVELOPMENT BUILD / UNVERIFIED.

## Authority and scope
All Q1–Q10/F01–F10 remain PROPOSED. The owner requested reversible synthetic development through the programme and continued execution; no detailed engineering default, repository, real-data processing, online call or release has been approved. Candidate source is separate from the preserved baseline. The unchanged original owner prompt and decision register remain in docs. No Git repository/branch was created and no commit, merge, push or publication occurred.

## Implemented increments and acceptance boundaries
| WP | Actual source and executed evidence | Programme acceptance |
|---|---|---|
| 01 | Original 19 tests unchanged; complete handover and original archive hashes checked; target Python 3.12.14 used | Foundation tests verified on Linux; Windows and broad crash/concurrency acceptance pending |
| 02 | domain/scene.py; services/geometry.py; mesh_import.py; ui/viewer.py; additive candidate schema2; 13-component synthetic module; SI/frame transforms; OBJ/ASCII STL worker; source bytes embedded; orbit/pan/zoom, pick/tree/register links, hide/show, five views and viewport serialization; actual three-theme Linux offscreen screenshots | PARTIAL. Windows, STEP/binary STL, robust self-intersection diagnostics, clipping, industrial-scale performance and exact Worksheet comparison pending |
| 03 | services/registers.py; equipment/fire/gas zone records; detector XYZ/orientation edit with transactional shared-ID mesh translation and persisted undo/redo; virtual cached extra register tabs; source inspector diagnostics; 10k-row model check; CANDIDATE state and audit | PARTIAL. Detector grid still QTableWidget. Equipment/zone editing UI, paste previews, full persisted edit undo/redo and source reconciliation pending |
| 04 | engine/mesh_visibility.py: segment/triangle, deterministic BVH, finite-target weighted visibility; separate Fraction/Cramer oracle; 250 comparisons, transformed fixtures, multiresolution constructive benchmark and mutation tests | PARTIAL numerical verification only. Coplanar refused; self-intersections/material response and general mesh qualification pending |
| 05 | engine/detection.py: strict engineering flame refusal, separately labelled weighted synthetic Boolean votes | NOT IMPLEMENTED as flame response. Manufacturer data, target/fire basis, approved model and independent qualification missing |
| 06 | UniformDesignCloud point concentration and ppm*m exact-clipped beam integral; explicit synthetic threshold and units; missing-physics refusal | PARTIAL mathematical construct only. No dispersion, CFD, LEL conversion, dynamic sensor response or engineering gas coverage |
| 07 | services/reporting.py: normalized snapshot, JSON/XLSX/DOCX/PDF/ZIP, per-file hash manifest, row/value re-open QA, corruption refusal; Word/PDF rendered and inspected | PARTIAL development register export; not a complete F&G engineering report or Windows Office acceptance |
| 08 | engine/scenarios.py: 34-digit Decimal supplied-frequency/detection aggregation and timely metric; exact Fraction check; no risk-reduction equivalence | PARTIAL aggregation only. No scenario generation, consequence model or time-series simulation |
| 09 | engine/optimisation.py: exhaustive <=16 synthetic candidate enumeration with supplied costs, voting, feasibility, maintainability and Pareto set | PARTIAL test benchmark only. No qualified physics-based optimisation, solver scaling or baseline acceptance workflow |
| 10 | ai/gateway.py: offline synthetic replay, exact preview digest, one-use consent, cost and closed schema checks; no live transport | PARTIAL offline verification harness only. No online provider, redaction, OS secrets, durable jobs or live API permission |
| 11 | integrations/proposals.py: closed, versioned synthetic P&ID tag/connectivity proposal parser, no inferred XYZ or external writes | PARTIAL contract fixture only. No connection to existing owner applications or live reconciliation |
| 12 | Hashes, test/mutation/oracle/convergence evidence, requirement matrix and explicit blockers | NOT QUALIFIED. No independent engineering reviewer, held-out plant studies, licensed methods, vendor data or owner release |

## Numerical method basis
Frame: source XYZ is first multiplied by explicit units-to-metres, then a finite affine right-handed orthogonal-column matrix applies rotation/scaling and metre translation. Shear/mirrors are refused. Source-coordinate absolute bound 1e7 and scale bounds 1e-9..1e9 are developer resource limits, not project engineering criteria. Inversion projects translated world coordinates on the orthogonal columns. Identity/90-degree/nonuniform-scale constructive answers and four arbitrary rotations are tested at 1e-10 coordinate comparison precision.

Mesh MV-1: unit face normal, signed endpoint plane distances, segment parameter and oriented edge halfspaces. Closed contact blocks; explicit tolerance in (0,0.001] m, with tested examples at 1e-6/1e-8/1e-10. Coplanar segments are indeterminate and refused. BVH bounds are expanded by tolerance. Finite-target result is positive-weighted *geometric sample visibility*, not radiance or detector response. Separate oracle uses exact rational determinants/Cramer's rule and imports no production engine. Constructive half-square visibility is exactly 0.5 at grids 4,8,16,32 per axis. This symmetric example is verification, not general convergence evidence.

Gas exercise: uniform concentration in a supplied closed AABB; point on boundary is inside. Clip a segment against each axis, retain exact rational t bounds converted once to float for physical chord length, multiply by supplied ppm. Output units ppm*m. This prevents subtractive cancellation in the 200 ppm*m axial known answer. General diagonal result remains float with tolerance 1e-7 in unittest's default numerical comparison; gas-specific LEL conversion is refused. No detector response time or dispersion is implied.

Scenario exercise: Decimal context precision 34, source strings required, frequency 1/year, finite nonnegative frequency, p in [0,1]. Outputs unweighted mean probability and frequency-weighted detection separately; timely metric absent if any timing input is missing. No frequencies or risk reduction are invented. Optimisation is exhaustive supplied synthetic incidence data, stable candidate order and exact Decimal costs; no engine-based engineering recommendation is claimed.

## Data and migrations
Original 0001_initial.sql and manifest.json are unchanged. candidate_manifest.json labels schema2 as NOT OWNER FROZEN. Upgrade is explicit; runtime verifies both migration hashes. Saved original and pre-upgrade working copy are backed up. Migration plus audit runs in one SQLite transaction. Original schema1 cases remain usable without upgrading; schema2 requires this candidate program. Geometry scene JSON stores exact typed source frames and meshes plus hashes. Imported raw bytes, source frame and diagnostics are stored separately in geometry_attachment, retaining original units after normalization. Scene and detector-edit undo/redo replay append-only compensation events across reopen with conflict refusal. Evidence/record creation and other command history remain incomplete and are not asserted.

Calculation run records retain full synthetic inputs, method, input hash, result, calculation status, qualification and review separately. Geometry/register edits mark existing runs STALE; no downstream engineering approval exists. New ledger update/delete triggers enforce immutability in schema2; schema1 remains unchanged.

## Dependency and licence evaluation
Display uses existing pinned PySide6 6.12.0 widgets and QPainter software projection; no VTK, OpenGL, PyVista or CAD dependency is added. It is a real interactive 3D projected-mesh display with a painter's algorithm, with depth/intersecting-surface limitations; it is not an equivalent high-fidelity industrial CAD viewer. Qt licence obligations require owner review before distribution/release. Report dependencies are optional and pinned separately. No runtime network, telemetry, provider SDK or automatic download exists in the application. Shell installation downloads were limited to the exact authorised development dependency. Shipping a binary or licence compliance sign-off has not occurred.

Current public reference checks (existence/API/licence only; not standards qualification):
- https://pypi.org/project/PySide6/6.12.0/ (version and supported Python listing)
- https://doc.qt.io/qtforpython-6/commercial/index.html (licence choices; legal assessment pending)
- Original handover research queue remains authoritative for unavailable licensed engineering references; no full clauses were obtained or claimed implemented.

## Defects encountered and disposition
1. UI viewport tuple/list mismatch on state restoration: normalized serialized vector lists, retest passed; initial failure retained.
2. Axial cloud path integral returned 199.99999999999994 vs exact 200: rational clipping fixed implementation; exact known-answer assertion retained.
3. Report JSON snapshot tuple/list mismatch: producer now returns canonical JSON-normalized snapshot; no value comparison removed.
4. Worker stdout could block before process exit for output above pipe capacity: temporary-file stdout/stderr, bounded result read, explicit process kill/reap; 1200-triangle regression added.
5. Migration backup test chose an arbitrary directory entry after a second backup type was added: test now identifies saved vs working backups and checks both explicitly, plus an additional unsaved-edit preservation test. No baseline test or numerical tolerance was weakened.
6. Raw JSON report layout replaced by readable field/value tables and labelled fields; headers repeated and rows kept together. PDF records kept together after visual QA found orphan headings.

7. Shared-ID detector placement translation and compensating history added before final handoff; conflicting scene history now refuses instead of overwriting intervening edits. Two regression tests cover geometry/register recovery and actor rollback.
8. Original mutation tool selected a non-directory after new top-level evidence files were added: selection now filters dated run directories; mutation assertions remain unchanged.

## Remaining non-negotiable limitations
No qualified flame/gas coverage is available. Passing tests, pretty geometry, sampling visibility, scenario weighted ratios and synthetic optioneering cannot approve detector placement, SIL, FGS effectiveness, standards compliance or facility risk. Engineering outputs require the missing source data, approved basis, method review and named owner promotion.

# Fire & Gas Mapping Engineering System
## Engineering Master Specification - Revision A (candidate requirements)
Date: 16 November 2026 | Status: DEVELOPMENT DESIGN | Engineering methods UNVERIFIED

Purpose: specify a standalone, Windows 11, offline-first engineering application for preparation, calculation, interpretation, reporting, and controlled review of fire and gas detector mapping studies, particularly FPSOs, offshore platforms, LNG plants and onshore process facilities. This is a DRAFT specification, not an approved design basis and not a claim of compliance.

## 1. Governing controls
The owner's EIE-STANDALONE-BUILD-PROMPT-01 is incorporated without silently altering its ten fixed practice rules. Proposed exceptions or adaptations are entered as design issues. Engineering assertions are provenance-linked, generated calculations are numerical and independently checked, synthetic-only test fixtures, no outside transmission by default, no code push or merge without specific approval, manual review remains possible.

## 2. Product boundary and deliverables
First useful engineering application: deterministic 3D flame detector mapping with user-defined performance targets, qualified geometry model, coverage algorithm and traceable results, once independently tested. Later modules: geographic point/open-path gas mapping, scenario-based coverage, uncertainty/sensitivity, optioneering, detector reliability and FGS system effectiveness integration, and constrained AI preparation. A live FGS controller, SIS controller, alarm logic solver, CFD solver, full QRA model and design certification are OUT OF SCOPE for initial development.

## 3. Inputs and preflight checks
- Facility identity, location coordinate system (local/global), datum, right-hand/left-hand convention, units, model revision.
- Geometry: native/projected 2D plans with explicit elevation data, STEP/IGES solids, mesh formats such as STL/OBJ, approved surface models, and controlled manual geometry. P&IDs supply connectivity only, never unverified absolute positions.
- Geometry component properties: category; obstruction transparency/occlusion; fire-zone membership; uncertainty; provenance; CAD revision; coordinate transform history. Distinguish transparent meshes, gas permeability, sight obstruction, inaccessible and excluded regions; categories do not silently imply one another.
- Fire/gas zone boundaries, relevant process equipment, hazardous event definition, design-basis fire/target or gas cloud, performance targets, facility philosophy, voting and operating states.
- Detector library: manufacturer, model, fuel, target-fire size, calibrated FOV/range contours, sensitivity, mounting orientation, obstruction, service condition, approval/reference revision. If model data is missing, prohibit engineering calculation, do not substitute a generic cone silently.
- Release scenario definitions (later): material, phase, temperature/pressure, leak diameter/direction/duration, release frequency with referenced basis, meteorology, ventilation, scenario assumptions, consequence model version, time step.
- Source record fields: source ID, document title, document revision/date, location (page/box/coordinate or data field), source statement/units, extraction method, source hash, review actor and time. Unknown is NOT SUPPLIED.
- All figures in SI internally; keep source units and conversion record. Input validation includes positive/finite parameters, bounds and coordinate-transform reasonableness.

## 4. Engineering definitions and result types
### Geographic coverage
A zone is discretised into representative sampling points/volumes. For each placement and design-basis target, a validated detector response function gives a detection condition. The achieved N-out-of-M geographic coverage is the total eligible weighted sample volume satisfying required votes divided by total eligible weighted volume. Zone weights must reflect actual sampling volume, not simply raw point count, especially where adaptive grids differ. Excluded volumes, plant occupancy and partial volumes must be explicitly documented. Maintain separate 0ooN, 1ooN, 2ooN, etc. No acceptance percentage is hard-coded.

### Fire detection
A simple centrepoint visibility and nominal cone/range are useful only as educational geometric examples. The qualified engine must implement an explicit target fire geometry and fuel/size/sensitivity-specific response, physically appropriate projected visible fire area, angular sensitivity, optical obstruction, range, detector mounting and applicable environmental effects. Analyse fire target size, orientation, detector response bounds and sensitivity. Test obstruction to a spatially extended fire, not only one ray. DNV-RP-A102:2026 methodology must be evaluated from a licensed copy before any specific conformity claim.

### Gas detection
Geographic gas mapping uses project-approved design cloud volume shape, effective detector threshold, point sensor intersection or open-path path integration and applicable sensor response. Geographic cloud-radius models are not equivalent to physical dispersion; name them accurately. Scenario-based gas mapping must use qualified cloud concentration/time fields or an independently verified model. Include thresholds, delay, voting and meteorology. Do not claim a point sensor detects a leak because it lies within a fixed arbitrary radius.

### Scenario coverage and risk
For each scenario, record source, annual frequency (if applicable), weighting method, time-dependent detection condition, gas/fire hazard definition and result. Keep unweighted fraction, frequency-weighted fraction, detection-on-time and relevant mitigation effectiveness separate. Detector coverage must never be presented as equivalent to FGS effectiveness, availability, or risk reduction.

## 5. Calculation engines
CE-01: geometry ingestion and reproducible boundary processing with persistent shape IDs and transform records.
CE-02: spatial index / ray-triangle and segment-obstacle intersection. Grazing contact convention must be an explicit study method parameter, not a buried constant.
CE-03: fire target modelling and candidate visibility with manufacturer performance envelope. Provide strict no-data refusal.
CE-04: weighted geographic and voting coverage. Capture precision, mesh density, convergence, truncation, and error bounds.
CE-05: point and open-path gas mapping, with explicit units, integrated concentrations and detector-specific behaviour.
CE-06: time-dependent scenario detection/response and optional validated dispersions.
CE-07: scenario aggregation and risk weighting with sensitivity and uncertainty.
CE-08: constrained detector layout optimisation; never optimise over unbuildable positions or mutate the official baseline without approval.
CE-09: result dependency graph, staleness detection and incremental recomputation.

## 6. Numerical reproducibility and performance
- Python 3.12 pure engineering core, testable without PySide6. Use floating-point for 3D computational geometry with documented tolerance, convergence and deterministic ordering. Use Decimal for designated decimal probability/accounting calculations as required by the owner's standard.
- Never infer accuracy from rendering. Geometry and output algorithms must be tested independently against constructive solids, CAD benchmarks and held-out reference studies.
- Separate engine worker process for expensive mesh preparation and long calculations; explicit time/memory budgets, cancellation, partial results clearly marked INCOMPLETE. UI must remain responsive.
- Adaptive resolution studies, mesh/voxel grid convergence, face winding, watertightness, non-manifold cases, self-intersecting shapes, coordinate scales and floating-point edge cases.
- Document time/memory benchmark on a representative Windows laptop with Intel i5 after first real run; do not invent benchmarks.

## 7. Engineering model and workflow
Case -> facility -> geometry revision -> equipment -> source documents -> zones -> detector catalogue -> detector placements -> scenario sets -> method versions -> calculations -> findings -> review decisions -> exports. Every object has immutable ID, evidence, status and version. Workflows: manual engineer-led wizard and expert workspace; assisted data preparation later. All AI proposals remain CANDIDATE pending named review; no automatic engineering approval.

## 8. Presentation
Three theme tokens exactly as owner's Worksheet standard; grey default. Dockable left navigator, central 3D viewer, bottom tabular register, right inspector and linked properties. Spreadsheet editing and keyboard focus must be adapted to geometry workflows. Visual legend distinguishing fully tested values, draft results, blocked data, calculation errors, and user-supplied criteria. No result heatmap without explicit method and legend. 2D plan/elevation views and 3D orbit/pan/zoom; selection synchronised across viewer, detector register and source pane. Persistent saved layout per PC.

## 9. Data storage, security and interoperability
- One portable .fgcase SQLite package proposed; normalised structured tables, source documents and optimised geometry caches. Large raw models might require a size policy and incremental embed; no broken external dependencies in a portable saved case.
- Active editing occurs on a local single-writer copy with conflict detection, fsync/atomic replace and recoverable unsaved session. Do not operate in WAL on multi-host shares. A OneDrive-synchronised file is not the active editing database.
- Versioned migrations and frozen contract hashes; backward-compatible changes by explicit owner review.
- Secure independent processes for untrusted CAD conversion; limit size, recursion, vertices, decompression and external references. No network use or telemetry by default.
- Optional future interface with P&ID Reader, safety modelling software, HAZOP/SIL Worksheet; proposal-only inbound/outbound exchange contracts, never silently change original studies.

## 10. Quality and qualification
Development tests do not confer engineering validation. Qualification requires method-by-method independent verification against pre-registered known-answer and held-out examples, documented tolerance, uncertainty, sensitivity, limitations, numerical convergence, and independent engineering review authorised by owner. Maintain distinct flags: computation state; evidence state; human review state; study data class; software method qualification state. No false 'approved/certified/safe' claims. Every report is reproducible from a frozen case snapshot and records methods, inputs, detector references, versions, sample counts, voting, tolerances and exclusions.

## 11. Missing standards detail and licence restrictions
Official public descriptions of ISA-TR84.00.07:2026, DNV-RP-A102:2026, ISO 13702:2024 establish their relevance, not their full normative text. Obtaining licensed copies, interpreting project contractual obligations, and deriving qualification tests remain open engineering activities. No standard equations or detector manufacturer curves have been fabricated.

## 12. Initial release exclusions
Not supported in v0.1.0a1: production CAD import, flame response calculation, gas detector calculation, 3D Qt viewer, voting-driven engineering coverage, safety report, optimisation, live data, AI gateway, independent external validation, release installer. The included geometry demonstrations only prove select mathematical programming behaviours.

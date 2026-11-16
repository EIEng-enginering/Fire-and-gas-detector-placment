# Rev C candidate user guide
This program works offline with synthetic development data. No engineering detector coverage is available.

Open examples/SYNTHETIC_REV_C_CONNECTED.fgcase using Case > Open case. All four register tabs use virtual tables. Type in the filter to search cached fields; click a header to sort (XYZ sorts numerically). Right-click a header to choose visible columns or follow the selected row. Column layout is stored per PC. Ctrl+C copies selected cells and highlights them. Ctrl+X is explicitly refused because mandatory engineering fields cannot be implicitly cleared.

Use Add candidate record or Edit selected record. Detector forms collect ID, type, SI XYZ, orientation and evidence; a new evidence record requires description, revision and locator. Enter a named editor. Optional manufacturer/model/sensitivity entries are source fields only; supplying names does not create a performance dataset or permit engineering calculation. Explicit synthetic markers can be created. Marker cubes are display symbols, not physical detector dimensions, range or FOV.

For equipment, select a geometry component where supplied. Fire/gas zone forms use ordered lower/upper XYZ bounds in metres and a design-criterion reference. Unknown criteria remain NOT SUPPLIED and generate a preparation finding. Orientation arrows and dashed zone boxes are illustrative annotations; they are not coverage plots. Azimuth is +X toward +Y, elevation above XY; roll is retained but the direction glyph does not represent roll-dependent response.

Paste starts from the current detector Type or X/Y/Z cell. Ctrl+V opens a before/after preview; enter a named editor and Apply. Pasting can update existing Type/XYZ cells only. IDs, evidence and review status are protected. All cells commit together; linked markers move with them. Sorted/filtered row order maps to stable IDs.

Undo workspace edit / Redo workspace edit restores the new detector/record/paste/import commands across closing/reopening. New edits clear redo. A conflicting intervening change refuses history instead of overwriting it. Remove selected candidate record explicitly removes a detector/equipment/zone from the study; prior values remain in the ledger and source evidence is retained. Referenced detector geometry must be detached before removal. Legacy scene/name commands have separate history; the Scene Undo buttons remain for legacy synthetic scene replacement.

Import synthetic mesh parses triangulated OBJ or ASCII STL in a cancellable worker. Declare source units, datum and right-handed axes first. After parsing, review the source hash/frame/diagnostics, choose APPEND or REPLACE and name the reviewer. Applying creates CANDIDATE geometry, not engineering acceptance. Raw source bytes/provenance stay retained when the imported scene is undone. Source changes, duplicate components and invalid meshes are refused. Self-intersections, STEP and binary STL remain unsupported.

Inspect evidence / findings opens the selected source record and the preparation findings. Missing performance data, missing zone criteria, orphan links and stale runs remain visible. A finding list is not a standards assessment or sign-off.

Case > Run supplied synthetic exercise accepts the closed synthetic JSON contract. examples/SYNTHETIC_FIELD_PATH_EXERCISE.json demonstrates concentration/time interpolation and a beam integral with an explicitly selected resolution. This does not model dispersion, sensor qualification, FGS effectiveness or risk reduction.

Case > Export synthetic study reports freezes the current snapshot and illustrative viewer figure, asks for a new output folder, then generates JSON/Excel/Word/PDF/ZIP in a cancellable process. No further input is requested while that job runs. Parser QA compares all primary records and findings with the snapshot; visual/native Office and engineering review remain separate. Existing output folders are not overwritten.

Left-drag orbits; right-drag pans; wheel zooms; preset buttons provide standard views. Tree checkboxes hide display components. Camera/visibility survive ordinary refreshes and a per-case view is saved per PC. The rendering uses a CPU painter algorithm with known depth limits; calculations use separate numerical engines.

Save/close uses a local working copy and conflict checks. No on closing preserves unsaved work for explicit recovery. A .writer.lock sidecar can remain beside a case; it is operational and contains no project data. Do not remove locks while a writer is active. Windows abnormal-lock cleanup and OneDrive/multi-host semantics remain unverified.

![Executed Rev C workflow in Linux offscreen Qt](screenshots/REV_C_WORKFLOW_grey.png)

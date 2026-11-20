# Open issues
- OI-001 CRITICAL: owner approvals Q1-Q10/F01-F10 in docs/DECISIONS_REV_A.md.
- OI-002 CRITICAL: licensed ISA-TR84.00.07:2026 and DNV-RP-A102:2026 content not provided; cannot derive full method requirements.
- OI-003 CRITICAL: no manufacturer-specific fire detector performance dataset approved or licensed.
- OI-004 HIGH: Qt GUI and theme screenshots not tested on real Windows 11/Python 3.12.
- OI-005 HIGH: actual 3D scene viewer and qualified mesh/CAD imports not implemented.
- OI-006 HIGH: complete compensating command ledger, redo, and linked source changes not implemented.
- OI-007 HIGH: no complete data model for zones, fire targets, uncertainty, scenario and calculation records.
- OI-008 HIGH: per-PC settings persistence and direct exact-UI comparison with user's actual Worksheet still pending; Github repository currently empty.
- OI-009 HIGH: all report formats and snapshot cross-format round-trip QA pending.
- OI-010 HIGH: crash recovery GUI decision semantics (discard vs preserve unsaved changes) require user testing.
- OI-011 HIGH: size bounds for SQLite embedded geometry and source files require performance testing.
- OI-012 HIGH: full security and external API gateway gates not implemented (no AI networking present).
- OI-013 HIGH: schema manifest hashes generated but owner has not frozen it.
- OI-014 HIGH: Windows create_case hard-link compatibility must be tested before calling atomic create verified.
- OI-015 HIGH: Windows launch PowerShell scripts and real Qt platform unit/integration separation not yet verified.
- OI-016 HIGH: no repository path/branch selected; do not commit, push, merge or publish.

## Rev B assessment and additions
All unresolved original issues remain open unless narrowed below.
- OI-005 PARTIAL: interactive synthetic 3D CPU viewer and OBJ/ASCII STL now exist; industrial CAD/STEP, clipping and qualified diagnostics remain missing.
- OI-006 PARTIAL: scene and detector-edit persisted compensating undo/redo and immutable schema2 ledger added. Full register undo/redo not implemented.
- OI-007 PARTIAL: geometry, engineering records, detector orientation and synthetic calculation history added. Full physics/scenario/performance model absent.
- OI-009 PARTIAL: all five register export formats now generated and parser checked; complete engineering report and native Windows/Office checks remain missing.
- OI-012 PARTIAL: offline AI replay tests exist; no live gateway or credentials/network path exists.
- OI-017 HIGH: viewer is CPU painter projection, no full depth buffer; intersecting meshes can display incorrectly. Not calculation truth.
- OI-018 HIGH: geometry diagnostics explicitly do not evaluate self-intersections, gaps by tolerance, STL normal correctness or CAD tessellation accuracy. No automatic engineering acceptance.
- OI-019 HIGH: Windows process memory limits require Job Objects; POSIX worker limits are not Windows evidence. Child isolation is not an OS security sandbox.
- OI-020 HIGH: baseline case locking is runtime/path-specific; another runtime/alias can bypass the single-writer lock. Compare-then-replace save has a concurrency race across separate runtimes. OneDrive multi-host acceptance not established.
- OI-021 HIGH: working-copy/recovery metadata and lock cleanup need fault-injection tests around fsync/rename/crash. No blanket crash-safety claim.
- OI-022 PARTLY RESOLVED: shared persistent-ID DETECTOR mesh components now translate transactionally with coordinate edits; persisted edit undo/redo restores both and rejects history conflicts. General explicit attachment relationships, orientation glyphs and arbitrary-source placement workflow remain pending.
- OI-023 HIGH: full 10k detector GUI test pending; 10k check exercised virtual extra-register model only, not QTableWidget detector grid.
- OI-024 MEDIUM: camera state serialized per PC, but loading a scene fits the view; exact case-specific saved view restore and component visibility persistence pending.
- OI-025 HIGH: source app remains src-layout dependent for contracts. Installed-wheel resource packaging and Windows executable absent; use supplied source launcher.
- OI-026 HIGH: synthetic calculation-run staleness covers implemented register/geometry edits only; complete dependency graph is not implemented.
- OI-027 HIGH: report exporter is a development register/audit export, not a full engineering study report; large-record pagination and spreadsheet visual/Office acceptance need more work.
- OI-028 MEDIUM: AI replay consent consumed in memory only; durable grant consumption/restart, real provider allowlist, redaction, secrets, budget accounting and logs need implementation before online work.
- OI-029 HIGH: qualification requires licensed methods, vendor data and independent competent review. All technical methods remain UNVERIFIED.
- OI-030 MEDIUM: original foundation allows repeated tag attempts to create separate evidence before detector rejection through the demo UI. Make evidence+detector creation one command and add general compensating history.
- OI-031 HIGH: synthetic run envelopes retain inputs, scene hash and named method version, but not yet the implementation's source-module hash. The return manifest provides source revision externally; add per-run code/contract fingerprinting before engineering reproducibility claims.

## Rev C dispositions supersede earlier entries
- OI-006 PARTIAL: new workspace commands have persisted conflict-aware undo/redo including create/edit/paste/remove/import. Legacy APIs retain separate histories; full unified legacy history remains open.
- OI-009 PARTIAL: report generation is now connected to the UI in a cancellable process with illustrative figure/findings. Parser and local Word/PDF visual QA executed; native Office/production template acceptance pending.
- OI-020 IMPROVED: native stable writer fence covers cooperating Rev C writers across runtimes/symlinks; hard links refused; a live legacy PID in the same runtime is respected. Different-runtime legacy/external writers, remote multi-host and OneDrive semantics remain unverified.
- OI-021 IMPROVED: atomic metadata and pending-save journal tested with injected pre/post-install failure and POSIX process kill. Windows stale-lock recovery stays conservatively blocked pending implementation/real-platform verification.
- OI-022 IMPROVED: markers can be explicitly created, edited, bulk-moved and removed/restored transactionally. Stored orientation arrows added. General arbitrary CAD attachment transforms/roll response remain pending.
- OI-023 RESOLVED FOR LINUX SOFTWARE CHECK: main detector grid is now virtual, and 10k rows/filter/sort exercised. Actual Windows responsiveness still pending.
- OI-024 IMPROVED: ordinary refresh preserves view/visibility; per-case camera and per-PC column layout persisted. More Windows/DPI testing required.
- OI-026 PARTIAL: new workspace edits invalidate runs conservatively. Fine-grained dependency graph not implemented.
- OI-030 RESOLVED IN NEW GUI WORKFLOW: evidence+detector+marker creation is atomic; duplicate/actor failure leaves no orphan evidence. Legacy add APIs remain available for compatibility.
- OI-031 RESOLVED FOR NEW SYNTHETIC RUNS: software version, method/input/scene and implementation-module hashes recorded. Historical runs are not retroactively assigned fingerprints.
- OI-032 HIGH: Windows stale runtime-lock inspection/recovery, Job Object memory limits and true platform acceptance remain pending. POSIX symlink tests require Windows prerequisites or a reviewed equivalent.
- OI-033 MEDIUM: native report spreadsheet visual/Office validation and arbitrary large-record layout need further work. Current synthetic Word/PDF layouts were rendered/inspected.
- OI-034 MEDIUM: empty manual classes/criteria may remain candidate missing inputs; preparation findings are incomplete engineering coverage checks, not approval.
- OI-035 HIGH: generic source/import/record proposals have no engineering acceptance path. All review status remains CANDIDATE/UNVERIFIED until named approval is designed and authorised.

## Rev D dispositions supersede earlier entries
- OI-022 IMPROVED: explicit component mounts/source anchors/metre offsets/full orientation now implemented and independently tested. Source changes require explicit remount; no automatic engineering remapping.
- OI-032 IMPROVED: Win32 three-state process inspection implemented with injected-kernel tests; actual Windows stale-lock/crash/recovery, Job Objects and platform acceptance NOT RUN.
- OI-033 IMPROVED: schema3 report overview/schedules/comparison, complete long-field chunks and embedded PDF fonts now verified by parser and rendering. Native Office/large project/report histories remain open.
- OI-034 IMPROVED: structured basis, explicit criteria/voting/exclusions and preparation readiness now exist; engineering calculation stays BLOCKED. Method-specific completeness/approval remains open.
- OI-035 OPEN: append-only draft reviews now retain named subject hashes and stale state; no engineering approval/promotion path exists.
- OI-036 HIGH: candidate schema3 not owner frozen; older source versions do not read schema3. Upgrade is explicit/backed up, not transparent backward compatibility.
- OI-037 HIGH: preparation data contract is SYNTHETIC-only; exact row lookup is not detector response. Authorised real curves/conditions/units and legitimate method engine still absent.
- OI-038 HIGH: geometric lower/upper bounds address ray ambiguity only, not physical/model uncertainty; no qualified solid/intersection/CAD/dispersion/FOV analysis.
- OI-039 HIGH: restore-as-new is verified on Linux; Windows hard-link/NTFS/cancel race/crash and cloud-sync need platform evidence. Installed target may exist after late cancellation; inspect before retrying.
- OI-040 HIGH: no Windows EXE/installer/signing/offline wheelhouse; full source layout/contracts required.
- OI-041 MEDIUM: general bulk-register import, source revision reconciliation, mount remapping, full report histories and mesh acceleration remain independent reversible next work.
Original OI-002 edition labels are inherited unresolved reference requests, not verified access to those editions or clauses. Obtain legitimate current references before engineering use.

## Rev E dispositions and checkpoint
- OI-041 IMPROVED: synthetic detector/equipment CSV/XLSX import and explicit stable-ID facility revision/follow-detach now implemented. Richer fields/zones/source metadata/parent/evidence/anchor redeclaration remain open.
- OI-042 HIGH: revision following is frame-local anchor reuse; no automatic surface correspondence or mechanical mounting acceptance.
- OI-043 MEDIUM: preview worker is killable; commit reconstruction stays on owning thread.2000 rows measured on a small synthetic case only; dense geometry/large case bounds and UI responsiveness need further evidence.
- OI-044 HIGH: scene broadphase passes independent/equality examples, not general industrial CAD/solid or physical method qualification.
- OI-045 HIGH: real Windows/Office/NTFS/Win32/DPI/clipboard/crash acceptance remains pending; no installer/EXE/offline wheelhouse.
- OI-046 MEDIUM: richer input-parser hardening (including explicit duplicate-key JSON policies), report histories and dependency graph remain future work.
- OI-047 MEDIUM: raw source reviews retained after undo; current entity state must be checked separately. Revision comparison currently emphasises geometry/frame fingerprints, not all metadata semantics.
All earlier unresolved engineering/data/owner-decision gates remain. This is an intentional working checkpoint requested by the owner; no entire work package or programme is accepted from190 passing tests.

## Rev F dispositions
- OI-045 IMPROVED: native Windows suites, real-Qt smoke/workflow, NTFS recovery suites and Excel literal read-back executed automatically. Manual keyboard/DPI/multi-monitor/visual Office-PDF/human cancellation and file-lock items remain pending.
- OI-048 HIGH (new, closed in Rev F): Rev E failed on Windows — read-only fsync (EBADF) and unclosed SQLite connections (WinError 32). Fixed; regression tests and mutants added.
- OI-049 MEDIUM (new): test_symlink_alias_fenced requires Developer Mode or SeCreateSymbolicLinkPrivilege; fails on the owner PC. Resolve the prerequisite under policy; do not skip the test.
- OI-050 MEDIUM (new): Word COM automation hung invisibly during read-back; Word/PDF native inspection not completed.
- OI-051 LOW (new): real-Qt screenshots show truncated register header and component IDs at default window size.
- OI-052 LOW (new): tools/rev_e_benchmarks.py hard-codes 'Linux; Windows NOT RUN' in its output even when run on Windows; Rev E tool left unchanged to preserve evidence semantics.
All earlier engineering/data/owner-decision gates remain.

## Rev H (20 Nov 2026)
- Independent review findings F01–F25: all FIXED within the scope in docs/FIX_DISPOSITION_REV_H.md, but this has not yet been independently re-reviewed.
- OI-H1 MEDIUM: there is no UI for recording engineer review (API only).
- OI-H2 MEDIUM: there is no justified extended-target visibility model (F14 limitation).
- OI-H3 LOW: Rev H coverage is about 18 % slower than Rev G on the same host.
- OI-H4: the Rev H return is uncommitted; commit or push needs explicit owner authorisation.

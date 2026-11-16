# Candidate user guide
This is a synthetic development application. No engineering flame/gas coverage result is available.

Open the supplied example using Case > Open case. Select a component in the 3D display or component tree; exact matching detector IDs select register rows. Left-drag orbits, right-drag pans, wheel zooms. Fit resets the view; Top, Front, Side, Isometric and Perspective provide preset cameras. Visibility checkboxes affect display only. Tooltips show mesh diagnostic limitations. The three themes use the owner-supplied Worksheet tokens.

![Actual Linux offscreen grey theme](screenshots/WP02_grey_LINUX_OFFSCREEN.png)

Detector XYZ values are SI metres. Select a detector and choose Edit selected detector coordinates / orientation; enter a named editor. Allowed azimuth/roll range is -180..180 degrees, elevation -90..90. Missing performance/model fields remain NOT SUPPLIED. A coordinate edit marks stored calculations STALE and leaves the detector CANDIDATE. A matching persistent-ID DETECTOR geometry marker moves transactionally with XYZ edits. Undo detector edit / Redo detector edit restores the register and scene together across reopen; conflicting subsequent scene changes block history rather than overwriting them. Marker cubes do not display an optical response or orientation envelope.

Equipment and fire/gas zone tabs display cached virtual registers. Full grid editing, paste previews, group layouts and all-command undo/redo are still pending. Scene Undo / Redo compensates scene replacement commands and survives saving/reopening; it refuses conflicting intervening detector geometry changes. Detector edit history is separate. Full evidence/register-add undo remains pending.

Import synthetic mesh accepts local triangulated OBJ or ASCII STL with explicit source units, datum and right-handed coordinate declaration. Identity transform is explicitly declared by the import form. Source bytes, original frame, diagnostics and hashes are stored in the case. Imports replace the current scene as an undoable command. No material file is loaded and no network access occurs. STEP, binary STL, self-intersection qualification and arbitrary coordinate transform editing are not yet supported. Cancel terminates and reaps the import process.

Use Case > Save case to atomically save the local working copy after conflict checking. Closing with No preserves unsaved work for explicit recovery rather than silently deleting it; Cancel keeps editing. Backups and working copies use the per-PC runtime. Do not delete locks/recovery data without checking active sessions. Cross-machine/synced-folder concurrency is not yet qualified.

Development register report outputs are supplied under OUTPUT_SAMPLES/SYNTHETIC_STUDY. The one normalized snapshot supplies JSON, Excel, Word, PDF and ZIP, including provenance, missing inputs and UNVERIFIED status. The example integral is a synthetic uniform concentration exercise, not gas coverage. Scenario aggregation/optimisation and offline AI replay are tested library/CLI functions, not completed engineering GUI workflows.

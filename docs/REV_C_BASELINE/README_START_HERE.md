# Fire and Gas Mapping Engineering System Rev C
16 November 2026. v0.3.0a1. DEVELOPMENT BUILD / UNVERIFIED.

Rev C adds a connected, executable synthetic study workflow to Rev B. It contains actual source, test evidence, synthetic cases/reports and screenshots, not a replacement planning prompt. Read USER_GUIDE.md and HOW_TO_RUN.md, then docs/REV_C_ENGINEERING_AND_WORKFLOW.md for implementation and limits.

Start: review/run setup.ps1 -Reports in a new source folder, then run.ps1. Open examples/SYNTHETIC_REV_C_CONNECTED.fgcase. This case contains an edited detector and explicit marker, equipment, a fire zone and a fingerprinted synthetic concentration-field calculation. All engineering qualification/review remains UNVERIFIED/CANDIDATE. No manufacturer flame/gas coverage method is available.

The app now provides four virtual filterable/sortable registers, named-editor forms, atomic multirow paste with preview, persisted workspace undo/redo, detector removal with reference checks, zone/orientation annotations, import review with append/replace, source/findings inspection, background report export and a supplied-synthetic-exercise runner. New case tests cover native locks across runtime folders, live legacy-lock refusal, process kill and interrupted-save recovery. These are Linux tests, not Windows acceptance.

Outputs: OUTPUT_SAMPLES/REV_C_WORKFLOW_STUDY contains JSON, Excel, Word, PDF and ZIP from one snapshot including the actual illustrative viewer PNG and preparation findings. Word/PDF were rendered and visually inspected. Tests, intermediate failures and corrections are retained; final counts/fresh extraction are in TEST_RESULTS/REV_C_FINAL_SUMMARY.json. Rev B's original 85 tests are unchanged.

Original WP01/takeover and Rev B ZIPs are preserved in ORIGINAL_ARCHIVES. SHA256SUMS.txt covers the return files. Operational .writer.lock sidecars/caches are excluded. Source revision is this manifest, not a fictional Git commit. No repository/commit/push/merge, live API, client processing, publication, independent qualification or release occurred.

The programme is still incomplete. Windows11/real Qt acceptance, robust CAD/STEP, manufacturer response data/methods, full standards/engineering review, complete production reporting/UX and independent qualification remain open. Q1–Q10/F01–F10 remain proposed. See PROJECT_STATE.md and NEXT_WORK_PROMPT.txt for the precise continuation.

# Fire & Gas Mapping Engineering System — Rev E
16 November 2026. Version0.5.0a1. DEVELOPMENT BUILD / UNVERIFIED.

Rev E is a complete source return pack at a working development checkpoint. It adds executable synthetic bulk register import, explicit geometry revision reconciliation, stronger geometry verification, a scene-level spatial filter, source-review/mount-decision reporting and recovery fault tests. It does not complete or qualify the full WP02–WP12 engineering programme.

Start: read HOW_TO_RUN.md and USER_GUIDE.md, review setup.ps1, install the pinned dependencies in a Python3.12 development environment, then launch run.ps1. Open examples/SYNTHETIC_REV_E_STUDY.fgcase. Windows11/PySide6 6.12.0 is the target; actual execution here was Linux Python3.12.14/Qt offscreen. No EXE, installer or offline dependency wheelhouse is supplied. Once dependencies are installed, the demonstrated app runs offline.

The unchanged Rev D baseline passed168 tests before edits; all600 file hashes were verified. Current suite:190 tests (87 unit,95 integration,8 acceptance), zero failures/skips; final and fresh-extraction results are indexed in TEST_RESULTS/REV_E_FINAL_SUMMARY.json. All inherited test files are unchanged except the exact expected version0.4.0a1→0.5.0a1. Original WP01 and migrations1/2/3 remain unchanged; no new migration.

Actual Qt preview/apply dialogs, facility follow decision, undo/redo, diagnostics, reports, save/reopen and restore were executed on synthetic data. Screenshots include both new review windows and three themes. OUTPUT_SAMPLES/REV_E_STUDY holds final JSON/Excel/Word/PDF/ZIP reports. The normalized JSON retains exact source bytes, review reasons and full calculation/comparison values. Word/PDF were rendered and visually inspected. No engineering detector response/coverage is established.

ORIGINAL_ARCHIVES preserves the original WP01, takeover and all predecessor return ZIPs, including Rev D. SHA256SUMS.txt covers all returned files. SOURCE_FILES.json identifies changes from Rev D. PROJECT_STATE.md/NEXT_WORK_PROMPT.txt specify exactly where to resume. Q1–Q10/F01–F10 remain proposed; no Git, paid/live AI, client data, live engineering integration, publication, sign-off or release occurred.

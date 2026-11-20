# START HERE — Rev H (20 Nov 2026): review fixes F01–F25
DEVELOPMENT / UNVERIFIED. COMPUTED - UNREVIEWED development results - not independently verified.
- Fix register: FIX_DISPOSITION_REV_H.md (also in docs/).
- Method and tolerances: docs/METHOD_AND_TOLERANCES_REV_H.md.
- Limitations: docs/LIMITATIONS_REV_H.md.
- Old vs new wellhead example: docs/WELLHEAD_COMPARISON_REV_G_VS_H.md.
- Evidence: TEST_RESULTS/REV_H/README.md; report renders in screenshots/REV_H/RENDER.
- State and next action: PROJECT_STATE.md and NEXT_WORK_PROMPT.txt.
The Rev F text below is historical.

# Fire & Gas Mapping Engineering System — Rev F
16 November 2026. Version 0.6.0a1. DEVELOPMENT BUILD / UNVERIFIED.

Rev F is a complete source return pack. It is the first revision executed on native Windows. The untouched Rev E suite failed on Windows 11 (98 of 190 errors) because durability flushes used read-only descriptors and SQLite connections were left open; both are fixed and regression-guarded. It does not complete or qualify the WP02–WP12 engineering programme.

Start: read HOW_TO_RUN.md and USER_GUIDE.md, review setup.ps1, install the pinned dependencies in a Python 3.12 environment, then launch run.ps1. Open examples/SYNTHETIC_REV_E_STUDY.fgcase. Executed here: Linux Python 3.12.16 / Qt offscreen, and Windows 11 Pro 10.0.26200 / Python 3.12.10 / PySide6 6.12.0 with the real `windows` Qt platform. No EXE, installer or offline wheelhouse.

Baseline before edits: 753/753 Rev E hashes on both hosts; untouched 190 tests Linux 190/190, Windows 92 PASS / 98 ERROR. Current suite 201 tests (87 unit, 105 integration, 9 acceptance): Linux 201/201; Windows 200/201 (symlink test needs Developer Mode/symlink privilege, which this PC lacks; test not changed). Inherited test edits are limited to closing SQLite connections and the version string. Migrations 1/2/3 and owner manifest unchanged.

Windows evidence: TEST_RESULTS/REV_F_WINDOWS_EVIDENCE (baseline failures, every intermediate run, real-Qt smoke and workflow screenshots/reports, native Excel read-back, mutants, dense benchmark). Checklist status: docs/REV_F_WINDOWS_CHECKLIST.md — automated items only; manual items and Word read-back not completed.

ORIGINAL_ARCHIVES keeps WP01, takeover and Rev B/C/D ZIPs; Rev E is referenced by exact SHA256 (too large for the unchanged pack bounds) and kept beside this ZIP. SHA256SUMS.txt covers all returned files. SOURCE_FILES.json lists changes from Rev E. Q1–Q10/F01–F10 remain proposed. No paid/live AI, client data, live engineering integration, publication, sign-off or release. Git commit/push of Rev F was separately authorised by the owner.

# Rev G deviations and limits (0.7.0a1)
G1. On 18 Nov 2026 the owner approved Q1–Q10/F01–F10 and lifted the synthetic-only, calculation-blocked and no-Git rules; see docs/DECISIONS_REV_A.md. The engineering coverage engine is implemented. Results are engineer-reviewed and not independently certified.
G2. Test files were updated only where they asserted the removed behaviour:
  - test_source_fingerprint now expects version 0.7.0a1.
  - test_wellhead_example still expects the schema-3 case to be BLOCKED. That remains true, because schema 3 is not coverage-enabled.
  - The old refusal tests in test_detection_scenarios and test_study_preparation still pass unchanged: calling the engine without complete inputs is still refused.
G3. Shipped detector library entries are EXAMPLE VALUES (generic, with no manufacturer named). They must be replaced by verified manufacturer data before project use.
G4. Scene and evidence data_class still accept only SYNTHETIC. A PROJECT data class for real facility geometry is not yet implemented (see NEXT_WORK_PROMPT).
G6. No public datasheet values were cited for the starter library; all its values are generic EXAMPLE values (see G3).
G7. The shipped wellhead coverage example is regenerated whenever an implementation file hashed into the run envelope changes. The test test_shipped_example_is_current_with_this_code enforces this.
G8. On Windows, test_symlink_alias_fenced still fails with WinError 1314, because the PC has no symlink privilege. This is the same as in Rev F; the test is unaltered.
G5. No standards conformity is claimed. Limits of the method are listed in docs/REV_G_COVERAGE_METHOD.md §5.

# Rev F deviations and limits
Rev E items below remain in force except where updated here.

F1. Git commit/push of Rev F was separately authorised by the owner (outside this pack); earlier revisions had no Git actions.
F2. Native Windows executed automatically via an owner-approved remote shell; manual Windows items, Word read-back and symlink-privilege tests remain NOT RUN/FAILED as recorded.
F3. Inherited test files changed only to close SQLite connections (identical commit semantics) and the exact version 0.5.0a1→0.6.0a1. No assertion/tolerance/selection change.
F4. Rev E return ZIP is not embedded (118.5 MB exceeds unchanged pack bounds); referenced by SHA256 in ORIGINAL_ARCHIVES/REV_E_PREDECESSOR_REFERENCE.json and preserved beside the return.
F5. rev_f_mutations.py forbids collateral ERRORs on POSIX only; on Windows the real defects also break fixtures, so >=1 assertion FAIL is required and ERRORs are recorded.

# Rev E deviations and limits (inherited)
Earlier deviations are preserved in docs/REV_D_BASELINE and predecessor archives. No new owner approvals are inferred.

1. Runnable source checkpoint only; no Git/repository changes, EXE/installer/signing or offline wheelhouse. Dependencies must be installed from pinned requirements through an authorised source.
2. Linux Qt offscreen executed; Windows11/native Qt/Win32/NTFS/Office/DPI/Job Objects/cloud-sync acceptance NOT RUN.
3. Bulk import bounded to synthetic literal CSV/XLSX detectors/equipment with existing synthetic evidence; zones/richer structured fields unresolved. Commit rebuilds on UI-owning thread after worker preview; larger dense projects need performance checks.
4. Revision follow means explicitly reusing a declared source-frame anchor, not inferred mesh-surface correspondence. Unit changes/stale prior mounts/missing references refuse apply. Rich metadata/parent/evidence reconciliation remains open.
5. Broadphase retains an unfiltered reference and uncertainty rules; sparse benchmark is one observation, not a qualified geometry/physical detector response claim.
6. Full source/preparation reviews are retained after undo; report history explicitly does not imply changes remain applied. Parser/render QA is not native Office or engineering acceptance.
7. Six new fault tests exercise the existing recovery implementation; no blanket crash-safety claim. Late cancellation/post-install error can leave a valid new copy requiring inspection.
8. Only inherited exact-version expectation0.4→0.5 updated; criteria/tolerances not weakened. Initial new test/helper fixture errors and corrected rerun evidence retained.
9. Preserved Rev D ZIP is larger than the ordinary pack file bound. One exact-path/SHA-pinned exception up to64MB preserves it; other file/runtime import bounds unchanged.
10. No actual manufacturer data/standard clauses/criteria/frequencies/sign-offs invented. No live/paid AI, client processing, live external engineering integration, publication, qualification or release. Entire WP02–WP12 remains unaccepted.

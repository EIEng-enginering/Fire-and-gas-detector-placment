# Rev F traceability
| Area | Implementation | Evidence | Open acceptance |
|---|---|---|---|
| Windows durability flush | services/case.py fsync_file; case.py/recovery.py call sites | Windows suite 200/201; test_windows_portability_rev_f; mutant fsync-read-only-descriptor caught (Linux, Windows) | Real power-loss/crash behaviour not tested |
| SQLite handle release | closing() in recovery, geometry, study_schema, preparation_job; inherited tests; build_return_pack | handle-release tests (Linux /proc, Windows rename probe); 2 connection-leak mutants caught | Long-running UI sessions/AV/OneDrive locking not tested |
| Native Windows checklist | tools/windows_acceptance.ps1, windows_smoke.py, rev_e_workflow.py on real Qt | REV_F_WINDOWS_EVIDENCE; docs/REV_F_WINDOWS_CHECKLIST.md | Manual items, symlink privilege, Word read-back |
| Dense-scene independent benchmark | tools/rev_f_dense_benchmark.py; test_dense_scene_rev_f | REV_F_DENSE_BENCHMARK_{linux,win32}.json | Industrial CAD/solids, physics |
| Native Excel literal text | tools/rev_f_literal_report.py, rev_f_office_check.ps1 | WIN_OFFICE_LITERAL_CHECK | Human visual Office review |

201 passing tests on Linux and 200/201 on Windows are software evidence only, not WP02–WP12 or engineering acceptance.

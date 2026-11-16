# Rev D traceability
| Approved direction | Implemented source | Executable evidence | Remaining acceptance |
|---|---|---|---|
| Explicit placement | domain/mounting.py; services/mounts.py; workspace.py; study_dialogs.py | test_mounting_pose; test_study_preparation; rev_d_workflow | CAD/source reconciliation; Windows UX; engineering mounting review |
| Geometry diagnostics | engine/inspection.py; services/geometry_inspection.py; viewer overlay | test_target_inspection; test_geometry_inspection_worker; rev_d_numerical_benchmarks | Arbitrary industrial geometry, acceleration, self-intersections; physical methods |
| Structured basis/readiness | domain/study_basis.py; services/basis.py; migration0003 | test_study_preparation; schema3 workflow/reports | Owner criteria and method-specific completeness/independent review |
| Reporting/comparison | services/reporting.py; comparison.py | test_schema3_reports; test_long_evidence_report; test_snapshot_revision; rendered exports | Native Office, large project templates, approved study interpretation |
| Recovery/Windows tooling | recovery.py; process_inspection.py; case.py; windows_smoke.py | test_backup_restore; test_process_inspection; Qt restore workflow | Native Windows, crash/NTFS, Job Objects, cloud-sync semantics |
| Manufacturer preparation | domain/performance.py; services/performance.py; basis.py | test_performance_preparation; test_study_preparation; schema3 workflow | Authorised real data, legitimate detector response engine and engineering verification |

Test-suite counts do not confer work-package acceptance. All new engineering methods remain UNVERIFIED. Historical Rev B/C traceability is retained. Original owner requirements/risks/decisions remain in docs and ORIGINAL_ARCHIVES.

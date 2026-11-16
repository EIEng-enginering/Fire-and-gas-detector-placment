# Rev E traceability
| Development area | Main implementation | Evidence | Open acceptance |
|---|---|---|---|
| Bulk register import | services/bulk_import.py, preparation.py, preparation_job.py, ui/preparation_dialogs.py | test_preparation_imports; test_preparation_reports_rev_e; actual Qt preview | Zones/richer fields; dense-case timings; native Windows |
| Revision reconciliation | services/reconciliation.py and preparation UI | explicit follow/detach/missing decision/unit/reference/undo tests; actual Qt review | Source metadata/anchor redeclaration/surface correspondence |
| Geometry verification | independent slab/rotated-union constructive oracles | test_scene_broadphase and benchmark; three deliberate mutants caught | Wider/dense industrial geometry/physical qualification |
| Performance | engine/spatial.py; inspection.py | indexed vs unfiltered complete equality; measured sparse scene | General performance/Windows guarantees absent |
| Reports | reporting.py | all-format parser QA; source bytes; literal-cell test; renders | Native Office/full production templates |
| Recovery | inherited recovery engine, new fault suite | six test_recovery_faults_rev_e tests | Actual Windows/NTFS/crash acceptance |

190 passing software tests are not work-package or independent engineering acceptance. Prior traceability and unchanged owner requirements remain in docs/original archives.

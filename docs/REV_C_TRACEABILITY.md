# Rev C executable traceability
| Requirement | Source | Evidence |
|---|---|---|
| Virtual detectors and numeric sort | ui/worksheet.py, register_model.py | integration/test_virtual_grid.py; tools/virtual_detector_benchmark.py |
| Typed detector/equipment/zone forms | ui/main.py, services/workspace.py | tools/rev_c_workflow.py actual Qt forms; integration/test_workspace.py |
| Atomic evidence/detector creation | workspace.detector_command | duplicate/no-orphan and actor rollback tests |
| Multirow paste with stable IDs | services/paste.py; workspace.paste_detectors | unit/test_paste.py, workspace atomic and linked-marker tests; actual preview/apply UI |
| Persisted generic undo/redo | workspace.history | reopen, redo invalidation, conflicting-edit refusal, record remove and marker restoration tests |
| Reviewed geometry append/replace | services/import_review.py | integration/test_import_review.py; raw-source mismatch and orphan-link finding |
| Source evidence/findings | services/findings.py | import tests; report exact row comparisons; evidence inspector |
| Writer lock across runtimes | services/file_lock.py, case.py | integration/test_case_hardening.py and writer-fence mutation |
| Interrupted save reconciliation | services/case.py | injected pre/post-replace failures and forced process kill |
| Source fingerprints on new runs | services/calculations.py | integration/test_source_fingerprint.py |
| Concentration/time field interpolation | engine/concentration.py | unit/test_concentration_field.py affine analytic oracle |
| Concentration path convergence | engine/concentration.py | tools/field_convergence.py exact triangle+rectangle integral |
| Orientation convention | domain/pose.py | unit/test_pose.py independent known axes |
| Cancellable five-format report job | services/report_job.py | acceptance/test_rev_c_workflow_service.py; actual UI export |
| Real Windows platform gate | tools/windows_smoke.py/windows_acceptance.ps1 | SUPPLIED / NOT EXECUTED; Linux offscreen cannot pass |

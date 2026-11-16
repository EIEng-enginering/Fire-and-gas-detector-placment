# Requirement to evidence traceability - Rev A

| Requirement | Current implementation | Test/evidence | Status |
|---|---|---|---|
| ST-01 Python 3.12/PySide6 6.12 | pinned requirements and UI entrypoint | Windows execution pending | DONE NOT VERIFIED ON WINDOWS |
| ST-02 One portable case | case.create_case SQLite schema 1 | integration.test_create_edit_save_reopen | DONE AND TESTED IN LINUX |
| ST-03 Atomic save and conflict detection | CaseSession.save | integration.test_save_conflict_refuses_silent_overwrite | DONE AND TESTED IN LINUX |
| ST-04 Single writer | CaseSession lock | integration.test_lock_refuses_second_writer | DONE AND TESTED IN LINUX |
| ST-05 Explicit recovery | working local session | integration.test_crash_recovery_explicit | DONE AND TESTED IN LINUX |
| ST-06 Immutable ledger and compensating commands | name change, detector add, evidence add; name undo | integration.test_undo_is_compensating_event | PARTIAL |
| ST-07 Evidence-linked detector | evidence foreign key | integration.test_evidence_mandatory_and_synthetic | DONE AND TESTED IN LINUX |
| ST-08 Three matching themes | theme.py | unit.test_colour_contrast | TOKENS TESTED, QT SCREENSHOTS PENDING |
| ST-09 Deterministic geometry teaching example | geometry.py | unit.test_geometry, independent oracle | PROTOTYPE ONLY, NOT F&G VERIFIED |
| ST-10 No silent AI transfer | no AI gateway installed | inspect source; no outbound calls | IN M0 ONLY |
| ST-11 GUI launched on Windows | ui/main.py | none yet | NOT DONE |
| ST-12 Full 3D CAD and detector study | future engine/GUI | none | NOT DONE |
| ST-13 Controlled Excel/Word/PDF/JSON/ZIP exports | snapshot() + synthetic JSON demo only | acceptance.test_end_to_end_no_real_data | PARTIAL |
| ST-14 Full independent engineering method validation | reserved future gate | none | NOT DONE |

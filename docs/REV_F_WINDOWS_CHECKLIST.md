# Rev F native Windows checklist — PARTIALLY RUN (automated items only)
Host: DESKTOP-MHQKA03, Windows 11 Pro 10.0.26200, Python 3.12.10 (64-bit) venv with pinned PySide6 6.12.0 / openpyxl 3.1.5 / python-docx 1.2.0 / reportlab 4.4.9 / pypdf 6.21.4, NTFS temp volume, Microsoft 365 Office 16.0.20527.20196, interactive console session. Developer Mode OFF; no symlink privilege. Working copies were local (C:\Users\Admin\fg_dev), not the OneDrive folder.

| Item (REV_E/REV_D checklist) | Result | Evidence (TEST_RESULTS/REV_F_WINDOWS_EVIDENCE) |
|---|---|---|
| Verify Rev E hashes on Windows | PASS 753/753 | 00_REV_E_HASH_VERIFY_WINDOWS.txt |
| Untouched Rev E suite on Windows | FAIL: 98 errors / 190 (97 tracebacks end in fsync EBADF from create_case; WinError 32 temp-cleanup errors also present). Symlink privilege failure surfaced only after these were fixed | 01_REV_E_UNTOUCHED_BASELINE_* |
| Rev F suite on Windows | 200/201 PASS; 1 ERROR symlink privilege | 04_*, 05_* |
| tools/windows_acceptance.ps1 | RAN; stopped after suites because of the symlink failure (by design) | 05_*, 05b_WINDOWS_* |
| tools/windows_smoke.py (real Qt `windows` platform) | PASS; process probe ALIVE; 3 themes captured | REV_F_WINDOWS_QT_SMOKE* |
| Case-menu bulk CSV/XLSX preview/apply, revision follow/detach, undo/redo/save/reopen, restore worker (automated Qt driver, real Windows platform) | PASS (automated, not manual) | 06_REAL_QT_WORKFLOW |
| Import workers never share live SQLite connections | Snapshot connection now closed before the worker starts; handle test PASS on Windows | test_windows_portability_rev_f |
| 2000-row preview | PASS 1.85 s, case unchanged (tool label still says "Linux; Windows NOT RUN" — hard-coded Rev E text; this run was on Windows) | REV_F_WINDOWS_REV_E_BENCHMARK_RERUN.txt |
| Dense scene processing | PASS vs independent oracle | REV_F_DENSE_BENCHMARK_win32.json |
| Excel literal '=' text in native Excel | PASS (automated COM read-back, 0 formulas) | WIN_OFFICE_LITERAL_CHECK, WIN_OFFICE_CHECK |
| Word read-back / PDF in native viewer | NOT COMPLETED — Word COM hung invisibly; killed after 120 s | — |
| Recovery faults, hard-link alias refusal, interrupted save (automated suites on NTFS) | PASS | 04_*, 05_* |
| Symlink alias fence | FAIL — privilege not held (prerequisite) | 05_* |
| DPI / multi-monitor / keyboard-only / human visual Office-PDF inspection / human cancellation | NOT RUN | — |
| Late cancellation leaving installed copy | Not exercised manually | — |

Observation from the real-Qt screenshots: at the default window size the register header "X (m" and component IDs ("DEC…", "V10…") are truncated; layout review is open.

Installer/EXE/offline wheelhouse, Job Objects, cloud-sync/multi-host semantics, physical methods and independent engineering qualification remain separate unresolved gates. Automated evidence does not equal manual Windows acceptance.

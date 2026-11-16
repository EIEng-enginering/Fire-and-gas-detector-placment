# Project state — Rev F checkpoint
16 November 2026 (AWST, UTC+8). v0.6.0a1. DEVELOPMENT BUILD / UNVERIFIED.

## Current implementation
Rev F is the first native Windows execution and Windows portability revision. Starting from the preserved Rev E ZIP (SHA256 7d56b4b2…cdf732e8), all 753 Rev E hashes verified on the Linux box and on Windows, and the untouched 190-test suite was rerun on both before edits: Linux 190/190 PASS; native Windows 11 / Python 3.12.10 / PySide6 6.12.0 **98 of 190 ERROR** (fsync on read-only descriptors; unclosed SQLite connections locking files). Rev E had never actually run on Windows.

Fixes: write-capable `fsync_file()` for all durability flushes; `contextlib.closing` for every SQLite connection opened with a context manager in src, three inherited test files and the pack builder. New: 10 Windows-portability regression tests (Windows semantics emulated on POSIX, native on Windows), 3 deliberate mutants (caught on Linux and Windows), dense-lattice broadphase benchmark against the independent oracle (+1 acceptance test), native Excel literal-text read-back tooling. Engine/geometry/calculation code, migrations, owner manifest and tolerances unchanged.

Current suite: 201 tests (87 unit / 105 integration / 9 acceptance). Linux: 201/201 PASS. Windows: 200/201 — `test_symlink_alias_fenced` fails with WinError 1314 because this PC has no Developer Mode/symlink privilege; the test was not altered or skipped. Real-Qt (`windows` platform) smoke and the Rev E integrated Qt workflow passed on Windows; native Excel showed literal `=` text and zero formulas. Word COM read-back hung and was not completed. Manual Windows items (keyboard, DPI/multi-monitor, human visual Office/PDF review, human cancellation/file-lock scenarios) were not performed. See TEST_RESULTS/REV_F_FINAL_SUMMARY.json and docs/REV_F_WINDOWS_CHECKLIST.md.

## Logical stopping point
Windows portability defects found by the first native run are fixed and regression-guarded. Engineering calculation stays BLOCKED. Not WP02–WP12 acceptance, qualification or release.

## Exact next action
Verify SHA256SUMS.txt; rerun tools/run_tests.py unchanged on Linux and Windows. On Windows, enable Developer Mode (or grant SeCreateSymbolicLinkPrivilege) under organisation policy and rerun tools/windows_acceptance.ps1 to clear the symlink prerequisite without changing the test. Diagnose the Word COM hang with Word visible (or inspect Study.docx/PDF manually in Word/Acrobat). Perform the manual checklist items in docs/REV_F_WINDOWS_CHECKLIST.md. Review register/component column truncation seen in real-Qt screenshots. Then the independent follow-on: richer preparation templates/zone import and source metadata, explicit anchor redeclaration review, report histories/dependency graph, parser hardening. Review Q1–Q10/F01–F10 before treating any as approved.

Engineering response/coverage/optimisation acceptance, real manufacturer data, live AI/integrations, independent WP12 qualification and release remain blocked pending legitimate method/data/permissions and owner review. Git commit/push of this revision was separately authorised by the owner; no publication, release, client processing or engineering sign-off is authorised.

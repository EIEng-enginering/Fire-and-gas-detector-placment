# Development report — Rev F
16 November 2026. v0.6.0a1. DEVELOPMENT BUILD / UNVERIFIED.

Done and verified: native Windows execution of the Rev E checkpoint; diagnosis and fix of two Windows portability defects (read-only fsync EBADF; unclosed SQLite connections causing WinError 32); 10 new regression tests that emulate Windows semantics on Linux; 3 deliberate mutants caught on both hosts; dense-lattice broadphase vs independent oracle (216 boxes, 576 rays, 0 mismatches); native Excel literal-text read-back; real Windows Qt smoke and integrated workflow.

Results: Linux 201/201. Windows 200/201 (symlink privilege prerequisite). Dense benchmark Linux 0.615 s→0.088 s, Windows 1.757 s→0.253 s (124,416→556 mesh queries); 2000-row preview Windows 1.85 s. Single observations, not guarantees.

Not done: Word read-back (COM hung), manual Windows checklist items, symlink privilege setup, installer/EXE, qualified detector response/coverage, industrial CAD qualification, WP02–WP12 acceptance, independent engineering qualification or release. Engineering calculation remains BLOCKED. See docs/REV_F_IMPLEMENTATION.md and TEST_RESULTS/REV_F_FAILURES_AND_FIXES.json.

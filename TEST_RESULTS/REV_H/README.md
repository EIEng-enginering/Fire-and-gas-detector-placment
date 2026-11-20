# Rev H evidence index (20 Nov 2026, AWST)
DEVELOPMENT / UNVERIFIED. COMPUTED - UNREVIEWED development results - not independently verified.

| Folder | Content | Result |
|---|---|---|
| 00_BASELINE_UNTOUCHED_LINUX | Rev G suite before any edit (ENV.txt: Python 3.12.16, PySide6 6.12.0, openpyxl 3.1.5, reportlab 4.4.9, pypdf 6.21.4, Pillow 13.0.0, python-docx 1.2.0) | 250/250 (115 unit, 126 integration, 9 acceptance) |
| 01_REVIEW_PROBES_BEFORE | the reviewer's probes on untouched Rev G | reproduce F01–F08, F10, F11, F13, F18, F24 |
| 02_REVIEW_PROBES_AFTER | the same probes on Rev H (adapted copies record the only changes: no IMPLEMENTATION tuple; refusals caught), plus an independent eligible-volume check | every reproduced defect is now absent or refused (see below) |
| 03_FULL_SUITE_LINUX_AFTER_FIXES | tools/run_tests.py on Rev H | 296/296 (140 unit, 147 integration, 9 acceptance) |
| 04_WELLHEAD | Rev G summary, Rev H options at 1.0 m, build logs | see docs/WELLHEAD_COMPARISON_REV_G_VS_H.md |
| 05_BENCHMARK | same-host timing and memory | Rev G 152.0 s vs Rev H 178.8 s |
| 06_CONSISTENCY | SQLite/JSON/XLSX/DOCX/PDF/PNG/manifest/README/USER_GUIDE audit (tools/rev_h_consistency_check.py) | all 12 checks pass |
| WINDOWS_REV_H | Windows 11 run of the same suite | Windows 11 Pro 10.0.26200, Python 3.12.10, PySide6 6.12.0: 295/296 (140 unit, 146/147 integration, 9 acceptance); the only failure is the known test_symlink_alias_fenced (WinError 1314, no symlink privilege; test unaltered). Evidence: TEST_RESULTS/REV_H/WINDOWS_REV_H |

Probe after-values:
- partial slab eligible 0.8 / obstruction 0.2;
- shared-edge inside = S;
- prism point not excluded;
- roll 30° accepted;
- standoff wall 1ooN 0;
- scene/mesh epsilon agree;
- sector 0.28 m → UNRESOLVED FEATURE;
- empty zone → NOT EVALUABLE;
- study modules fingerprinted, and an injected study fault → STALE;
- sensitivity in envelope;
- no formula cells;
- ../escaped refused with sibling intact;
- heptane/100 kW vs methane/400 kW refused by the direct engine;
- NaN scenario location refused.

Independent eligible-volume check: six zones, slab-sweep exact Fractions without fgmapping, |diff| ≤ 5.7e-14 m³.

Render evidence: screenshots/REV_H/RENDER (LibreOffice → PDF → PNG at 70 dpi: DOCX 22 pages, PDF 21, XLSX 15).

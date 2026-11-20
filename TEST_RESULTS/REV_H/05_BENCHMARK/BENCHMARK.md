# Same-host benchmark: wellhead coverage example, Rev G vs Rev H

Host: box, Linux 6.12, 8 vCPU Intel Xeon, Python 3.12.16. Both runs use the same scene and inputs:
`tools/build_wellhead_coverage_example.py OUT --grid 0.5 --refine 2`. The figure is the builder's "runs X s" line: wall time for all coverage runs, scenario and options.

| Run | Conditions | Rev G | Rev H |
|---|---|---|---|
| 2 (headline) | sequential, box otherwise idle | 152.0 s | 178.8 s |
| 1 | Rev G concurrent with other work / Rev H alone | 156.9 s | 177.8 s |
| 3/4 | memory runs (Rev G concurrent with test suite) | 156.8 s wall (process), 158.3 MB max RSS | 185.4 s wall (process), 410.4 MB max RSS |

- Sample counts are identical (sample_count per zone): FZ-MANIFOLD 2574, FZ-WELLBAY 11178, FZ-WIRELINE 1320, GZ-MANIFOLD 2574, GZ-MODULE 43200, GZ-WELLBAY 11178.
- Rev H is about 18 % slower and uses about 2.6× peak memory. The causes are the exact cell-measure work and the per-row cell bounds and scene snapshot stored for F09/F20. No speed improvement is claimed.
- Rev H's options study runs at 0.5 m; Rev G's ran at 1.0 m. This is included in the totals.

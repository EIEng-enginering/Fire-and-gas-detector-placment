# Example: SYNTHETIC offshore wellhead module WHM-01 (3D)

> **SYNTHETIC / ILLUSTRATIVE ONLY.** This module is not a real facility or a design, and it does not use client data. It makes no engineering claim. The geometry and the candidate detector locations are study-setup inputs only. Nothing in this example infers surface mounting, detector field of view, detector response or coverage. Engineering calculation stays **BLOCKED** and qualification stays **UNVERIFIED**.

## Files

| Path | What it is |
|---|---|
| `examples/SYNTHETIC_WELLHEAD_MODULE.fgcase` | Saved example case (schema 3: geometry plus study). Open it in the app. |
| `examples/wellhead/SYNTHETIC_WELLHEAD_GEOMETRY.json` | Explicit scene JSON (`Scene.from_dict`): frame `WHM_LOCAL`, 116 box components |
| `examples/wellhead/SYNTHETIC_WELLHEAD_REGISTER.csv` | Bulk register template that was imported: 23 candidate detectors and 17 equipment records |
| `examples/wellhead/SYNTHETIC_WELLHEAD_REGISTER.xlsx` | The same rows in the app's XLSX template (single sheet `Registers`, no formulas) |
| `examples/wellhead/SYNTHETIC_WELLHEAD_ZONES.json` | 3 fire zones and 3 gas zones (axis-aligned boxes, m) |
| `examples/wellhead/SYNTHETIC_WELLHEAD_BASIS.json` | Study basis (`fg-study-basis/1`); every criterion is `NOT SUPPLIED` |
| `examples/wellhead/BUILD_SUMMARY.json` | Generator output: counts, scene SHA-256 and readiness |
| `tools/build_wellhead_example.py` | Reproducible generator |
| `tools/render_wellhead_preview.py` | Matplotlib isometric/plan preview. This is a tool-only dependency; the app does not depend on matplotlib. |
| `tools/capture_wellhead_app.py` | Opens a temporary copy in the real `MainWindow` and saves screenshots |
| `screenshots/WELLHEAD_MODULE_{ISO,ISO_CUTAWAY,ISO_NW,PLAN}.png` | Matplotlib previews |
| `screenshots/WELLHEAD_APP_*.png` | Screenshots of the actual application window (Linux offscreen and Windows) |
| `tests/integration/test_wellhead_example.py` | Rebuilds the example and checks it opens and validates. It also checks the shipped case matches a fresh build. |

## Layout and levels (local frame `WHM_LOCAL`, metres, Z up)

- **Footprint:** 30 m (X, east) × 20 m (Y, north). The module is open on the south and east sides, with handrail envelopes `HR-SOUTH` and `HR-EAST`.
- **Blast/fire walls:** `BW-NORTH` and `BW-WEST` are full height, 0.3 m thick. Their rating is NOT SUPPLIED.
- **Levels:**
  - Cellar deck plate top of steel: local Z 0.0.
  - Wellhead/mezzanine grating: +4.5. There are three strips over the well rows (`MZ-GRATE-1..3`) and a walkway to the manifold (`MZ-GRATE-4`).
  - Upper deck plate underside: +9.0. The plates `UD-PLATE-S/N/W/E` leave a hatch over the wellbay.
  - The narrative datum maps local 0.0 to EL +24.0 m LAT (illustrative only). Wellhead deck ≈ EL +28.5 and upper deck ≈ EL +33.0.
- **Structure:**
  - 8 main columns `COL-A1..D2`, 0.6 m box envelopes.
  - Primary beams `BM-S` and `BM-N`, transverse beams `BM-TA..TD`, and mezzanine beams `BM-MZ-W/E`.
  - Stairs `ST-MZ` (cellar to mezzanine) and `ST-UD` (mezzanine to upper deck).
- **Wellbay:** 8 slots, W01–W08, at X = 9, 12, 15, 18 and Y = 7 (south row) and 12 (north row). Each slot has:
  - wellhead body `Wnn-WH`, Xmas tree `Wnn-XT` and tree cap `Wnn-CAP`
  - production wing valve `Wnn-WV` and choke `Wnn-CH`
  - flowline riser `Wnn-FL-R`, horizontal run `Wnn-FL-H` and drop leg `Wnn-DROP`
  - manifold diverter valve `Wnn-MV`
- **Manifold area (east):**
  - production/test manifold skid `MF-SKID`
  - production header `HDR-PROD` and test header `HDR-TEST`
  - outlets `HDR-EXPORT` (to process) and `TS-INLET` (to the test separator, off-module)
- **Wireline/intervention area (west):**
  - wireline unit `WL-UNIT` and power pack/cabin `WL-PCE`
  - lubricator/PCE envelope `WL-LUB` above W01, temporary
  - laydown area marker `WL-LAYDOWN`
- **Escape routes:** markers `ER-SOUTH` and `ER-EAST` (primary, 1.2 m), `ER-WELLBAY` (between the well rows) and `ER-MZ` (mezzanine). These markers and `WL-LAYDOWN` are thin, `NON_OBSTRUCTING_ANNOTATION` components. They are listed in the basis `exclusions`.

**Component counts by semantic (116 in total):** EQUIPMENT 52, PIPE 28, STRUCTURE 20, DECK 5, GRATING 4, ESCAPE_ROUTE 4, WALL 2, AREA_MARKER 1. Every mesh is closed and manifold. The evidence ID on every component is `SYN-WHM-GEOM-01` (SYNTHETIC).

## Candidate detectors (CANDIDATE register records only)

These positions are illustrative candidate anchors. They are not a layout recommendation.

| Type | Count | Tags and illustrative intent |
|---|---|---|
| FLAME | 8 | `FD-101..104` at the module corners at +7.5, aimed inward. `FD-105/106` on the south/north edges at +8.0. `FD-107` on the wireline side and `FD-108` on the manifold side, at about 4 m. |
| POINT_GAS | 12 | `GD-101..106` at the well rows, near the cellar deck (+0.6). `GD-107..109` at the manifold. `GD-110` at the wireline unit. `GD-111/112` at mezzanine level (+5.0). |
| OPEN_PATH | 3 | `GD-OP-01` (south edge), `GD-OP-02` (east edge) and `GD-OP-03` (between the well rows). Each transmitter has a paired receiver *position* recorded as an EQUIPMENT record `GD-OP-0n-RX`. |

**Equipment records (17):**
- `EQ-W01..W08` and `EQ-MF`
- `EQ-HDR-PROD` and `EQ-HDR-TEST`
- `EQ-WL-UNIT`, `EQ-WL-PCE` and `EQ-WL-LUB`
- 3 open-path receiver records

Each record links to its geometry component.

**Zones:**
- Fire zones: `FZ-WELLBAY`, `FZ-MANIFOLD`, `FZ-WIRELINE`
- Gas zones: `GZ-WELLBAY`, `GZ-MANIFOLD`, `GZ-MODULE`

All zones are AABB, in m.

**Not created:** no detector mounts (`set_mount`), performance datasets or links, fuels, criteria, targets or calculation runs.

## Readiness: deliberately BLOCKED

`readiness()` reports:
- `input_status = BLOCKED`
- `engineering_calculation_status = BLOCKED`
- `qualification = UNVERIFIED`

The input status is BLOCKED because these items are missing:
- criterion reference
- fuel/gas
- targets
- a performance dataset for each detector

The mixed BOTH study also raises `MIXED_STUDY_REQUIRES_SEPARATE_METHOD_BASES`. This is the honest state for an illustrative layout and should not be "fixed" with invented data.

## How it was built (reproducible, via the application's own service paths)

```
PYTHONPATH=src:. python -B tools/build_wellhead_example.py --inputs examples/wellhead --case examples/SYNTHETIC_WELLHEAD_MODULE.fgcase
```

The generator first writes the input files. It then builds the case **from those files** in a temporary folder, in this order:
1. Evidence: `add_evidence`
2. Geometry: `Scene.from_dict` → `geometry.set_scene`
3. Registers: `bulk_import.prepare_bulk(CSV)` → `preparation.apply_plan`, with a recorded reviewer and reason
4. Zones: `workspace.record_command`
5. Basis: `basis.set_basis`

It asserts that engineering stays BLOCKED, saves, and copies the case out. Existing destinations are refused. No database rows are written by hand.

The scene SHA-256 is `ef65fc6ffff64a48ede8c34f30118a08a66c436c76794e9dda9f2de1c33453c2`.

**Previews:**
```
python -B tools/render_wellhead_preview.py examples/SYNTHETIC_WELLHEAD_MODULE.fgcase OUT_PREFIX
python -B tools/capture_wellhead_app.py examples/SYNTHETIC_WELLHEAD_MODULE.fgcase OUT_PREFIX
```

## How to open it in the app

1. Copy `examples/SYNTHETIC_WELLHEAD_MODULE.fgcase` somewhere writable. Keep the shipped file as the reference.
2. Start the app with `run.ps1` on Windows (see HOW_TO_RUN.md) or `python -B -m fgmapping` with `src` on PYTHONPATH.
3. Choose **Case → Open case** and select the copy.
4. Click **Fit**, then **Isometric** or **Top**.
5. The component list lets you untick `UD-*` and `BM-*` to see into the wellbay.
6. The register tabs show the detectors, equipment, fire zones and gas zones.
7. Choose **Study preparation → Input readiness and engineering blockers** to see the readiness report (BLOCKED).

## Limits of what the program represents (by design, or not yet implemented)

- **Geometry:** axis-aligned closed box envelopes only. There is no CAD import of curved or cylindrical pipe, no insulation or flange detail, and no real tree models. Pipes and valves are box envelopes.
- **Open-path detectors:** recorded as a transmitter position plus orientation. No receiver or beam entity exists, so receivers are EQUIPMENT records and the beam path is not modelled. The preview's dotted line is a pairing visual only.
- **Bulk-imported detectors:** they carry no detector display geometry. The viewer shows them as placement and orientation annotations only.
- **Escape routes and laydown:** these are annotation markers. The program has no egress or route-analysis model.
- **Zones:** axis-aligned boxes only.
- **Study basis:** one basis per case, so a mixed fire and gas study is blocked until separate method bases exist.
- **Viewer grid:** in Rev F the grid was fixed at about X −5..25 and Y −5..20. From Rev G the grid is sized to the model on Fit.
- **Coverage:** no detector response, field of view, obstruction or coverage is computed or implied anywhere. Engineering calculation is BLOCKED.


## Rev G coverage applied to the wellhead example (EXAMPLE VALUES – illustrative only, not for design)

The case is `examples/wellhead_coverage/SYNTHETIC_WELLHEAD_COVERAGE.fgcase`. It was generated from the base case by `tools/build_wellhead_coverage_example.py --grid 0.5 --refine 2`. The generator:

- enables schema 4;
- imports the EXAMPLE starter library;
- explicitly assigns all 23 detectors:
  - 8 flame detectors to `EX-FLAME-IR3-METHANE`;
  - 12 point gas detectors to `EX-GAS-IR-POINT-METHANE`;
  - 3 open-path detectors to `EX-GAS-OPGD-METHANE`, with receivers GD-OP-0n-RX;
- fills the basis references;
- writes per-zone setups:
  - flame: 450 kW methane point target, 0.05 m standoff;
  - gas: 5 m spherical cloud at 100 %LEL;
  - both: 2ooN voting and EXAMPLE user targets of 1ooN 0.90 and 2ooN 0.80;
- runs all six zones, a scenario set and a layout-options study;
- exports the report `WELLHEAD_COVERAGE_REPORT/`.

| Zone | Method | Eligible m³ | 0ooN | 1ooN | 2ooN | Target 1ooN / 2ooN | Convergence (0.5 m vs 0.25 m) |
|---|---|---|---|---|---|---|---|
| FZ-MANIFOLD | FG-FLAME-GEO/1.0 | 271.7 | 0.7 % | 99.3 % | 79.2 % | MEETS USER TARGET / BELOW USER TARGET | CONVERGED |
| FZ-WELLBAY | FG-FLAME-GEO/1.0 | 1338.6 | 6.5 % | 93.5 % | 85.9 % | MEETS USER TARGET / MEETS USER TARGET | CONVERGED |
| FZ-WIRELINE | FG-FLAME-GEO/1.0 | 123.1 | 0.2 % | 99.8 % | 86.5 % | MEETS USER TARGET / MEETS USER TARGET | CONVERGED |
| GZ-MANIFOLD | FG-GAS-GEO/1.0 | 271.7 | 70.4 % | 29.6 % | 0.6 % | BELOW USER TARGET / BELOW USER TARGET | CONVERGED |
| GZ-MODULE | FG-GAS-GEO/1.0 | 5023.6 | 84.8 % | 15.2 % | 2.0 % | BELOW USER TARGET / BELOW USER TARGET | CONVERGED |
| GZ-WELLBAY | FG-GAS-GEO/1.0 | 1338.6 | 63.8 % | 36.2 % | 4.7 % | BELOW USER TARGET / BELOW USER TARGET | CONVERGED |

- **Scenario study WHM-SCN-A** uses 19 EXAMPLE scenarios with illustrative frequencies. The frequency-weighted detected fraction is 0.242. Small wellbay gas leaks get only one vote against the 2ooN requirement, and the wireline fire point gets one vote.
- **Layout options WHM-OPT-A (FZ-MANIFOLD, 2ooN, existing layout credited):** the existing layout gives 0.753. Adding CAND-MF-1 gives 0.906 (cost 1), and adding CAND-MF-1 plus CAND-MF-3 gives 0.974 (cost 2). These are proposals only, and the baseline is unchanged.
- **Finding:** the GD-OP-01 beam is obstructed by stair tower ST-MZ, and the GD-OP-02 beam by ST-UD. Both detectors are treated as inoperative, with a BLOCKING finding. Relocate them before relying on open-path coverage.
- **Gas coverage is low** because of this layout's spacing compared with a 5 m cloud under 2ooN voting. This is an illustrative result of EXAMPLE inputs.

Screenshots are in `screenshots/REV_G/` (BOX_OFFSCREEN_*, and WINDOWS_REAL/WIN_REAL_* from the real Windows Qt platform). The Rev F statement "no coverage is computed" applies only to the schema-3 base case.

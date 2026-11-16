# Design issues, trade-offs, and quality gates - Revision A
All findings are actionable engineering/software design checks. Status: OPEN unless 'CURRENT CONTROL' is stated.

| Issue | Severity | Risk / challenge | Proposed control and acceptance evidence |
|---|---|---|---|
| DI-001 | Critical | Simplistic cone mistaken for qualified flame detection | Clearly mark prototype and block production result; manufacturer target response required |
| DI-002 | Critical | Mapping fire target as a point can over/underestimate coverage | Implement finite fire area and angular response; compare with independently calculated cases |
| DI-003 | Critical | Detector FOV depends on fuel, sensitivity, fire size, revision | Source-referenced curves, versioning, strict no-data error |
| DI-004 | Critical | Arbitrary mapping acceptance percentages | Require explicit project performance criteria and sign-off |
| DI-005 | Critical | Geometry units and coordinate transformations incorrect | Unit/datum/transform register, physical landmark cross-check, synthetic coordinate tests |
| DI-006 | High | CAD mesh missing faces or internal equipment | Geometry QA checks, manual review and accepted exclusions |
| DI-007 | High | Scenery visualization mistaken for numerical visibility | Distinct qualified algorithm and visually independent geometric tests |
| DI-008 | High | Occlusion tolerance/grazing intersection causes unstable results | Published boundary convention, precision tests, mesh convergence |
| DI-009 | High | Transparent/partially opaque materials modeled as solid | Engineering classification + explicit detector wavelength applicability |
| DI-010 | High | Detector physical mounting feasibility overlooked | Candidate mounting, access, maintenance and cable routing constraints |
| DI-011 | Critical | Point gas modeled with simple arbitrary radius | Only use project-approved design cloud models or validated concentration results |
| DI-012 | High | Open-path response improperly modelled | Integrate concentration along beam, detector-specific units and thresholds |
| DI-013 | High | Acoustic gas detection approximated using optical coverage | Separate sensor physics; not in initial scope |
| DI-014 | Critical | Geographic coverage confused with scenario/risk coverage | Separate data types and result labels; acceptance checks |
| DI-015 | Critical | Detector coverage confused with FGS effectiveness | Independent reliability, logic, final elements and response calculations |
| DI-016 | High | Detector voting misunderstood (1ooN versus 2ooN) | Configurable method with independently checked scenarios |
| DI-017 | High | Incorrect sampling weights on adaptive grids | Volume-weighting of cells, conservation tests, convergence |
| DI-018 | High | Inaccessible/inside-equipment zone volume included | Zone masking and accepted excluded-volume register |
| DI-019 | Critical | Unqualified standards-implementation claims | Licensed texts, technical review and claim gate |
| DI-020 | Critical | Synthetic data accidentally replaced by sensitive client material | Pack, log, screenshot and commit scans; default synthetic-only |
| DI-021 | High | Untrusted CAD parsing creates attack surface | Helper-process sandbox, size limits and file scanning |
| DI-022 | High | SQLite modified while synced/shared | Local editing copy and integrity/conflict checks; no network WAL |
| DI-023 | High | Crash mid-save or recovery overwrites work | Atomic save + backup + explicit recovery; fault injection |
| DI-024 | High | Cross-version schema corruption | Frozen migrations and older/newer file gates |
| DI-025 | High | Numerical differences across machines | Pin dependencies, tolerance, deterministic iteration and platform qualification |
| DI-026 | High | Large model freezes UI | Background workers, progress/cancel and memory ceilings |
| DI-027 | High | AI generated detector claims lack evidence | Closed-schema proposal, named review actor, no direct write |
| DI-028 | High | AI external cost/data leakage | No AI in M0; signed preflight, preview, budget and audit later |
| DI-029 | High | AI module substitutes unavailable model silently | Strict fail, no fallback policy |
| DI-030 | High | Optimisation yields physically impossible design | Candidate positions with documented engineering constraints |
| DI-031 | High | Inconsistent Word/Excel/PDF calculation numbers | One canonical snapshot and round-trip export QA |
| DI-032 | High | API contract drift with Worksheet / P&ID Reader | Schema/version interface, proposal-only, no integration without approval |
| DI-033 | High | P&ID connectivity guessed as equipment location | Physical location requires geometric source; fail if absent |
| DI-034 | Medium | Unverifiable sample resolution or hidden defaults | Record full calculation parameters and qualification state |
| DI-035 | Medium | Proprietary detector performance library licensing | Licence review per manufacturer and no redistributing restricted curves |
| DI-036 | Medium | Qt/VTK/graphics dependency and licence issues | Confirm compatible binary versions and redistribution terms before production |
| DI-037 | High | Existing Worksheet GitHub repository appears empty | Cannot clone UI; use owner prompt tokens and request real reference pack |
| DI-038 | High | Host environment differs from Windows 11/Python 3.12 | Run real platform Qt screenshot/acceptance tests on owner's Windows PC |
| DI-039 | High | Undo ledger incomplete for all commands | Implement compensating commands for every edit, including deletion and revisions |
| DI-040 | High | Window closure after choosing No keeps recoverable unsaved work | Clarify UX: explicit discard vs preserve for recovery; add separate choices |

Current controls in v0.1.0a1: schema v1, local working copy, explicit file locks, detected source save conflicts, backup, explicit crash recovery, evidence-linked candidate detector register, partial immutable command ledger, theme contrast tests, labelled educational geometry. No CAD import, real F&G coverage, or independent engineering qualification.

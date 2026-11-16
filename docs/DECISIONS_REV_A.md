# Owner decision register - 16 November 2026
Status: ALL BELOW PROPOSED ONLY. No default is an approval. Based on section 12 of EIE-STANDALONE-BUILD-PROMPT-01. Before later owner-dependent work, accept or amend in one response.

| ID | Question and recommended default | Consequence if accepted | Status |
|---|---|---|---|
| Q1 | A: Program title 'Fire & Gas Mapping Engineering System', one portable `.fgcase` file | Extension and branding become a contract | PROPOSED |
| Q2 | A: Manual, engineer-reviewed software first; AI preparation added only after validated imports | Lowers initial automation risks | PROPOSED |
| Q3 | A: First qualified calculation planned for 3D flame geographic mapping with 1ooN/2ooN; no gas calculation until next stage | Prioritises testable geometry + detector response | PROPOSED |
| Q4 | A: Evidence includes drawing/document revision, page/box, detector vendor spec and numeric rule/version, source hash, actor | Enables technical audit and no silent AI facts | PROPOSED |
| Q5 | A: JSON and Excel register at first engineering model milestone; Word and PDF after snapshot QA; all five formats required for completed product | Controls report complexity | PROPOSED |
| Q6 | A: AI disabled by default; later optional approved provider through controlled gateway with preview, explicit transfer consent and per-job ceiling; no paid calls before separate budget approval | Entire product works offline | PROPOSED |
| Q7 | A: All development fixtures synthetic; real client data remains local and must never enter tests, source control or external AI without item-specific approval | Minimises confidentiality risks | PROPOSED |
| Q8 | A: Create a NEW local working repository under authorised Windows project directory after owner supplies exact folder; new development branch, no commit/merge/push until owner approval | Existing apps untouched | PROPOSED |
| Q9 | A: Review after first usable foundation + synthetic demo (M0/WP01), then after first 3D/geometry milestone | Supports phased engineering checks | PROPOSED |
| Q10 | A: All fixed rules in owner standard unchanged; adapt Decimal arithmetic only for floating-point numerical geometry with explicit tolerance and qualification | Preserves standard without inappropriate numeric types | PROPOSED |

Additional engineering-specific decisions that require named owner approval:

| ID | Technical question and default | Engineering significance |
|---|---|---|
| F01 | A: Offshore FPSO/platform and onshore gas plant at start | Defines initial risk and data examples |
| F02 | A: Both onshore and offshore 3D facility geometry; STEP/STL/OBJ import after qualified mesh tests | Affects geometry libraries and verification |
| F03 | A: Flame performance from manufacturer curves, no generic FOV used for engineering acceptance | Prevents optimistic visibility misclassification |
| F04 | A: 1ooN and 2ooN plus configurable N-out-of-M; default study requires explicit voting selection | Aligns with relevant fire detection philosophies |
| F05 | A: Performance targets specified and signed by engineer, never embedded global pass/fail percent | Avoids unsupported coverage claims |
| F06 | A: Geographic flame mapping first, geographic gas mapping next, scenario/CFD input thereafter | Reduces qualification scope |
| F07 | A: 3D CAD import only when source units/transform accepted; P&ID never provides inferred physical positions | Prevents spatial hallucination |
| F08 | A: Performance uncertainty and sensitivity must be reported | Avoids false precision |
| F09 | A: Candidate detector optimisation constrained by feasible locations and maintenance | Avoids unrealistic layouts |
| F10 | A: Separate software test status from engineering model qualification | Prevents premature acceptance |

Owner may respond: "Approve Q1-Q10 defaults and F01-F10 defaults", or supply modifications by ID. The initial isolated prototype does not constitute approval.

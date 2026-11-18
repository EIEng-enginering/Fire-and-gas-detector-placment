# Owner decision register - 16 November 2026
Status (updated 18 Nov 2026, Rev G): Q1–Q10 and F01–F10 APPROVED by the owner; see the owner approval record below. The original text said: ALL BELOW PROPOSED ONLY. No default is an approval. Based on section 12 of EIE-STANDALONE-BUILD-PROMPT-01. Before later owner-dependent work, accept or amend in one response.

| ID | Question and recommended default | Consequence if accepted | Status |
|---|---|---|---|
| Q1 | A: Program title 'Fire & Gas Mapping Engineering System', one portable `.fgcase` file | Extension and branding become a contract | APPROVED by owner 18 Nov 2026 |
| Q2 | A: Manual, engineer-reviewed software first; AI preparation added only after validated imports | Lowers initial automation risks | APPROVED by owner 18 Nov 2026 |
| Q3 | A: First qualified calculation planned for 3D flame geographic mapping with 1ooN/2ooN; no gas calculation until next stage | Prioritises testable geometry + detector response | APPROVED by owner 18 Nov 2026 |
| Q4 | A: Evidence includes drawing/document revision, page/box, detector vendor spec and numeric rule/version, source hash, actor | Enables technical audit and no silent AI facts | APPROVED by owner 18 Nov 2026 |
| Q5 | A: JSON and Excel register at first engineering model milestone; Word and PDF after snapshot QA; all five formats required for completed product | Controls report complexity | APPROVED by owner 18 Nov 2026 |
| Q6 | A: AI disabled by default; later optional approved provider through controlled gateway with preview, explicit transfer consent and per-job ceiling; no paid calls before separate budget approval | Entire product works offline | APPROVED by owner 18 Nov 2026 |
| Q7 | A: All development fixtures synthetic; real client data remains local and must never enter tests, source control or external AI without item-specific approval | Minimises confidentiality risks | APPROVED by owner 18 Nov 2026 |
| Q8 | A: Create a NEW local working repository under authorised Windows project directory after owner supplies exact folder; new development branch, no commit/merge/push until owner approval | Existing apps untouched | APPROVED by owner 18 Nov 2026 |
| Q9 | A: Review after first usable foundation + synthetic demo (M0/WP01), then after first 3D/geometry milestone | Supports phased engineering checks | APPROVED by owner 18 Nov 2026 |
| Q10 | A: All fixed rules in owner standard unchanged; adapt Decimal arithmetic only for floating-point numerical geometry with explicit tolerance and qualification | Preserves standard without inappropriate numeric types | APPROVED by owner 18 Nov 2026 |

Additional engineering-specific decisions that require named owner approval:

| ID | Technical question and default | Engineering significance | Status |
|---|---|---|---|
| F01 | A: Offshore FPSO/platform and onshore gas plant at start | Defines initial risk and data examples | APPROVED by owner 18 Nov 2026 |
| F02 | A: Both onshore and offshore 3D facility geometry; STEP/STL/OBJ import after qualified mesh tests | Affects geometry libraries and verification | APPROVED by owner 18 Nov 2026 |
| F03 | A: Flame performance from manufacturer curves, no generic FOV used for engineering acceptance | Prevents optimistic visibility misclassification | APPROVED by owner 18 Nov 2026 |
| F04 | A: 1ooN and 2ooN plus configurable N-out-of-M; default study requires explicit voting selection | Aligns with relevant fire detection philosophies | APPROVED by owner 18 Nov 2026 |
| F05 | A: Performance targets specified and signed by engineer, never embedded global pass/fail percent | Avoids unsupported coverage claims | APPROVED by owner 18 Nov 2026 |
| F06 | A: Geographic flame mapping first, geographic gas mapping next, scenario/CFD input thereafter | Reduces qualification scope | APPROVED by owner 18 Nov 2026 |
| F07 | A: 3D CAD import only when source units/transform accepted; P&ID never provides inferred physical positions | Prevents spatial hallucination | APPROVED by owner 18 Nov 2026 |
| F08 | A: Performance uncertainty and sensitivity must be reported | Avoids false precision | APPROVED by owner 18 Nov 2026 |
| F09 | A: Candidate detector optimisation constrained by feasible locations and maintenance | Avoids unrealistic layouts | APPROVED by owner 18 Nov 2026 |
| F10 | A: Separate software test status from engineering model qualification | Prevents premature acceptance | APPROVED by owner 18 Nov 2026 |

Owner may respond: "Approve Q1-Q10 defaults and F01-F10 defaults", or supply modifications by ID. The initial isolated prototype does not constitute approval.


## Owner approval record (Rev G)
- **Date and time:** 18 November 2026, 09:58 AWST (UTC+8).
- **Given by:** Andrew Bardsley (owner), in chat.
- **Verbatim:** "I as the owner approved evething and build everthing that make the full program"
- **Context:** this followed an explanation that:
  - coverage calculation is designed in ENGINEERING_MASTER_SPECIFICATION_REV_A but was gated by a hard-coded refusal;
  - Q1–Q10 and F01–F10 were PROPOSED;
  - the work would be engineer-reviewed, not certified.
- **Effect:** Q1–Q10 and F01–F10 are APPROVED as the defaults stated above. The earlier "synthetic only / calculation BLOCKED / no Git" development rules are lifted by the owner. Git commit and push to main is authorised; force-push is not.

Interpretation recorded for Rev G:
- **Q3 / F06:** flame geographic mapping comes first, then geographic gas mapping. Rev G implements both because the owner asked for the full program.
- **F03:** each engineering run requires an explicit library entry with a contour table for every detector. No generic cone is ever substituted.
- **F05:** performance targets are user-defined per zone. No pass percentage is embedded in the software.
- **F08:** grid-convergence deltas are reported, plus an optional ±10 % range sensitivity.
- **F10:** software test status stays separate from engineering qualification. Results are labelled "Engineer-reviewed results – not independently certified".
- **Q8:** superseded by the owner's later Git authorisation (commit and push to main allowed, no force-push).

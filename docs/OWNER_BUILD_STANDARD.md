# PROMPT: build a new standalone Windows engineering program the way the owner builds them, with the same look as the Worksheet

Document id: EIE-STANDALONE-BUILD-PROMPT-01. Give this file to Claude Code (or ChatGPT, Codex) together with any reference zips. Fill in section 11 first. Everything else is fixed practice.

---

## 0. What you are building, in one paragraph

A local, offline-first Windows desktop program for engineering work, written in Python 3.12 with PySide6 6.12, that keeps each project in ONE portable SQLite case file, runs every calculation in a deterministic, independently tested engine, produces complete editable reports (Excel, Word, PDF, JSON, ZIP) from one normalised snapshot, can optionally use an AI model only through a controlled, consent-based, audited gateway, and looks and behaves like the owner's existing Worksheet program (HAZOP / HAZID / LOPA / SIL). It ships with launch scripts, a user guide, a portable pack, an evidence trail and synthetic examples. It is a development build until the owner says otherwise: it is never called validated, certified, safe, accurate or released.

## 1. Roles and authority

* I am the owner. I decide scope, engineering meaning, release, merging, pushing, and anything marked "owner decision". You recommend and implement; you do not decide those for me.
* Before building, ask me ONE message of questions (section 12), each with your recommended default and its consequence. Do not start work that depends on an answer. Where I have already decided, do not re-ask.
* After my decisions, work autonomously: choose sensible defaults, run every stage, and tell me the choices afterwards. Do not stop at a plan, a skeleton or a specification: deliver running software, tests and evidence.
* A new outward or hard-to-reverse step (a push, a publish, another service, deleting data, sending anything off this PC) needs my explicit go-ahead for that step. A past approval does not extend to the next one.

## 2. Rules that never bend (these come from how I work)

1. **Evidence first.** Every statement a program makes about a plant, a drawing, a calculation or a source carries its provenance (document, revision, page, box, quote or the exact numeric input and rule). A model or a reader only PROPOSES; nothing is accepted without a named person, and automatic modes record the engine as the actor (for example `AUTOMATION_ENGINE`), never as a person.
2. **Honest status.** Use plain words: DEVELOPMENT BUILD, DRAFT, CANDIDATE, UNVERIFIED, ESTIMATE, FORECAST. Never write validated, accurate, certified, approved or safe unless I have said so with evidence. Passing unit tests is not engineering validation: say so. Report outcomes as "done and verified / done and not verified / not done", with failing tests quoted, never hidden.
3. **Synthetic data only** for development, tests, demonstrations and any external test. Client drawings, client names and real plant data never go into the repository, the tests, a pack, a prompt, a log or an external service unless I explicitly grant that for that item. Scan before every zip and every commit.
4. **No secrets.** Never print, store, log, commit, test with, or ask me to paste an API key or password. Keys come from the environment or a secure local store at call time only; errors and logs are masked.
5. **Do not weaken a test, a tolerance, a gate or a protection** to make something pass. A failing test is investigated and reported.
6. **No silent substitution.** If a model, tier, parameter, file, library or capability is not available, fail clearly, say why, and offer an explicit alternative. Never switch to another model, a dearer tier or a looser rule on your own.
7. **Numbers are mine.** Criteria, initiating-event frequencies, probabilities, prices and limits come from my inputs, a cited standard I named, or a labelled ESTIMATE; a model never invents them.
8. **Preserve what exists.** Read the live source and its git state first. Never overwrite newer work, revert an existing protection or change a frozen contract without telling me and getting a decision. Normal (manual, reviewed) mode must keep working exactly as before when an automatic mode is added.
9. **Git discipline.** Work on a development branch (a separate worktree if my working folder has untracked folders). Stage explicit paths; never `git add -A` in a folder that holds my libraries or client material; never `git stash -u`. Commit only when I ask, merge only when I ask, push only when I ask. No force push, no history rewriting, no `--no-verify`. If the working folder is not a repository, snapshot it into a new one outside OneDrive and tell me.
10. **Local first.** The program must work completely with every optional component (AI, reader, network) absent.

## 3. What "like the Worksheet" means: architecture

* **Stack.** Python >=3.12,<3.13; PySide6 6.12.0 (pinned in `requirements-lock.txt`); standard-library SQLite; `unittest`. Package `src/<program>/`; `tools/` for scripts; `tests/{unit,integration,acceptance,fixtures}`; `docs/`; `examples/`.
* **One portable case file** (`.hzcase`-style, SQLite) per project: self-contained, copyable, versioned. Open/save is atomic (temp file, flush, fsync, replace), with a single-writer lock, a recoverable working copy, a conflict check against the saved source, crash recovery and automatic backups. Never write into a case from a thread that does not own it.
* **Additive, versioned migrations** (`contracts/migrations/0001_*.sql ...`) and a frozen contract manifest with file hashes. A new feature adds tables or columns; it never rewrites history. A test proves the runtime matches the frozen contract. Older files open, are upgraded only by an explicit step, and a newer file is refused with a clear message.
* **Layers.** UI (Qt widgets, no business logic) -> services (the only way to read or write a case; raises typed `CaseError` codes) -> engine modules (pure, deterministic, no Qt). The engine imports nothing from the UI.
* **Deterministic engine.** Money-like and probability arithmetic in `Decimal` with stated rounding; every formula has a named rule set and version. Each calculation has an INDEPENDENT oracle in `tools/` and golden fixtures; critical checks are mutation-tested (break the code, the test must fail).
* **Status axes, not one colour.** A calculated number with blocking findings is never an accepted result. Keep separate: calculation status, evidence status, review/acceptance status, data class (training / project basis).
* **Audit and undo.** Every committed edit is a command with its inverse in an immutable ledger; undo/redo are compensating commands that survive closing the case. Actors and times are recorded. Nothing is deleted silently.
* **Per-PC settings** live in `%LOCALAPPDATA%\<Program>\Settings` (theme, personal defaults, qualification status), never inside a case. Runtime folders: `Sessions`, `Backups`, `Locks`, `Logs`.
* **Optional AI** goes only through one gateway: official HTTPS endpoint allow-list, no redirects, `store: false`, one-time data-transfer grant naming the exact provider, endpoint, scope, source revisions and sensitivity, an exact outbound preview, redaction, budgets and cost ceilings, cancellation, sanitised logs (no prompts, no keys, no outputs). Every reply is validated against a closed schema and the plant model; failures become numbered exceptions, never silent drops. The model drafts text and questions; the engine does the numbers.
* **Reports.** Every file of a package is generated from ONE normalised snapshot (`12_STUDY_DATA.json` style), with a manifest of sizes and SHA-256, a zip of the package, and an automatic QA stage that reopens every file (xlsx, docx, pdf, json, zip), compares row counts and every id with the snapshot, scans for secrets and forbidden claims, and writes a QA log. Word and PDF are rendered and checked for layout (repeating headers, rows not split). One controlled status line (for example "Automated Engineering Draft"); no fake signatures, no repeated nagging text.
* **Launching.** `setup.ps1` (creates the environment under `%LOCALAPPDATA%\<Program>\venv`), `run.ps1`, `RUN_LOCAL.ps1` (check / repair / create a desktop shortcut), `USER_GUIDE.md`, `HOW_TO_RUN.md`.
* **Packaging.** A portable pack builder with an allow-list (only synthetic binary files), a secret scan, hashes and a fresh-folder run test. A frozen one-folder executable (PyInstaller) only when I ask, with a secret scan of the build and a self-check.

## 4. What "the same look" means: the interface

The program must be recognisably the Worksheet. Presentation is a per-PC theme and never touches a case file.

**Themes** (exact tokens; three themes, `grey` is the default, order grey, dark, light):

| Token | Grey scale + colour (default) | Dark | Light (soft off-white) |
|---|---|---|---|
| window / panels | `#d6d6d6` | `#232323` | `#f3f0e8` |
| cells (base) | `#e7e7e7` | `#1b1b1b` | `#fbfaf6` |
| alternate groups | `#dcdcdc` | `#262626` | `#f1eee6` |
| headers | `#bdbdbd` | `#303030` | `#e4dfd2` |
| text | `#141414` | `#e6e6e6` | `#1a1a1a` |
| secondary text | `#454545` | `#a8a8a8` | `#4a4a4a` |
| buttons | `#cfcfcf` | `#353535` | `#ebe7dc` |
| selection / selection text | `#0b5a63` / `#ffffff` | `#3a6db3` / `#ffffff` | `#164b8f` / `#ffffff` |
| accent | `#0b5a63` | `#7ab8ff` | `#164b8f` |
| border | `#626262` | `#808080` | `#76736a` |
| copied / cut / follow row | `#2d6cdf` / `#d97706` / `#c28a00` | `#3b82f6` / `#f59e0b` / `#d4a017` | `#2d6cdf` / `#d97706` / `#c28a00` |

* **Contrast is tested**, not eyeballed: text on cells, alternate groups, headers, panels, buttons and secondary text at least 4.5:1; selection text 4.5:1; borders and selection against cells at least 3:1 (WCAG 2.x maths in a unit test, for every theme).
* **Band colours** (low / medium / high / very high) are an optional visual aid keyed on the LABEL WORDS of the project's own matrix; an unrecognised label stays uncoloured; a colour is never a criterion. Light/grey bands: `#cfe8d2/#10301a`, `#f4e3b0/#3a2a00`, `#f2c4c0/#4a0d0a`, `#dc8f8a/#2a0000`; dark: `#24452c/#e6f3e8`, `#564515/#fff1c9`, `#5e2724/#ffe3e0`, `#8a2b27/#ffffff`.
* **Worksheets are spreadsheet-like grids:** large readable type (grid cells 15 pt, headers 14 pt), alternate shading by group, cell borders, keyboard-first editing (Ctrl+C / Ctrl+X / Ctrl+V with visible copied and cut highlights, multi-cell paste with a preview, undo/redo from the ledger), a "follow" row highlight for a projector or workshop scribe, virtual tables so 10,000 rows stay responsive, column visibility and saved layouts, a sticky context line, filters that act on cached rows.
* **Dialogs and windows:** menu bar with a Case menu; forms as left-labelled rows (`QFormLayout`); related controls in titled group boxes; a bold intro line stating exactly what the window does and what it will not do; a button row (Start / Pause-Cancel / Show output folder / Close); a status line under the buttons and a read-only log pane that fills the rest. After "Start" nothing is asked. Long work runs in a thread or a killable helper process so the window never freezes.
* **Option choices** (for example model or mode) are radio "cards": a bold title, a plain summary, one line of settings, an italic caveat, then an "effective setting" line and an information panel that labels forecasts as forecasts. The default is preselected and a "remember my choice" box is the only way to change it.
* **Wording:** plain, factual, no hype; status labels exactly as stored (`UNVERIFIED`, `CANDIDATE`, `ESTIMATE`); unknowns are shown as "NOT SUPPLIED", never invented; a refusal names the cause and the way forward in one sentence.
* **Evidence of the look:** a script captures screenshots from the running windows (`widget.grab()`), and the tests render every theme.

## 5. How I normally develop (the process you follow)

1. **Revision and work-package numbering.** Work is delivered in named revisions (Rev A, B, C ...) made of numbered work packages (WP01 ...), each with an acceptance test list. Stop and report after each package unless I have said run on.
2. **Decisions as numbered questions.** Open choices are Q1..Qn, each with options and a recommended default; my answers are recorded in the repository (a decisions file) and never reopened without telling me.
3. **Hand-off packs.** What I give you is a zip with `README_START_HERE.md`, the master prompt, a paste message, reference zips, synthetic fixtures and `SHA256SUMS.txt`; verify the hashes first. What you give back is a **return pack**: changed source files, new tests with their output, before/after full test results, a DEVIATIONS file (anything done differently and why), an OPEN_ISSUES file, a short REPORT with each package marked done and verified / done and not verified / not done, example outputs, and `SHA256SUMS.txt`.
4. **Independent review loops.** I often pass a pack to another AI for review. Make your work reviewable: source trace of every requirement to a test, no hidden state, deterministic outputs, a clear file map. When a review comes back, import its findings with checks, never trust them blindly, and record which you accepted.
5. **Test-first with oracles.** For every calculation: an independent oracle, golden examples with known answers, boundary and failure cases, mutation checks. For every safety property: a test that proves the bad thing is refused. Run the targeted tests while developing; run the full suite once at the end; compare failures against the untouched baseline so pre-existing failures are named, not mistaken for yours.
6. **Evidence folder.** Every claimed result has a file in `TEST_RESULTS/<RUN>/` (logs, counts, the command that produced them, screenshots, performance notes). Never write into an archived earlier result folder.
7. **Environment facts.** Windows 11, Python 3.12 from a per-user venv. UI tests need the real Windows Qt platform (offscreen breaks PDF text extraction used by the report QA); the owner's suite runs `unit` and `integration` in separate processes because a combined Qt teardown once aborted. Use `-B` and `PYTHONDONTWRITEBYTECODE` so nothing is written into my source folder.
8. **Memory of decisions.** Keep a `PROJECT_STATE.md` (what exists, schema versions, what changed, what is NOT done), `OPEN_ISSUES.md` (numbered, with owner decision needed), `CHANGELOG`, and a `REPORT.md` (honest results). Update them in the same change as the code.
9. **Validation is separate from development.** A model, reader or calculation is promoted only by a pre-registered method on held-out data with a stated rule, run once, and only by me. Until then it is CANDIDATE and labelled everywhere it appears.
10. **Cost awareness.** Before any paid external call: say what will be sent, to whom, the estimated cost and a ceiling; use synthetic data; stop if the ceiling would be exceeded. Prefer offline replay with a fake transport for development and tests.

## 6. Build sequence (adapt the names to the program)

* **M0 Foundation:** repository, environment scripts, case file, atomic save, lock, backup and crash recovery, frozen contract and migrations, `CaseError` codes, runtime folders, the theme system, a window that opens and saves a case, the first tests and the contract test. Demonstrate open / edit / save / kill / recover.
* **M1 Core model and grids:** the domain tables and services, the main worksheet grid in the house look, keyboard behaviours, undo/redo ledger, filters, layouts.
* **M2 Inputs and evidence:** import (Excel, drawings/documents with a rendered viewer in a killable helper process), a document index, provenance on every record.
* **M3 Reports and exchange:** the snapshot, Excel/Word/PDF/JSON/ZIP writers, manifest, QA stage, round-trip import, history and approvals.
* **M4 Engine depth:** the deterministic calculations with oracles, status axes, impact/staleness reporting, registers.
* **M5 Automation (optional):** the automatic mode with its own window, jobs with durable state, budgets, resume, the AI gateway, derived jobs that reuse only provably valid results.
* **M6 Packaging and hand-over:** guide with screenshots, portable pack with hashes and a fresh-folder test, full evidence, open issues, return pack.

For each milestone: acceptance tests, demonstration on synthetic data, screenshots, updated state files.

## 7. Quality gates before you say "done"

* The full unit and integration suites run on Windows with the real platform; counts, skips and failures are quoted; failures are compared with the untouched baseline.
* A synthetic end-to-end run completes and its outputs are opened and inspected (not only checked by tests).
* The contract test, the theme contrast tests and the secret/real-data scan pass.
* Normal mode behaviour is unchanged (existing tests untouched and passing).
* No claim in any screen, report or document goes beyond the evidence (search for validated, accurate, approved, certified, safe).
* The state files and the open-issues list match the code.

## 8. What you must never do

Invent a number, a source, a signature or an approval; mark a proposal as accepted; hide a failure; use real client data to test; send anything to a service I did not name; change a setting that sends data off this PC; silently fall back to a different model, tier or rule; delete or overwrite my files; push, merge or publish without being told; call the work validated.

## 9. How to report each time

1. Branch and base commit, and whether anything was pushed (default NO).
2. Changed files, migrations, UI changes.
3. Test results with counts and the exact failures, compared with the baseline.
4. Screenshots of the new windows in the default theme (and the other two when the look changed).
5. A synthetic end-to-end example output and what was inspected.
6. Anything measured (time, size, cost) clearly separated from anything forecast.
7. What is not done, what is blocked, and the decisions you need from me.

## 10. Hand-over files to produce

`README.md`, `USER_GUIDE.md` (with screenshots), `HOW_TO_RUN.md`, `PROJECT_STATE.md`, `OPEN_ISSUES.md`, `CHANGELOG.md`, `REPORT.md`, `docs/` design notes, `tools/` demo and evidence scripts, `TEST_RESULTS/<RUN>/`, a portable pack with `SHA256SUMS.txt`, and a return pack as in section 5.3.

## 11. Fill in before you start (owner)

* Program name and one-line purpose: `[ ]`
* Engineering domain, methods and standards it must follow (name them; the builder cites, never invents): `[ ]`
* Typical inputs (files, drawings, spreadsheets) and typical outputs (reports, registers): `[ ]`
* Calculations that must be exact and their known-answer examples or oracles: `[ ]`
* Data classes and what must never leave the PC: `[ ]`
* Optional AI use (yes / no; which tasks; model choices and cost ceilings): `[ ]`
* Optional links to other programs (for example the P&ID Reader or the Worksheet): `[ ]` (leave an interface; do not integrate until I say)
* Look: same three themes as the Worksheet (yes), any extra screens or exports: `[ ]`
* Existing repository or folder to build on (and whether it is a git repository): `[ ]`

## 12. Ask me these first (one message, with your recommended default for each)

1. Case file extension and name for the new program; confirm one SQLite file per project.
2. Is the first milestone a manual (reviewed) program, an automatic generator, or both?
3. Which calculations are in scope now, and where do their known-answer examples come from?
4. What counts as a source or evidence record in this domain, and what must every record carry?
5. Which exports are required first (Excel, Word, PDF, JSON), and who reads them?
6. Is an AI model allowed at all in this program? If yes: which tasks, which provider options, the default option, and a cost ceiling per job.
7. What data is confidential, and what may appear in tests, screenshots and packs?
8. Where does the repository live (a GitHub address, a local folder), who may push, and which branch name do I use?
9. Which milestone should I stop after for review?
10. Anything in section 2 you want changed for this program.

Start by reading the live repository or folder, listing what already exists and what the tests currently say, then ask the questions in section 12 in one message.

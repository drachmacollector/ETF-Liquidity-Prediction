# Documentation, Logging and Phase-Gate Protocol

| Field | Value |
|---|---|
| Document ID | PR-01 |
| Version | 1.0 (17 Nov 2026) |
| Applies to | Every session (human or agent) that changes code, data, models or documents in this repository |

This protocol keeps three things separate and always visible: **what was planned** (the documents in `docs/`), **what was actually done** (the records in `records/`, run folders and manifests), and **what was verified** (acceptance reports). It also makes sure a fresh agent or session can pick up the project at any point without reconstructing history.

---

## 1. Planned vs actual: where each lives

| Kind of information | Planned (intent) | Actual (evidence) |
|---|---|---|
| Phase scope and tasks | `docs/technical/phases/PXX_*.md` | `records/walkthroughs/PXX_walkthrough.md` |
| Definitions and parameters | `docs/technical/00_System_Specification.md` | `config/settings.yaml`, `config/pre_registration.md`, run folders' `config.yaml` |
| Progress | `docs/technical/00_System_Specification.md` §13 (phase map) | `records/STATUS.md`, `records/PROGRESS_LOG.md` |
| Decisions | Phase documents' "decision points" | `records/DECISIONS.md` |
| Problems | Phase documents' risk tables | `records/ISSUES.md` |
| Open questions | Research Document §13 | `records/OPEN_QUESTIONS.md` |
| User actions | `docs/manual/MI-XX_*.md` | `records/MANUAL_ACTIONS.md` |
| Data acquisition | Phase documents P04–P06 | `data/manifests/ingest_log.jsonl`, coverage reports |
| Experiments and model runs | Phase documents P11–P15 | `runs/<run_id>/`, `runs/registry.csv` |
| Verification | Acceptance criteria in each phase document | `records/acceptance/PXX_acceptance.md` |

**Rule:** planning documents are not edited to describe what happened. If reality differs from the plan, record it in the walkthrough and, if the plan itself must change for later phases, log a decision and then update the plan with a version bump and a changelog line at the bottom of the changed document.

---

## 2. The records folder

| File | Purpose | Format | Who writes | When |
|---|---|---|---|---|
| `records/STATUS.md` | Single status board: one row per phase and per MI | Table (see §3) | Executing agent | At every status change |
| `records/PROGRESS_LOG.md` | Append-only diary of work sessions | Dated entries (§4) | Executing agent | End of every working session |
| `records/DECISIONS.md` | Every significant decision, with rationale and alternatives | Entries `D-XXX` (§5) | Executing agent; user decisions recorded verbatim | When made |
| `records/ISSUES.md` | Bugs, data problems, blockers, risks that materialised | Entries `I-XXX` (§6) | Executing agent | When found; updated when resolved |
| `records/OPEN_QUESTIONS.md` | Live tracker of research open questions (seeded from the Research Document §13) | Table | Executing agent | When an OQ is resolved or defaulted |
| `records/MANUAL_ACTIONS.md` | Live tracker of manual interventions | Table (§8) | Executing agent; user confirms | When requested / done / verified |
| `records/walkthroughs/PXX_walkthrough.md` | What actually happened in a phase | Template | Executing agent | End of each phase (and mid-phase checkpoints for long phases) |
| `records/acceptance/PXX_acceptance.md` | Evidence that each acceptance criterion is met | Template | Executing agent; orchestrator countersigns | Before marking `VERIFIED` |
| `records/PROJECT_STATE.md` | Final state (P17) | Free form | Executing agent | End of project |

Machine-generated evidence lives outside `records/`:

| Location | Content |
|---|---|
| `data/manifests/ingest_log.jsonl` | One line per downloaded or manually dropped file (System Specification §6.2) |
| `data/manifests/coverage_*.csv` | Coverage per instrument and series |
| `runs/registry.csv` | One row per run: `run_id, started_utc, ended_utc, phase, purpose, model_id, data_cutoff, train_end, test_period, key_metrics_json, status, git_commit, notes` |
| `runs/<run_id>/` | `config.yaml`, `git_commit.txt`, `data_fingerprint.json`, `metrics.json`, `plots/`, `README.md` |
| `logs/` | Runtime logs (gitignored; summarise anything important in the progress log) |

---

## 3. Status vocabulary and the status board

**Phase statuses:** `NOT_STARTED` → `IN_PROGRESS` → `IMPLEMENTED` (code and outputs exist; not yet verified) → `VERIFIED` (acceptance report complete, orchestrator checks done). Side states: `BLOCKED_ON_USER` (waiting for an MI or decision), `BLOCKED_ON_ISSUE` (an `I-XXX` prevents progress), `VERIFIED_WITH_PENDING` (allowed only where a phase document explicitly permits a pending item, e.g., MI-07 in P01; the pending item becomes an entry condition of named later phases).

**MI statuses:** `NOT_NEEDED_YET`, `REQUESTED`, `IN_PROGRESS_USER`, `DONE` (user says done), `VERIFIED` (agent confirmed the result), `DECLINED` (user chose not to do an optional MI), `NOT_APPLICABLE`.

`records/STATUS.md` columns: `Phase | Title | Status | Started | Implemented | Verified | Walkthrough | Acceptance | Blockers | Notes`. Update the row at every status change and add a line to the progress log.

---

## 4. Progress log entries

Append at the end of every working session (and at every phase status change):

```markdown
## 2026-11-20 14:35 IST — P04 — session 3
- Done: Tiingo adapter backfilled 52/55 US tickers; manual drop for USCF files parsed.
- Evidence: runs/20261120-141002_ingest_us/ ; data/manifests/coverage_us.csv
- Not done / carried over: VanEck RSX NAV (waiting on MI-04 item 3).
- Issues: I-007 opened (iShares XLS dates parse as text for pre-2010 rows).
- Decisions: D-014 (use Stooq for EGPT prices 2010-2012).
- Next step: finish SSGA parser; run coverage report.
```

Rules: factual, past tense, link evidence paths, distinguish done from attempted. Never delete or rewrite earlier entries; corrections are new entries.

---

## 5. Decision records

```markdown
### D-014 — Use Stooq prices for EGPT 2010–2012
- Date: 2026-11-20 · Phase: P04 · Decided by: agent (within delegated scope) | user
- Context: Tiingo lacks EGPT before 2013-01-02.
- Options considered: (a) Stooq raw closes; (b) yfinance; (c) drop EGPT 2011 event.
- Decision: (a). Cross-checked 2013–2014 overlap: median |diff| 0.02%.
- Consequences: EGPT price source differs by period; flagged in coverage report.
- Affects documents: none (within P04 scope) | System Specification §x (version bumped to 1.1)
- Reversible: yes
```

**What counts as significant:** any choice between documented alternatives; any deviation from a phase document; any parameter change; any waiver of an acceptance criterion; any user decision; any change to universe, labels, features or evaluation after they were first built.

**Delegated scope:** the executing agent may decide implementation details (library function choice, file layout within a module, parser workarounds) without user approval, but must log them if they matter for reproducibility. Changes to definitions, parameters marked "frozen at P11", universe membership after P07, pre-registration content, or anything touching the lockbox require **user approval** (record "Decided by: user").

---

## 6. Issue records

```markdown
### I-007 — iShares XLS dates parse as text before 2010 [OPEN|RESOLVED|WONTFIX]
- Found: 2026-11-20 · Phase: P04 · Severity: low | medium | high | blocker
- Symptom: …   Cause: …   Impact: …
- Resolution: … (commit/run reference) · Resolved: 2026-11-21
```

A `blocker` issue sets the phase status to `BLOCKED_ON_ISSUE`.

---

## 7. Experiment and run logging

1. Every training, tuning, evaluation or report-generation command runs inside `RunContext` (System Specification §12.5) and therefore creates a run folder and a registry row automatically.
2. The executing agent adds a one-paragraph note to the run folder's `README.md` ("why this run, what was learned") for any run referenced in a walkthrough or report.
3. Failed runs are kept (status `failed`) with the error in the README; they are evidence too.
4. Runs touching the lockbox (P14/P15) must record the pre-registration hash in their README; the code does this automatically.
5. Reports cite run IDs for every number (P17 traceability).

---

## 8. Manual-intervention workflow

1. When a phase needs a user action, the agent sets the MI to `REQUESTED` in `records/MANUAL_ACTIONS.md` with the date, the phase that needs it, and the specific items (e.g., the exact list of files to download), and tells the user in the session, pointing to `docs/manual/MI-XX_*.md`.
2. The agent continues with any work in the phase that does not depend on the MI. If nothing remains, the phase status becomes `BLOCKED_ON_USER`.
3. When the user reports completion, the agent runs the **verification steps** in the MI guide and sets the MI to `VERIFIED` (or back to `REQUESTED` with what is still missing).
4. Credentials are never pasted into chat or committed. The user writes them into `.env` directly; the agent checks only that the variable is set and the service accepts it.

---

## 9. Phase-gate procedure

At the end of each phase:

1. **Self-check (executing agent):** run the phase's acceptance test and full test suite; evaluate each acceptance criterion; fill `records/acceptance/PXX_acceptance.md` with evidence (command outputs, file paths, run IDs, numbers). Mark the phase `IMPLEMENTED`.
2. **Walkthrough:** write `records/walkthroughs/PXX_walkthrough.md` from the template.
3. **Orchestrator verification:** the orchestrating agent (or the same agent in a fresh session, which must not rely on memory of the implementation) performs the phase's "Verification checklist", re-runs at least the acceptance test independently, and either countersigns the acceptance report or lists defects. Defects go to `ISSUES.md` and the phase stays `IMPLEMENTED` until fixed.
4. **Mark VERIFIED:** update STATUS and PROGRESS_LOG; then commit and push to `origin main` (D-003). The message is short, plain English, starts with the phase ID and says what was achieved, e.g. `P09: find price-NAV dislocation episodes and build targets`. At most one extra line for something important. No attribution lines.
5. **Gate for the next phase:** the next phase's prerequisites checklist is evaluated and recorded at the top of its walkthrough.

A phase is never `VERIFIED` merely because code exists. The Global Definition of Done is in System Specification §14.

---

## 10. Walkthrough standard

Use [`templates/WALKTHROUGH_TEMPLATE.md`](templates/WALKTHROUGH_TEMPLATE.md). A good walkthrough lets a fresh agent answer, without reading code: What exists now and where? What was decided and why? What differs from the plan? What is broken or uncertain? What exactly should happen next? Keep it factual and specific (paths, counts, run IDs, dates). Length: usually 1–3 pages; longer for P07, P09, P12, P14, P15.

For long phases, write a dated checkpoint section in the same walkthrough file at least every three working sessions.

---

## 11. Session start and end ritual (for every Claude Code session)

**Start:**
1. Read `CLAUDE.md`, `records/STATUS.md`, the latest 3 entries of `records/PROGRESS_LOG.md`, the walkthrough of the last completed phase, and the current phase document.
2. Check `records/MANUAL_ACTIONS.md` for items waiting on the user and `records/ISSUES.md` for open blockers.
3. State in one or two lines what this session will do.

**End:**
1. Append a progress-log entry.
2. Update STATUS if anything changed.
3. Make sure no half-written file would mislead the next session (if work is incomplete, say so in the walkthrough checkpoint).
4. Commit if the policy allows and the work is in a consistent state.

---

## 12. Templates

| Template | Use |
|---|---|
| [`templates/WALKTHROUGH_TEMPLATE.md`](templates/WALKTHROUGH_TEMPLATE.md) | Phase walkthroughs |
| [`templates/PHASE_ACCEPTANCE_TEMPLATE.md`](templates/PHASE_ACCEPTANCE_TEMPLATE.md) | Acceptance reports |
| [`templates/PRE_REGISTRATION_TEMPLATE.md`](templates/PRE_REGISTRATION_TEMPLATE.md) | `config/pre_registration.md` (P11–P13) |
| [`templates/MANUAL_INTERVENTION_TEMPLATE.md`](templates/MANUAL_INTERVENTION_TEMPLATE.md) | New MI guides discovered during the build |
| Decision and issue formats | §5 and §6 above |

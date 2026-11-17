# P17: Final Validation, Verification, Report and Project Readiness

| Field | Value |
|---|---|
| Phase ID | P17 |
| Depends on | P14, P15, P16 |
| Unlocks | Project closure |
| Estimated effort | 3–5 days |
| Manual interventions | **MI-12** (final review and sign-off of the report and summary; optional hosting) |
| Canonical references | All documents; System Specification §14 (Definition of Done) |

## 1. Purpose

Prove that the project is complete, correct, reproducible and honestly reported, and package it for its audiences: a full technical report, a two-page summary for the Mirae Asset ETF team, a model card and a data card, a reproducibility package, and a final project-state walkthrough that lets anyone (or any agent) pick the project up later.

## 2. Scope

**In scope:** clean-environment rebuild; full test suite; reproduction of headline numbers; traceability audit; documentation-vs-code consistency audit; threats-to-validity review; final report, summary, model card, data card, user guide; readiness checklist; final project state; release tag.

**Out of scope:** new analyses or model changes (anything new is "future work").

## 3. Prerequisites

- [ ] P14, P15, P16 `VERIFIED`.

## 4. Implementation specification

### T17.1 Clean-environment rebuild

1. Clone the repository into a fresh temporary directory; create a new environment from the lockfile.
2. Copy (do not move) `data/raw/` and `data/manual_drop/` from the working copy (raw files are not in git by design; their checksums are in the manifest).
3. Verify every raw file's checksum against `ingest_log.jsonl`.
4. Run `python -m esw rebuild --all` (curated → pricing → labels → features), then `esw evaluate lockbox --frozen --reproduce` and `esw evaluate india --frozen --reproduce` (reproduce mode writes to a new run folder and compares with the original run).
5. Pass condition: content hashes of curated/derived Parquet files identical; headline metrics identical to the original runs (tolerance 1e-9; LightGBM determinism is enabled).
6. Spot-check fresh download: re-download one week of data from each automated source into a scratch folder and confirm the parsers still work (not required to match old files exactly; vendors may revise).

### T17.2 Full test suite and static checks

`pytest -q` (all tests, including `network`-marked tests if network is available), `ruff check`, `ruff format --check`; coverage report for `src/esw` (target ≥ 80% line coverage for `labels`, `features`, `evaluation`, `pricing`; report others).

### T17.3 Traceability audit

Every number, table and figure in the final report and summary must trace to a run ID and a script. Implement the report tables and figures as generated assets (`esw report build`) that embed the run ID in captions. Produce `reports/final/traceability.csv`: `item (table/figure/number), location in report, run_id, script, file`. Manually written numbers in prose must reference a table entry. The audit samples 20 numbers and re-derives them from stored outputs.

### T17.4 Documentation-vs-code consistency audit

- Parameters in `config/settings.yaml` equal System Specification §4.13 (or a logged decision explains each difference).
- Feature dictionary matches the registry; label card matches label code (synthetic tests reference the spec).
- Every decision in `records/DECISIONS.md` that amended a spec section is reflected in the docs (update the spec version and changelog).
- Open questions: each RESOLVED or carried into limitations/future work.

### T17.5 Threats to validity

`reports/final/threats_to_validity.md`: internal validity (leakage risks and controls; label definition choices; multiple comparisons in development; calibration drift), construct validity (close vs NAV vs iNAV; timing artefacts; what "dislocation" captures), external validity (US→India; regime changes; survivorship of ETFs), statistical conclusion validity (clustered events; bootstrap assumptions; small Indian sample). For each: risk, mitigation used, residual risk.

### T17.6 Final deliverables

| Deliverable | Audience | Content |
|---|---|---|
| `reports/final/ETF_Stress_EWS_Technical_Report.md` (+ PDF export) | Technical reviewers | 12–20 pages: problem; mechanisms; data; definitions; methods; baselines; results (US lockbox, India transfer); explanations; business value; robustness; limitations; future work; appendices (pre-registration, hashes, traceability) |
| `reports/final/ETF_Stress_EWS_Summary_2page.md` (+ PDF) | Mirae Asset ETF team | Problem, what was built, headline evidence with CIs in plain language, the Oct 2025 case study, what a desk would see each morning, limitations, what would make it better (internal creation data, iNAV feeds) |
| `reports/final/model_card.md` | Anyone using the model | Intended use, out-of-scope use, training data, metrics, calibration, fairness/stability notes across groups, limitations, update procedure |
| `reports/final/data_card.md` | Anyone using the data | Sources, terms, coverage, known issues, point-in-time rules, licensing constraints |
| `docs/operations/USER_GUIDE.md` | Non-technical users | How to read the brief and dashboard; what WATCH/HIGH mean; caveats |
| `records/PROJECT_STATE.md` | Future agents/maintainers | Final state, how to resume, known issues, future-work backlog with priorities |

The two-page summary is written for its audience (Mirae Asset ETF product/sales/risk staff): plain language, no jargon without definition, every claim backed by the report.

### T17.7 Readiness checklist (`records/acceptance/P17_readiness_checklist.md`)

| Area | Check |
|---|---|
| Reproducibility | T17.1 passed |
| Tests | T17.2 passed |
| Traceability | T17.3 passed |
| Consistency | T17.4 passed |
| Hypotheses | Every pre-registered hypothesis has a reported verdict |
| Negative results | Reported in the summary as prominently as positive ones |
| Operations | `esw daily` works for the latest date; runbook tested by following it step by step |
| Compliance language | Banned-word scan over all reports, briefs, dashboard text |
| Data terms | Data card states terms; no raw vendor data in the repository |
| Secrets | No secrets in git history (`git log -p` scan for key patterns) |
| Records | STATUS shows all phases VERIFIED; all walkthroughs and acceptance reports present; MANUAL_ACTIONS all DONE or DECLINED |
| User sign-off | MI-12 final review DONE |

### T17.8 Release

If D-003 allows: tag `v1.0-research-complete`; write release notes in `records/PROGRESS_LOG.md`. Archive the frozen run folders' hashes in `records/PROJECT_STATE.md`.

## 5. Deliverables

All files in T17.6, plus `reports/final/{traceability.csv,threats_to_validity.md}`, `records/acceptance/P17_readiness_checklist.md`, the reproduction run folders, and the final walkthrough.

## 6. Tests and validation

T17.1–T17.4 are the validation. The acceptance test (`tests/acceptance/test_p17_acceptance.py`) checks presence of all deliverables, the reproduction comparison result file, traceability coverage (every figure/table in the report has a row), and the banned-word scan.

## 7. Acceptance criteria

| ID | Criterion |
|---|---|
| AC-17.1 | Clean rebuild reproduces curated/derived hashes and headline metrics exactly |
| AC-17.2 | All tests pass; static checks clean; coverage reported |
| AC-17.3 | Traceability file covers every table/figure; 20-number audit passes |
| AC-17.4 | Documentation-vs-code audit passes; spec version updated with changelog |
| AC-17.5 | Final report, summary, model card, data card, user guide, PROJECT_STATE written |
| AC-17.6 | Readiness checklist fully checked; MI-12 sign-off recorded |

## 8. Verification checklist (orchestrator)

- [ ] Read the two-page summary as the target reader would; does every claim appear in the technical report with a CI or count?
- [ ] Re-run `esw daily` for the latest date yourself.
- [ ] Confirm STATUS shows every phase VERIFIED.

## 9. Risks and decision points

| Item | Handling |
|---|---|
| Reproduction differs | Find the non-determinism (threads, unordered groupby, timestamps in content); fix; re-run; document |
| Temptation to add "one more analysis" | Future-work list only |

## 10. Walkthrough requirements

The P17 walkthrough doubles as the final project walkthrough: summary of the whole project, verdicts, deliverables, how to resume, and the prioritised future-work list (e.g., iNAV/intraday capture, internal creation data, LLM-assisted brief grounded in tables, international-ETF cap headroom data, price-band simulator, forward-test scorecard after 3 months).

# P14: US Lockbox Evaluation, Robustness and Event Replays

| Field | Value |
|---|---|
| Phase ID | P14 |
| Depends on | P13 **and MI-11 DONE** (pre-registration signed; lockbox opening authorised) |
| Unlocks | P15, P16 evidence views, P17 |
| Estimated effort | 3–4 days |
| Manual interventions | **MI-11** must be DONE before any step below |
| Canonical references | `config/pre_registration.md` (Parts A, B, explainability appendix); System Specification §9; Research Document §7.3 |

## 1. Purpose

Run the frozen system exactly once on the US lockbox (1 Jan 2020 → `DATA_CUTOFF`), evaluate hypotheses H1–H5, H7 (US part) and H8 as pre-registered, run the pre-registered robustness analyses, replay the key US incidents day by day, and quantify business value. This phase produces the project's main scientific evidence.

## 2. Scope

**In scope:** lockbox walk-forward refits with frozen settings; predictions, SHAP, tags, analogues for lockbox rows; all pre-registered metrics with CIs; hypothesis verdicts; robustness analyses; event replays; business-value metrics; `full_us` vs `core_transfer` comparison on the US (value of creation data); the US evaluation report.

**Out of scope:** any change to model, features, labels, thresholds, rules; Indian evaluation (P15).

## 3. Prerequisites (hard gate)

- [ ] MI-11 DONE: `records/MANUAL_ACTIONS.md` shows the user's sign-off with date.
- [ ] The SHA-256 of `config/pre_registration.md` equals the last recorded hash (D-P13-PREREG-EXPL). **If it differs, stop.**
- [ ] `git status` clean for `src/`, `config/`, `reference/` (the frozen state is committed or, if commits are not allowed, archived as a zip with its hash recorded).

## 4. Implementation specification

### T14.1 Lockbox predictions

`esw evaluate lockbox --frozen`:

1. For each lockbox year Y (2020 … year of `DATA_CUTOFF`): train `full_us` and `core_transfer` with the frozen configuration on all rows with `date ≤ start(Y) − EMBARGO` (T11.2), calibrate per the frozen method, predict year Y.
2. Fit the baselines (B0–B3) the same way.
3. Compute SHAP, tags, reasons and analogues (library extended with incidents whose anchor dates precede each query, using the fold models covering their anchor dates).
4. Store everything in one run folder `runs/<id>_lockbox_us/` with the frozen config hashes in `README.md`.

The command refuses to run if the pre-registration hash check fails or if `--frozen` is omitted.

### T14.2 Pre-registered analyses

| Analysis | Output |
|---|---|
| H1–H5, H8 verdicts | Table with metric, comparison, point estimate, 95% CI, onsets, pass/fail |
| H7 (US part) | Tag agreement on lockbox incidents; confusion matrix |
| Metrics by group, asset class, mechanism (catalogue family of linked incident) and year | Tables + figures |
| Reliability diagrams (model and best baseline) | Figures |
| Recall vs alert-budget curves | Figure |
| Lead-time distribution | Histogram |
| Secondary triggers: SEC-style (2%/7-day) and operational events | Lead-time tables |
| Excluding March 2020 | Re-computed headline table |
| Excluding timing-suspect episodes | Re-computed headline table |
| Label sensitivity grid (System Specification §4.13) | For each variant: retrain with frozen hyper-parameters on that variant's labels (pre-registered), headline metrics |
| Horizon variants (H = 1, 3) | Headline metrics using the H = 5 model's scores |
| `full_us` vs `core_transfer` on US lockbox | ΔPR-AUC and Δrecall with CIs ("value of creation data") |

### T14.3 Event replays (US)

For each of the following, if data exist: USO April 2020; LQD and HYG March 2020; GLD March 2020 (COMEX–London dislocation); RSX/ERUS February–March 2022; SLV/SIVR October 2025; GLD/SLV January–February 2026; plus the largest three lockbox episodes not in the catalogue.

Each replay (`reports/replays/<incident_id>.md` + figure) shows, day by day from 20 trading days before onset to the end of the episode: close, NAV, premium, robust band, `p` for `full_us` and `core_transfer`, best-baseline `p`, risk level, tag, top reasons, analogue, shares-outstanding change (US), operational events (with `known_at` markers), and secondary-trigger dates. A short commentary states, without hindsight embellishment, when the system would first have shown WATCH/HIGH and what it said.

### T14.4 Business-value metrics

From T11.3: premium cost avoided per HIGH alert (bps and ₹/$ per 1 crore/1 million deferred), alert burden (alerts per week; false alerts per instrument-quarter), lead-time summary, trigger anticipation. Present in a "What this would have meant for a desk" section with clear caveats (hypothetical; a buyer may not be able to wait; costs differ by investor).

### T14.5 Exploratory analyses (clearly labelled)

Allowed after the pre-registered analyses are complete and saved: e.g., SHAP dependence plots, error analysis of missed onsets, near-miss behaviour (SLV Feb 2021 is in the development period; any lockbox near-misses). They are written in a separate section titled "Exploratory (not pre-registered)" and cannot alter the verdicts.

### T14.6 Report

`reports/evaluation/us_lockbox_report.md` (+ figures): summary of verdicts first, then methods recap (one page), results, robustness, replays (links), business value, limitations, exploratory section. Every number carries its run ID.

## 5. Deliverables

| Path | Description |
|---|---|
| `src/esw/evaluation/lockbox.py`, `src/esw/reporting/{replays,figures,tables}.py`; CLI `esw evaluate lockbox --frozen`, `esw report replay <incident_id>` | Code |
| `runs/<id>_lockbox_us/`, `runs/<id>_sensitivity_*/` | Runs |
| `reports/evaluation/us_lockbox_report.md`, `reports/replays/*.md`, figures | Reports |
| Tests: `tests/unit/test_frozen_guard.py` (hash mismatch refuses to run), `tests/acceptance/test_p14_acceptance.py` | Passing |

## 6. Tests and validation

- Frozen-guard test: altering a byte of the pre-registration makes `esw evaluate lockbox` exit with an error.
- Acceptance: every pre-registered analysis has an output file; every hypothesis has a verdict row; replays exist for every listed incident with data (or a reason).

## 7. Acceptance criteria

| ID | Criterion |
|---|---|
| AC-14.1 | Lockbox run executed once with frozen settings; hash check logged in the run README |
| AC-14.2 | Verdicts for H1–H5, H8 and the US part of H7, each with point estimate, CI and onset count |
| AC-14.3 | All robustness analyses in T14.2 completed |
| AC-14.4 | Replays produced for listed incidents with data |
| AC-14.5 | Business-value section produced with caveats |
| AC-14.6 | No change to frozen files after the run (git diff / hash check at the end) |

**Results are not acceptance criteria.** A failed hypothesis is a valid outcome; the phase is complete when the evaluation is executed and reported correctly.

## 8. Verification checklist (orchestrator)

- [ ] Re-compute one headline metric from the stored predictions with an independent short script; values must match.
- [ ] Confirm that the lockbox run is the only lockbox run in `runs/registry.csv` (a second run is allowed only if the first crashed, with a logged reason and identical settings).
- [ ] Confirm exploratory content is clearly separated.

## 9. Risks and decision points

| Item | Handling |
|---|---|
| A bug is found after the lockbox run | Fix only bugs that make the pre-registered procedure *not* what was specified (e.g., a metric computed wrongly); re-run; log both runs and the bug; report it. Never fix "bugs" that are really modelling choices. |
| Very few lockbox onsets in some groups | Report per-group counts; avoid per-group claims with tiny counts |

## 10. Walkthrough requirements

Record: verdict table; anything surprising; any re-run and why; replay highlights; the business-value headline with caveats.

## 11. Handoff

P15 uses the lockbox-year fold models for Indian years ≥ 2020 and the development-fold models for 2010–2019.

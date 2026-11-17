# P11: Evaluation Harness, Baselines and Pre-Registration (Part A)

| Field | Value |
|---|---|
| Phase ID | P11 |
| Depends on | P09, P10 |
| Unlocks | P12 |
| Estimated effort | 3–4 days |
| Manual interventions | **MI-10** (stakeholder conversation, optional but recommended before freezing alert budgets); sign-off of Part A is part of **MI-11** (Part A can be reviewed now; final sign-off happens after P12) |
| Canonical references | System Specification §4.12–4.13, §8, §9; Research Document §7.3, §11.4, §11.7 |

## 1. Purpose

Build the machinery that decides whether the model works, before the model exists: time-ordered splits with purging and embargo, all metrics (probabilistic, ranking and event-level), block-bootstrap confidence intervals, a leakage detector, and the four baselines. Run the baselines on the development period. Then write and freeze **Part A of the pre-registration**: hypotheses, metrics, numeric pass criteria and procedures for the lockbox and India evaluations.

## 2. Scope

**In scope:** `esw.evaluation` (splits, metrics, bootstrap, event scoring, business-value metrics, leakage detector, reporting helpers); baselines B0–B3; development-period baseline results; `config/pre_registration.md` Part A.

**Out of scope:** LightGBM (P12); any lockbox or India predictions.

## 3. Prerequisites

- [ ] P09 and P10 `VERIFIED`; event-count gate passed or resolved.

## 4. Implementation specification

### T11.1 Data assembly (the only place labels meet features)

`esw.evaluation.dataset.build(market, label_variant="default")` joins `features_<market>` with `daily_labels` on `(instrument_id, date)`, keeps rows with `y` not null and `lock_class ≠ confirmed_locked`, and attaches `episode_id` (next onset within window), `group`, `asset_class`, `month` (for bootstrap blocks).

### T11.2 Splits

- **Development folds (US):** test years 2010–2019 (`DEV_END`). For test year Y: training rows have `date ≤ (first trading day of Y) − EMBARGO`; test rows are dates in Y. Additionally **purge** training rows whose label window `[t+1, t+H+PERSIST_MIN+GAP_BRIDGE]` extends into Y (redundant with the embargo when `EMBARGO` ≥ window; implement anyway and test).
- **Tuning vs confirmation split inside development:** folds 2010–2016 are **tuning folds**; folds 2017–2019 are **confirmation folds** used only to confirm the chosen configuration (P12).
- **Calibration block:** inside each training set, the last 20% of dates (time-ordered) form the calibration block; the model is fitted on the first 80% and calibrated on the last 20%.
- **Lockbox folds (US, used in P14):** test years 2020 … year of `DATA_CUTOFF`, same construction (training includes all earlier data, including earlier lockbox years: standard walk-forward with frozen settings).
- **India (P15):** for Indian test year Y (2010 …), predictions come from the US `core_transfer` model of the US fold whose training ends before Y (System Specification §9).
- Tests: no test date appears in its own training set; embargo respected; purge removes the right rows on a synthetic example.

### T11.3 Metrics

Implemented in `esw.evaluation.metrics`, all taking `y`, `p` (and identifiers for event-level metrics):

| Metric | Definition |
|---|---|
| `pr_auc` | Average precision (scikit-learn `average_precision_score`) |
| `brier`, `bss(ref)` | Brier score; skill `1 − Brier/Brier_ref` |
| `log_loss` | With clipping 1e-6 |
| `ece` | Expected calibration error, 10 equal-count bins |
| `cal_slope`, `cal_intercept` | Logistic recalibration of `y` on `logit(p)` |
| `roc_auc` | Reported only |
| `event_recall(thr)` | Share of episode onsets (eligible, in the test period) for which some eligible day in `[onset − H, onset − 1]` of the same instrument has `p ≥ thr` |
| `lead_time(thr)` | For warned onsets: `onset − first alert day` in that window (trading days) |
| `false_alert_rate(thr)` | Alert **chains** (consecutive alert days merged) that contain no day with `y = 1`, per eligible instrument-month (and per instrument-quarter for HIGH) |
| `alerts_per_week(thr)` | Universe-wide alert chains started per week |
| `trigger_lead(thr, trigger_type)` | For secondary triggers (`sec`, `sebi`, `op_event`): whether and how early an alert preceded the trigger |
| `premium_cost_avoided(thr)` | For alert chains at HIGH that are followed by an episode onset: mean of (`prem` on the alert day − `prem` on the episode end day, or day +10 if sooner), in bps, sign-adjusted for direction (a buyer at a premium avoids paying it; for discounts, a seller avoids selling at a discount); also ₹ per ₹1 crore of purchases deferred |

### T11.4 Bootstrap

Block bootstrap by calendar month (`BOOT_BLOCK`): resample months with replacement, `BOOT_N = 2000` replicates, seeded. For model-vs-baseline comparisons, compute the **paired** difference within each replicate. Report 95% percentile intervals, the number of positive rows and onsets beside every metric, and repeat the headline comparison excluding March 2020.

### T11.5 Leakage detector

Before any fit, compute the single-feature average precision of every feature against `y` on the training rows; any feature with AP > 0.9 or perfectly separating `y` raises `LeakageError`. A test injects a canary feature equal to `y` and asserts the error.

### T11.6 Baselines

All baselines output probabilities, are fitted on the training rows of each fold only, and are calibrated like the model (B1–B3 are probability models by construction).

| ID | Baseline | Fit |
|---|---|---|
| **B0** | Climatology: base rate of `y` per `asset_class` in the training rows | Counting |
| **B1** | Single-signal rule: isotonic regression of `y` on `f1_abs_z` | Isotonic |
| **B2** | Persistence lookup: empirical rate of `y` in cells of (`f1_n_absz_gt2_5` ∈ {0,1,2,3+}) × (`f1_abs_z` bins {<1, 1–2, 2–3, ≥3}) × `asset_class`, with additive smoothing toward the asset-class base rate (strength 20 pseudo-rows) | Counting |
| **B3** | L2-regularised logistic regression on 10 core features: `f1_abs_z`, `f1_z_mean5`, `f1_n_absz_gt2_5`, `f1_z_slope5`, `f4_edge_spread21_z`, `f7_turnover_surge5`, `f6_nav_rv_ratio`, `f5_absdiv_mean5_z`, `f8_global_vix_z`, `f7_peer_z_median` (standardised within fold; median imputation + missing indicators); `C` chosen by inner time-ordered validation on the tuning folds | Logistic |

"**Best baseline**" for a metric is the baseline with the best value of that metric on the **development OOF** predictions; it is fixed in the pre-registration and not re-chosen on the lockbox.

### T11.7 Development-period baseline run

Run B0–B3 on all development folds; produce `runs/<id>_baselines_dev/` with OOF predictions, metrics with CIs, reliability plots, event-level metrics at a grid of thresholds, and `reports/evaluation/baselines_dev.md`.

### T11.8 Pre-registration Part A (`config/pre_registration.md`)

Written from the template in [`docs/process/templates/PRE_REGISTRATION_TEMPLATE.md`](../../process/templates/PRE_REGISTRATION_TEMPLATE.md). It must state, with exact values:

1. Data: `DATA_CUTOFF`, universe (instrument lists by group and market), label parameters (System Specification §4.13), label variant grid for sensitivity.
2. Splits and procedures (T11.2), embargo, calibration-block rule.
3. Metrics (T11.3) and bootstrap (T11.4).
4. Best baseline per metric (from T11.7).
5. **Hypotheses and pass criteria** (fill the numbers marked ⟨…⟩ from T11.7 results and MI-10 input where applicable):

| ID | Hypothesis | Pass criterion |
|---|---|---|
| H1 | `full_us` discriminates onsets better than the best baseline on the US lockbox | Paired bootstrap 95% CI of ΔPR-AUC (model − best baseline) has lower bound > 0 |
| H2 | `full_us` has probabilistic skill over the best baseline | 95% CI of BSS vs best baseline has lower bound > 0 |
| H3 | `full_us` is calibrated on the lockbox | Calibration slope in [0.7, 1.3] **and** |mean p − mean y| ≤ 0.5 × lockbox base rate |
| H4 | `full_us` gives more early warnings than the best baseline at the same alert budget | Event recall at `THR_HIGH` minus best-baseline recall at its own threshold meeting the same `ALERT_BUDGET_HIGH`: 95% CI lower bound > 0; median lead time reported |
| H5 | Controls stay quiet | `US_CTRL` HIGH alert chains ≤ ⟨1 per 10 instrument-years⟩ in the lockbox |
| H6 | Warning patterns transfer to India | `core_transfer` zero-shot PR-AUC on India > best India baseline: **strong pass** if the 95% CI lower bound of the difference > 0; **weak pass** if the point estimate > 0; otherwise fail |
| H7 | Root-cause tags are informative | Top-1 agreement of tags with catalogue primary family on lockbox + India incidents > majority-class rate, one-sided binomial p < 0.05 |
| H8 | Alerts carry business value | Mean premium cost avoided at HIGH alerts > 0 with 95% CI lower bound > 0 (US lockbox); reported for India |
| H9 | Case study: Oct 2025 Indian silver | At least one Indian silver ETF reaches WATCH or HIGH on at least one trading day before the onset of its data-detected Oct 2025 episode (reported with the FoF-suspension `known_at` dates; descriptive, not statistical) |

6. Exclusions and robustness analyses to be run in P14/P15 (excluding March 2020; excluding timing-suspect episodes; label sensitivity grid; horizon variants; lock-excluded vs included).
7. The statement: "Results will be reported whatever they are. No model, feature, threshold or label change will be made after the lockbox is opened. Any analysis not listed here is reported as exploratory."
8. Part B placeholder (filled in P12): final feature lists, model configuration, calibration method, `THR_WATCH`, `THR_HIGH`, model IDs.

At the end of P11, compute the SHA-256 of `config/pre_registration.md` (Part A complete, Part B empty) and record it in `records/DECISIONS.md` as D-P11-PREREG-A.

## 5. Deliverables

| Path | Description |
|---|---|
| `src/esw/evaluation/{dataset,splits,metrics,bootstrap,events,business,leakage,baselines,report}.py` | Harness |
| `runs/<id>_baselines_dev/` | Baseline run |
| `reports/evaluation/baselines_dev.md` | Baseline results |
| `config/pre_registration.md` (Part A) and its hash in `records/DECISIONS.md` | Pre-registration |
| Tests: `tests/unit/test_splits.py`, `tests/unit/test_metrics.py`, `tests/unit/test_event_metrics.py`, `tests/unit/test_bootstrap.py`, `tests/unit/test_leakage_detector.py`, `tests/unit/test_baselines.py`, `tests/acceptance/test_p11_acceptance.py` | Passing |

## 6. Tests and validation

- Metric tests against hand-computed small examples (including event recall, lead time and false-alert chains on a toy timeline).
- Split tests (no overlap; embargo; purge).
- Bootstrap reproducibility with a fixed seed.
- Leaky-canary test.
- Baseline sanity: B0's Brier equals the base-rate variance on its own training data; B1 is monotone in `|z|`.

## 7. Acceptance criteria

| ID | Criterion |
|---|---|
| AC-11.1 | Harness implemented; all tests pass |
| AC-11.2 | Baselines B0–B3 run on all development folds; results with CIs and onset counts reported |
| AC-11.3 | Best baseline per metric recorded |
| AC-11.4 | Pre-registration Part A complete with every ⟨…⟩ filled; hash recorded |
| AC-11.5 | MI-10 done or explicitly skipped by the user (alert budgets kept at defaults if skipped) |

## 8. Verification checklist (orchestrator)

- [ ] Read the pre-registration: every hypothesis has a numeric criterion and a named comparison.
- [ ] Confirm no lockbox-period row was used in any P11 run (check `date` ranges in run folders).
- [ ] Confirm the hash in DECISIONS matches the file.

## 9. Risks and decision points

| Item | Handling |
|---|---|
| Baselines already very strong | Fine; the model must beat them or the result is reported as negative |
| Event-level metrics unstable with few onsets | CIs; onset counts shown; avoid claims whose CI includes no improvement |

## 10. Walkthrough requirements

Record: development baseline results table; chosen best baselines; any metric implementation choices (e.g., alert-chain merging); the pre-registration hash; MI-10 outcome.

## 11. Handoff

P12 uses the harness unchanged; any change to the harness after this point requires a logged decision and, if it touches lockbox procedures, a new Part A hash before P14.

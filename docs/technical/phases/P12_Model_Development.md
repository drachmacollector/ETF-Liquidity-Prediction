# P12: Model Development (development period only) and Pre-Registration Part B

| Field | Value |
|---|---|
| Phase ID | P12 |
| Depends on | P11 |
| Unlocks | P13 |
| Estimated effort | 4–5 days |
| Manual interventions | None during the phase; at the end, Part B is presented for **MI-11** together with P13 results |
| Canonical references | System Specification §8; P11 harness and pre-registration Part A |

## 1. Purpose

Train, tune and calibrate the LightGBM breakdown-onset models (`full_us` and `core_transfer`) **using only development-period data**, compare them with the baselines on development out-of-fold predictions, understand what drives them (ablation by family, stability), choose the WATCH/HIGH thresholds under the alert budget, and freeze everything in Part B of the pre-registration.

## 2. Scope

**In scope:** model training code; random-search tuning on tuning folds (2010–2016); confirmation on folds 2017–2019; calibration-method choice; threshold selection; family ablation; stability analysis; the development-period model report; Part B.

**Out of scope:** any use of lockbox (2020+) or Indian data, including "just a quick look". Explanations (P13).

## 3. Prerequisites

- [ ] P11 `VERIFIED`; Part A hash recorded.

## 4. Implementation specification

### T12.1 Training function

`esw.models.train.fit_fold(train_df, feature_list, params, seed) -> FittedModel`:

1. Split training rows by date: first 80% → fit set; last 20% → calibration block (T11.2).
2. Inside the fit set, the last 15% of dates → early-stopping validation (time-ordered); LightGBM with `objective = binary`, `metric = average_precision`, `deterministic = true`, `seed`, `num_threads` from config, early stopping 100 rounds, max 3,000 rounds.
3. Calibrate the raw scores on the calibration block with the chosen method (isotonic or sigmoid).
4. Return the booster, calibrator, feature list, params, the best iteration, and training metadata (row counts, positive counts, date ranges).

Categorical features (`f10_asset_class`, and in `full_us` `f10_group`, `f10_subgroup`, `f10_legal_form`, `f10_nav_basis`) use LightGBM's native categorical handling with fixed category lists from the reference tables.

### T12.2 Feature sets

- `full_us`: every registered feature valid for the US (all families; India-only features excluded).
- `core_transfer`: features with `core = True` only.
- Both include the `*_missing` indicators of their families.

### T12.3 Tuning (tuning folds 2010–2016 only)

Random search, ≤ 40 configurations per feature set, seed fixed, over:

| Parameter | Values |
|---|---|
| `num_leaves` | 7, 15, 31 |
| `max_depth` | 3, 4, 5, −1 |
| `min_data_in_leaf` | 50, 100, 200, 400 |
| `learning_rate` | 0.02, 0.05 |
| `feature_fraction` | 0.6, 0.8 |
| `bagging_fraction` (freq 1) | 0.7, 0.9 |
| `lambda_l2` | 0, 1, 10 |
| `scale_pos_weight` | 1, 5, √(neg/pos) |
| monotone constraint +1 on `f1_abs_z`, `f1_absz_max5`, `f1_n_absz_gt2_5` | on, off |
| calibration | isotonic, sigmoid |

Objective: mean average precision across tuning folds of the calibrated OOF predictions; tie-break (within 1%) by lower mean log loss, then by simpler model (fewer leaves). Every configuration is one row in `runs/<id>_tuning_<set>/trials.csv`.

### T12.4 Confirmation (folds 2017–2019)

Refit the chosen configuration on each confirmation fold; report PR-AUC, BSS vs best baseline, event recall at candidate thresholds, with CIs. **Confirmation folds do not change the choice** unless the configuration fails catastrophically (e.g., PR-AUC below B0); in that case, the next-best configuration is evaluated and the event is logged as a decision. This is the only permitted re-choice.

### T12.5 Development budget (guard against overfitting the development period)

At most **three** feature-set or design revisions may be made in response to development results (e.g., fixing a bug in a feature, dropping a family that is pure noise). Each revision is a run with a written reason in `runs/registry.csv` and the walkthrough. Bug fixes in data or features found here are fixed at source (P07/P10 code) and rebuilt, and count against the budget only if they change modelling choices.

### T12.6 Full development OOF and comparison with baselines

With the final configuration, produce OOF predictions on all development folds (2010–2019). Report the same metrics as the baselines (T11.3, with CIs) and a side-by-side table. This is the development-period evidence; it is **not** the test of H1–H5 (that is the lockbox).

### T12.7 Threshold selection

On development OOF predictions of `full_us`:

- `THR_HIGH` = the smallest threshold for which HIGH false-alert chains ≤ `ALERT_BUDGET_HIGH` (≤ 1 per eligible instrument-quarter outside episodes).
- `THR_WATCH` = the smallest threshold for which WATCH-or-higher false-alert chains ≤ `ALERT_BUDGET_WATCH`.
- Repeat for `core_transfer` (its own thresholds, used in India), and for each baseline (needed for H4 comparisons at the same budget).
- Plot recall vs alert budget curves for the model and the best baseline.

### T12.8 Ablation by family (development OOF)

Drop each family in turn (F1 … F9, keeping F10) and retrain with the frozen configuration; report ΔPR-AUC and Δevent recall with CIs. Also report "F1 only" (gap state only) to show what the stress families add beyond the gap itself. **Ablation results are descriptive; they do not change the frozen model.**

### T12.9 Stability

Per-fold metrics; Spearman correlation of gain-based feature importance across folds; distribution of predicted probabilities per asset class; check that controls (`US_CTRL`) receive very low probabilities.

### T12.10 Part B of the pre-registration

Append to `config/pre_registration.md`: final feature lists (IDs) for both models; final LightGBM parameters and calibration method; `THR_WATCH`, `THR_HIGH` for each model and for each baseline at the same budgets; model IDs; training procedure for lockbox refits (T12.1 unchanged); production-model procedure for P16 (retrain on all US data up to `DATA_CUTOFF` with the frozen configuration). Compute the new hash and record it as D-P12-PREREG-B. Also copy the final thresholds into `config/settings.yaml` (`THR_WATCH`, `THR_HIGH`).

## 5. Deliverables

| Path | Description |
|---|---|
| `src/esw/models/{train,tune,predict,thresholds,ablation}.py`; CLI `esw model tune|confirm|oof|ablate|thresholds` | Code |
| `config/model_configs/full_us.yaml`, `core_transfer.yaml` | Frozen configurations |
| `runs/<id>_tuning_*`, `runs/<id>_confirm_*`, `runs/<id>_oof_dev_*`, `runs/<id>_ablation_*` | Runs |
| `reports/models/model_dev_report.md` (+ figures) | Development report: tuning summary, confirmation, OOF vs baselines, thresholds, ablation, stability |
| `config/pre_registration.md` (Part B) and hash | Pre-registration |
| Tests: `tests/unit/test_train_reproducible.py`, `tests/unit/test_thresholds.py`, `tests/acceptance/test_p12_acceptance.py` | Passing |

## 6. Tests and validation

- Reproducibility: the same fold trained twice with the same seed yields identical predictions.
- Threshold-selection unit test on a synthetic score/label set.
- Acceptance: assert that every P12 run's data date range ends ≤ `DEV_END` (scan run metadata); thresholds and configurations present in Part B; hash recorded.

## 7. Acceptance criteria

| ID | Criterion |
|---|---|
| AC-12.1 | No P12 run used data after `DEV_END` or any Indian data (verified from run metadata) |
| AC-12.2 | Tuning, confirmation, development OOF, thresholds, ablation and stability results reported with CIs and onset counts |
| AC-12.3 | Development budget respected (≤ 3 revisions, each logged) |
| AC-12.4 | Part B complete; hash recorded; thresholds in settings |
| AC-12.5 | Reproducibility test passes |

**Note:** beating the baselines on development data is *not* an acceptance criterion. If the model does not beat them, P12 still completes; the finding is documented, and the lockbox test proceeds as pre-registered.

## 8. Verification checklist (orchestrator)

- [ ] Scan `runs/registry.csv` for P12 rows and their `data_cutoff`/date ranges.
- [ ] Confirm the confirmation folds did not drive configuration choice (or the logged exception).
- [ ] Read the ablation table and check it is described as descriptive.

## 9. Risks and decision points

| Item | Handling |
|---|---|
| Overfitting the development period by iteration | Development budget; tuning/confirmation split |
| Calibration unstable for rare positives | Sigmoid preferred if isotonic overfits (decided by tuning-fold log loss) |
| Model gains come only from F1 | Reported honestly; still informative ("gap dynamics dominate") |

## 10. Walkthrough requirements

Record: chosen configurations; tuning trajectory summary; confirmation outcome; revisions used; thresholds and achieved development recall; ablation highlights; stability concerns.

## 11. Handoff

P13 uses the frozen models (development folds and, for library signatures, the latest development fold) to build explanations and the analogue finder, validated on development incidents only.

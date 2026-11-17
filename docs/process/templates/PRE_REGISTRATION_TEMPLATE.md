# Pre-Registration — ETF Arbitrage-Stress Early Warning System

> Copy this file to `config/pre_registration.md` in P11. Part A is completed and hashed in P11, Part B in P12, the Explainability appendix in P13. After MI-11 sign-off the file is frozen: any later change invalidates the lockbox gate.

## Part A — Data, labels, procedures, metrics, hypotheses (P11)

### A1. Data
- `DATA_CUTOFF`: ⟨date⟩
- US universe (included instruments by group): ⟨lists⟩
- India universe (included instruments by group): ⟨lists⟩
- Excluded instruments and reasons: ⟨reference to `reference/instruments_*.csv` commit⟩

### A2. Labels
- Parameters: `ABS_FLOOR_BPS` ⟨200⟩, `K_MULT` ⟨3.0⟩, `PERSIST_MIN` ⟨3⟩, `GAP_BRIDGE` ⟨1⟩, `HORIZON` ⟨5⟩, `BASE_WIN/MIN` ⟨60/40⟩, `SCALE_WIN/MIN` ⟨250/120⟩, `SCALE_FLOOR_BPS` ⟨5⟩, `FREEZE_MAX` ⟨60⟩, `COOLDOWN` ⟨5⟩
- Secondary labels: SEC ⟨200 bps, 8 days⟩; SEBI ⟨100 bps, 7 days⟩; no-quote ⟨3 days⟩; operational events ⟨types⟩
- Sensitivity grid: ⟨list⟩
- Event counts at freeze (dev / lockbox / India): ⟨n / n / n⟩

### A3. Splits and procedures
- Development folds: test years ⟨2010–2019⟩; tuning folds ⟨2010–2016⟩; confirmation folds ⟨2017–2019⟩
- Lockbox: ⟨2020-01-01 → DATA_CUTOFF⟩; annual refits; frozen settings
- India: point-in-time US fold models; evaluation ⟨2010-01-01 → DATA_CUTOFF⟩; rolling-origin Indian baselines and recalibration with fallback rule ⟨< 3 onsets → US-fitted⟩
- Embargo ⟨10⟩ trading days; calibration block ⟨last 20% of training dates⟩
- Rows excluded from headline metrics: ⟨confirmed_locked; y = null⟩

### A4. Metrics and statistics
- Primary: PR-AUC; BSS vs best baseline; event recall at THR_HIGH/THR_WATCH; lead time; false alerts per instrument-month/quarter
- Secondary: log loss, ECE, calibration slope/intercept, ROC-AUC, secondary-trigger lead times, premium cost avoided
- Bootstrap: block = calendar month; ⟨2000⟩ replicates; seed ⟨…⟩; paired differences
- Alert budgets: HIGH ⟨≤ 1 per eligible instrument-quarter outside episodes⟩; WATCH ⟨≤ 1 per instrument-month⟩ (MI-10 input: ⟨summary or "skipped"⟩)

### A5. Best baselines (from development OOF)
- PR-AUC: ⟨Bx⟩; Brier: ⟨Bx⟩; event recall at budget: ⟨Bx⟩

### A6. Hypotheses and pass criteria
⟨Copy the H1–H9 table from P11 §T11.8 with every ⟨…⟩ filled⟩

### A7. Robustness analyses (to be reported regardless of results)
⟨excluding March 2020; excluding timing-suspect; label grid; horizons; lock-excluded vs included; per group/mechanism/year⟩

### A8. Commitments
"Results will be reported whatever they are. No model, feature, threshold or label change will be made after the lockbox is opened. Any analysis not listed here is reported as exploratory."

**Part A hash (SHA-256, recorded in DECISIONS as D-P11-PREREG-A):** ⟨…⟩

## Part B — Frozen model specification (P12)

- Feature list `full_us` (IDs): ⟨…⟩
- Feature list `core_transfer` (IDs): ⟨…⟩
- LightGBM parameters (each model): ⟨…⟩
- Calibration method: ⟨isotonic | sigmoid⟩
- Thresholds: `full_us` WATCH ⟨…⟩ HIGH ⟨…⟩; `core_transfer` WATCH ⟨…⟩ HIGH ⟨…⟩; each baseline at the same budgets ⟨…⟩
- Model IDs and development run IDs: ⟨…⟩
- Lockbox refit procedure: ⟨T12.1 unchanged⟩
- Production procedure (P16): ⟨retrain on all US data to DATA_CUTOFF with frozen configuration⟩
- Development budget used: ⟨n of 3 revisions; decision IDs⟩

**Part A+B hash (D-P12-PREREG-B):** ⟨…⟩

## Appendix — Explainability rules (P13)

- Tag families, positive-only rule, secondary threshold ⟨0.25⟩, `UNSPECIFIED` rule
- Episode tag = tag of max-p eligible prediction in [onset − H, onset − 1]
- Reason templates file hash: ⟨…⟩
- Analogue library construction, distance (cosine + ⟨0.5⟩ direction + ⟨0.25⟩ asset class), point-in-time constraint
- Validation tests for H7: ⟨binomial vs majority class, α = 0.05⟩

**Final hash (D-P13-PREREG-EXPL):** ⟨…⟩

## Sign-off (MI-11)

- User: ⟨name⟩, ⟨date⟩ — "I have read this pre-registration and authorise opening the lockbox."

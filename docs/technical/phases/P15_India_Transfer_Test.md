# P15: India Transfer Test

| Field | Value |
|---|---|
| Phase ID | P15 |
| Depends on | P14 |
| Unlocks | P16 evidence views, P17 |
| Estimated effort | 3–4 days |
| Manual interventions | None new (MI-11 covers India: India data are part of the lockbox) |
| Canonical references | Pre-registration (H6, H7 India part, H8 India, H9); Research Document §4.3 (two-layer gap), §5.2 (Indian incidents), §11.6 |

## 1. Purpose

Answer the project's central scientific question: **do warning patterns learned from US arbitrage breakdowns carry over to Indian ETFs?** Evaluate the US-trained `core_transfer` model zero-shot on Indian ETFs, compare it with Indian baselines and an India-recalibrated variant, handle the 1 April 2026 measurement break and the 2026 band-regime changes correctly, and present the Indian case studies, including Mirae's products against peers.

## 2. Scope

**In scope:** Indian predictions (2010 → `DATA_CUTOFF`); Indian baselines; India-recalibrated variant; H6, H7 (India), H8 (India), H9; regime-split reporting; Layer-1 monitor evaluation; SEBI-trigger lead times; case studies; Indian report.

**Out of scope:** training any model on Indian labels other than the pre-registered recalibration and baselines.

## 3. Prerequisites

- [ ] P14 `VERIFIED`.
- [ ] Pre-registration hash unchanged.

## 4. Implementation specification

### T15.1 Point-in-time Indian predictions

For each Indian test year Y from 2010: use the `core_transfer` fold model whose training ended before Y (development folds for 2010–2019, lockbox folds for 2020+), with its own calibration (US calibration block) and its own thresholds (`THR_WATCH_core`, `THR_HIGH_core` from Part B). Compute SHAP, tags, reasons, analogues (library: all incidents, US and Indian, satisfying the point-in-time constraint).

Also produce, for the operational view only (not for H6), predictions from the final `core_transfer` model trained on all US data up to `DATA_CUTOFF`.

### T15.2 Indian baselines (rolling origin)

B0, B1, B2 and B3 fitted on **Indian** rows from years before Y (rolling origin), falling back to the US-fitted version of the same baseline when fewer than 3 Indian onsets exist in the training window. "Best India baseline" per metric is determined on Indian years 2010–2019 and fixed before evaluating 2020+ (pre-registered rule; record which baseline it is).

### T15.3 India-recalibrated variant

Recalibrate `core_transfer` raw scores with the pre-registered calibration method on Indian rows from years before Y (rolling origin; same minimum-onset fallback). Reported alongside zero-shot; H6 is judged on zero-shot.

### T15.4 Regime and measurement-break handling

- Exclude `confirmed_locked` rows from headline metrics; report them separately (Feb 2026).
- Report Indian gold/silver results separately for (a) before 1 Apr 2026 (NAV = import parity; Layer 2 includes the domestic premium), (b) from 1 Apr 2026 (NAV = domestic spot; Layer 2 is pure arbitrage friction), and (c) from 7 Sep 2026 (new band regime; few weeks, say so).
- International ETFs: report structural episodes (absorption) and the model's behaviour around changes in premium level (e.g., 2022 cap stop, April 2024 stop).

### T15.5 Layer-1 monitor (deterministic)

Define Layer-1 episodes on `lp_bps_med5` with the same rule as the primary label (floor 200 bps, `K_MULT` 3, persistence 3, baseline from Layer-1 history). Report the detected Layer-1 episodes (expected: late 2013 gold; Oct 2025 silver), and whether the ETF-level model raised alerts around them. This is descriptive and supports the brief's Layer-1 panel.

### T15.6 SEBI trigger analysis

For every `sebi_trigger` (discount > 1% for 7 consecutive days) and `noquote_trigger` in India: did a WATCH/HIGH alert precede it, and by how many days? Table by instrument and date. This speaks directly to the Risk & Compliance use case.

### T15.7 Case studies

`reports/replays/` entries (same format as P14 replays), at minimum:

1. **Oct 2025 silver (H9):** every Indian silver ETF, Mirae `SILVERAG` highlighted; markers for each AMC's FoF suspension `known_at`; the domestic premium (Layer 1) path; peers vs Mirae; the first WATCH/HIGH date versus the data-detected onset and versus the first FoF suspension.
2. **Feb 2026 crash:** gold and silver ETFs; lock classes; what the model said in the preceding days; caveat that locked prices are not market-clearing.
3. **International ETFs (Mirae `MAFANG`, S&P 500 Top 50, Hang Seng TECH; Motilal `MON100`):** premium level path, structural episodes, alerts around changes.
4. **2013 gold (Layer 1)**, if price/NAV/spot data allow.
5. **March 2020 India**, if episodes exist.

### T15.8 Report

`reports/evaluation/india_transfer_report.md`: verdicts (H6, H7 India, H8 India, H9) first; zero-shot vs recalibrated vs baselines; regime splits; Layer-1 monitor; SEBI triggers; case studies; Mirae vs peers summary; limitations (few onsets, measurement break, no creation data, iNAV vs NAV).

## 5. Deliverables

| Path | Description |
|---|---|
| `src/esw/evaluation/india.py`; CLI `esw evaluate india --frozen` | Code |
| `runs/<id>_india_transfer/` | Run |
| `reports/evaluation/india_transfer_report.md`, `reports/replays/INC-IN-*.md`, figures | Reports |
| Tests: `tests/unit/test_rolling_origin.py`, `tests/acceptance/test_p15_acceptance.py` | Passing |

## 6. Tests and validation

- Rolling-origin test: an Indian baseline for year Y never sees Indian rows from Y or later.
- Point-in-time model selection test: the fold model used for Indian year Y has `training_end < start(Y) − EMBARGO`.
- Acceptance: verdict rows for H6, H7 (India), H8 (India), H9; regime-split tables; case-study files.

## 7. Acceptance criteria

| ID | Criterion |
|---|---|
| AC-15.1 | Indian predictions for 2010 → `DATA_CUTOFF` produced with point-in-time fold models |
| AC-15.2 | H6, H7 (India), H8 (India), H9 verdicts reported with CIs/counts as pre-registered |
| AC-15.3 | Regime splits and lock-excluded/included results reported |
| AC-15.4 | Layer-1 monitor and SEBI-trigger analyses reported |
| AC-15.5 | Case studies 1–3 produced (4–5 if data allow) |
| AC-15.6 | Frozen files unchanged |

## 8. Verification checklist (orchestrator)

- [ ] Check the Oct 2025 replay: markers for FoF suspensions use `known_at`, not `effective_at`.
- [ ] Confirm the Mirae-vs-peers statements are supported by the tables.
- [ ] Confirm iNAV-based press figures appear only as context.

## 9. Risks and decision points

| Item | Handling |
|---|---|
| Very few Indian onsets | Case-study emphasis; wide CIs reported; no over-claiming |
| Zero-shot fails but recalibrated works | Report both; interpret as "patterns transfer but base rates/scales differ" |
| Everything fails | Report plainly; discuss why (measurement break, missing creation data, different market structure) and what data would fix it (the value of internal creation data for an AMC) |

## 10. Walkthrough requirements

Record: verdicts; Indian onset counts by group and regime; key case-study findings; anything unexpected about Indian data behaviour.

## 11. Handoff

P16 uses the final production models and Indian outputs for the brief and dashboard evidence views; P17 consolidates.

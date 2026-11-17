# P10: Feature Engineering — Stress Signals

| Field | Value |
|---|---|
| Phase ID | P10 |
| Depends on | P08 (**not** P09: features must be built without access to labels) |
| Can run in parallel with | P09 |
| Unlocks | P11 |
| Estimated effort | 4–6 days |
| Manual interventions | None |
| Canonical references | Research Document §3 (mechanisms), §9.6 (availability matrix); System Specification §4.14 (families), §7 (point-in-time rules) |

## 1. Purpose

Build the point-in-time feature panel that encodes the observable precursors of each breakdown mechanism, organised into families that map to root-cause tags, with a registry that documents every feature, marks which features are available in both markets (the **transferable core**), and is protected by leakage tests.

## 2. Scope

**In scope:** feature registry; families F1–F10; peer and cross-sectional features; the `as_of` accessor; missing-value policy; the feature dictionary; the availability matrix; leakage, rebuild and unit tests.

**Out of scope:** feature selection by predictive power (P12 does ablation within the development period only); labels.

## 3. Prerequisites

- [ ] P08 `VERIFIED`.

## 4. Implementation specification

### T10.1 Registry and conventions

Every feature is a function registered with metadata:

```python
@feature(
    id="f4_edge_spread21_z",
    family="LIQ",
    markets={"US", "IN"},
    core=True,
    lookback=270,
    unit="z",
    inputs=["px_daily.open", "px_daily.high", "px_daily.low", "px_daily.close"],
    missing="null+flag",
    description="EDGE spread (21d) standardised vs own trailing 250d",
)
def f4_edge_spread21_z(ctx: FeatureContext) -> pd.Series: ...
```

- Feature IDs: `f<family number>_<name>`; families: F1 GAP, F2 CRE (creation/flow), F3 CRE (capacity/constraint), F4 LIQ, F5 STL, F6 UND, F7 DEM, F8 MKT, F9 CAL, F10 CTX.
- Every feature is computed per `(instrument_id, t)` from data with `known_at ≤ τ(t)` via `esw.features.pit` (System Specification §7). Feature functions never read files directly.
- "Own-history" standardisation uses trailing windows ending at `t` (inclusive of `t` when the value at `t` is known at `τ(t)`), never full-sample statistics.
- Missing policy: if inputs are unavailable, the value is null and a family-level indicator `<family>_missing` is set; no imputation. LightGBM handles nulls natively; baseline B3 (logistic) uses fold-wise median imputation plus the indicator.
- `asset_class` (CTX) is the transfer-safe categorical: `commodity_physical`, `commodity_futures`, `bond`, `intl_equity`, `dom_equity` (mapping: `US_COMM_PHYS`, `IN_GOLD`, `IN_SILVER` → `commodity_physical`; `US_COMM_FUT` → `commodity_futures`; `US_BOND`, `IN_DEBT` → `bond`; `US_INTL`, `IN_INTL` → `intl_equity`; `US_CTRL`, `IN_CTRL` → `dom_equity`).

### T10.2 Feature specification

"Core" = included in the `core_transfer` model (available with the same definition in both markets). Windows are in trading days.

**F1 Gap state and persistence (family `GAP`)** — from `pricing_panel` (`prem`, `b`, `s`, `dev`, `z`, `band_*`)

| ID | Definition | Core |
|---|---|---|
| `f1_z` | `z(t)` | Y |
| `f1_abs_z` | `|z(t)|` | Y |
| `f1_excess_bps_rel` | `excess(t) / s(t)` | Y |
| `f1_z_mean5`, `f1_z_mean20` | Mean of `z` over last 5/20 days | Y |
| `f1_absz_max5`, `f1_absz_max20` | Max `|z|` over last 5/20 | Y |
| `f1_n_absz_gt2_5`, `f1_n_absz_gt2_20` | Count of days with `|z| > 2` | Y |
| `f1_sign_consistency5` | Share of last 5 days with `sign(dev)` equal to today's | Y |
| `f1_z_slope5` | OLS slope of `z` on day index over last 5 days | Y |
| `f1_days_since_absz_gt3` | Trading days since last `|z| > 3` (capped at 250) | Y |
| `f1_rt_dd_count20` | Count of real-time threshold crossings (`|dev| ≥ max(ABS_FLOOR_BPS, K_MULT·s)`, unfrozen) in last 20 | Y |
| `f1_prem_std20_rel` | Std of `prem` over 20 days ÷ `s(t)` | Y |
| `f1_band_width_rel` | `band_width / s` | Y |
| `f1_prem_bps_abs_level` | `|prem(t)|` in bps (absolute level matters for capacity-driven events) | Y |

**F2 Creation activity (family `CRE`)** — US only (shares outstanding)

| ID | Definition | Core |
|---|---|---|
| `f2_so_chg1`, `f2_so_chg5`, `f2_so_chg20` | % change in shares outstanding over 1/5/20 days | N |
| `f2_so_chg20_z` | `f2_so_chg20` standardised vs own trailing 250 days | N |
| `f2_so_chg20_pctile` | Percentile of `f2_so_chg20` within own history to date | N |
| `f2_prem_no_creation5` | Days in last 5 with `prem > band_hi` and `so_chg1 ≤ 0` (pipe not responding) | N |
| `f2_disc_no_redemption5` | Days in last 5 with `prem < band_lo` and `so_chg1 ≥ 0` | N |
| `f2_creation_on_prem20` | Days in last 20 with `prem > band_hi` and `so_chg1 > 0` | N |
| `f2_so_flat_days20` | Days in last 20 with zero change in shares outstanding | N |

Shares-outstanding timing: apply the per-issuer lag resolved in OQ-05 (default: treat `SO(t)` as reflecting flows of `t−1`).

**F3 Capacity and constraints (family `CRE`)**

| ID | Definition | Core |
|---|---|---|
| `f3_reg_headroom_pct` | Registered shares remaining ÷ shares outstanding (from `capacity`, forward-filled by `known_at`) | N |
| `f3_headroom_days` | Registered remaining ÷ average daily creations over last 20 days (capped) | N |
| `f3_constraint_active` | 1 if any active operational event of type `creation_suspended`, `creation_limited`, `subscription_halt_fof`, `subscription_halt_etf_direct`, `industry_cap_stop`, `prospectus_risk_warning` applies to the instrument, its issuer or its industry segment, known by `τ(t)` | Y |
| `f3_constraint_age` | Trading days since the active constraint became known (null if none) | Y |
| `f3_peer_constraint_active` | 1 if any peer in the same subgroup and market has an active constraint | Y |

**F4 Liquidity (family `LIQ`)**

| ID | Definition | Core |
|---|---|---|
| `f4_edge_spread21` | EDGE spread estimate over last 21 days (`bidask.edge_rolling`), bps | Y |
| `f4_edge_spread21_z` | Standardised vs own trailing 250 days | Y |
| `f4_amihud20_log` | log of mean `|ret_px| / traded_value` over 20 days (traded value in USD for US; INR for India: standardisation below makes the currency irrelevant) | Y |
| `f4_amihud20_z` | Standardised vs own trailing 250 days | Y |
| `f4_hl_range5_z` | Mean `(high − low)/close` over 5 days, standardised vs own 250 | Y |
| `f4_volume_z` | `log(volume)` vs own trailing 60-day mean and std | Y |
| `f4_zero_vol_days20` | Days in last 20 with zero volume | Y |
| `f4_stale_close_flag` | Close equals previous close and volume = 0 | Y |
| `f4_ntrades_z` | India only: `log(n_trades)` vs own 60 days | N |

**F5 NAV staleness and timing (family `STL`)**

| ID | Definition | Core |
|---|---|---|
| `f5_div_bps` | `ret_px − ret_nav` today (bps) | Y |
| `f5_absdiv_mean5_z` | Mean `|div|` over 5 days, standardised vs own 250 | Y |
| `f5_nav_unchanged_run` | Consecutive days NAV unchanged (capped 20) | Y |
| `f5_corr_px_nav20` | Rolling 20-day correlation of `ret_px` and `ret_nav` | Y |
| `f5_lead_corr60` | Rolling 60-day correlation of `ret_px(t−1)` with `ret_nav(t)` (NAV lagging the price) | Y |
| `f5_home_closed_today` | Home market of the underlying closed on `t` (scheduled calendar) | Y |
| `f5_home_closed_next` | Home market scheduled closed on `t+1` (scheduled calendars are known in advance) | Y |
| `f5_unsched_closure_active` | Active `market_closure_unscheduled` event known by `τ(t)` | Y |
| `f5_post_strike_move_abs` | `|post_strike_move_bps|` where available (gold/silver/international with same-day proxy) | N |

**F6 Underlying stress (family `UND`)**

| ID | Definition | Core |
|---|---|---|
| `f6_nav_rv5`, `f6_nav_rv20` | Realised volatility of NAV returns (annualised) | Y |
| `f6_nav_rv_ratio` | `rv5 / rv60` | Y |
| `f6_nav_dd20` | NAV drawdown from 20-day high | Y |
| `f6_nav_absret_max5` | Max `|ret_nav|` over 5 days | Y |
| `f6_und_rv20_z` | Realised volatility of the mapped underlying series (metal/energy/home index), standardised vs own 250 | Y |
| `f6_und_ret5` | 5-day return of the mapped underlying | Y |
| `f6_roll_yield` | (front − second)/front, annualised, for futures funds (null elsewhere) | N |
| `f6_roll_window` | 1 inside the fund's documented roll window | N |
| `f6_lp_med5` | Layer-1 local premium, 5-day median (India gold/silver; US gold/silver: COMEX-vs-NAV-implied proxy, 5-day median) | Y (missing-aware) |
| `f6_lp_chg20` | Change in `f6_lp_med5` over 20 days | Y (missing-aware) |
| `f6_lp_z` | `f6_lp_med5` standardised vs own 250 | Y (missing-aware) |

**F7 Demand pressure (family `DEM`)**

| ID | Definition | Core |
|---|---|---|
| `f7_turnover_surge5` | Mean traded value over 5 days ÷ median over prior 60 days | Y |
| `f7_volume_surge1` | Today's volume ÷ median over prior 60 days | Y |
| `f7_ret_px5`, `f7_ret_px20` | Price momentum | Y |
| `f7_flow_lastmonth_pct` | Net flow % for the last **published** month: US from month-end shares outstanding; India from AMFI monthly AUM net of NAV return; both made available with the same publication rule (10th calendar day of the following month) so the definition matches | Y |
| `f7_peer_turnover_surge` | Median `f7_turnover_surge5` across same-market, same-subgroup peers (excluding self; null if < 2 peers) | Y |
| `f7_peer_z_median` | Median `z` across peers | Y |
| `f7_own_minus_peer_z` | `z − f7_peer_z_median` | Y |
| `f7_peer_z_dispersion` | Interquartile range of peers' `z` | Y |
| `f7_peer_share_absz_gt2` | Share of peers with `|z| > 2` | Y |

**F8 Market-wide stress (family `MKT`)**

| ID | Definition | Core |
|---|---|---|
| `f8_global_vix_z` | US VIX standardised vs trailing 250 days (same series for both markets; known before the Indian decision time) | Y |
| `f8_global_vix_chg5` | 5-day change in VIX | Y |
| `f8_local_vol_z` | Local implied volatility: VIX (US), India VIX (India), standardised vs 250 | Y |
| `f8_us_credit_chg20` | 20-day change in `baa10y` | Y |
| `f8_home_fx_ret5`, `f8_home_fx_rv20_z` | Home-currency move vs listing currency (international ETFs: home FX vs USD or INR; others: USD index for US, USD/INR for India) | Y |
| `f8_local_equity_dd20` | Drawdown of the local broad market (S&P 500 proxy via SPY NAV; Nifty 50) | Y |
| `f8_breadth_absz_gt2` | Share of all eligible instruments in the same market with `|z| > 2` today | Y |

**F9 Calendar (family `CAL`)**

| ID | Definition | Core |
|---|---|---|
| `f9_dow` | Day of week | Y |
| `f9_month_end_window` | Within 2 trading days of month end | Y |
| `f9_days_to_holiday` | Trading days to the next listing-market holiday (capped 10) | Y |
| `f9_post_long_break` | First trading day after ≥ 3 calendar-day closure | Y |
| `f9_index_rebalance_window` | US: within 3 days of quarterly third-Friday rebalances | N |
| `f9_india_festival_window` | India: ±10 days around Dhanteras/Diwali and Akshaya Tritiya (hand-built dates table) | N |
| `f9_india_budget_window` | India: ±3 days around Union Budget | N |

**F10 Context (family `CTX`)**

| ID | Definition | Core |
|---|---|---|
| `f10_asset_class` | Categorical (T10.1) | Y |
| `f10_physical` | 1 for physically backed | Y |
| `f10_age_log` | log(trading days since listing) | Y |
| `f10_log_aum` | log of AUM at the last published month end (same rule both markets) | Y |
| `f10_group`, `f10_subgroup`, `f10_legal_form`, `f10_nav_basis` | Categorical | N (market-specific) |
| `f10_in_band_regime` | India band-regime code | N |

The executing agent may add features only if they fit a family, have a written economic rationale in the registry, and are added **before P12 tuning begins**. Each addition is logged in the walkthrough.

### T10.3 Peer construction

Peers = instruments in the same market and subgroup that are eligible on `t` (have `s` defined). Peer statistics use values at `t` (all known by `τ(t)`). Self is excluded. Peer features are null when fewer than 2 peers exist.

### T10.4 Feature panel and dictionary

- `data/derived/features/features_us.parquet`, `features_in.parquet`: one row per `(instrument_id, date)` from listing to `DATA_CUTOFF`; columns = feature IDs + `*_missing` indicators + identifiers (`instrument_id, date, market, asset_class`).
- `reports/features/feature_dictionary.md` and `.csv`: auto-generated from the registry (ID, family, core, markets, lookback, unit, inputs, description, missing share US/IN).
- `reports/features/availability_matrix.md`: feature × market coverage (% non-null by year) — the empirical version of Research Document §9.6.
- `reports/features/feature_eda.md`: distributions by asset class and market; correlation clusters (to inform P12 interpretation, not selection).

### T10.5 Leakage and correctness tests (mandatory)

1. **Future-injection:** for 200 random `(i, t)` pairs, perturb every curated input row with `known_at > τ(t)` (multiply numeric values by a random factor, shift dates of events); recompute features for those pairs; all values identical.
2. **Import guard:** `esw.features` does not import `esw.labels` (shared test with P09).
3. **Rebuild equality:** two full builds produce identical Parquet content hashes.
4. **Per-feature unit tests:** each family has at least one hand-computed test case; every registered feature is exercised by at least one test (a meta-test enumerates the registry).
5. **Scale-free check:** for core features, the distribution (median, IQR) per asset class does not differ between US and India by more than a documented amount — reported, not a hard gate; large differences are flagged as transfer risks in the walkthrough.

### T10.6 Commands

`esw build features [--market US|IN|all]`.

## 5. Deliverables

| Path | Description |
|---|---|
| `src/esw/features/{registry,pit,f1_gap,f2_creation,f3_capacity,f4_liquidity,f5_staleness,f6_underlying,f7_demand,f8_market,f9_calendar,f10_context,peers,build}.py` | Code |
| `data/derived/features/features_{us,in}.parquet` | Panels |
| `reports/features/{feature_dictionary.md,feature_dictionary.csv,availability_matrix.md,feature_eda.md}` | Reports |
| Tests: `tests/unit/test_features_*.py`, `tests/integration/test_future_injection.py`, `tests/integration/test_features_rebuild.py`, `tests/acceptance/test_p10_acceptance.py` | Passing |

## 6. Tests and validation

The mandatory tests are listed in T10.5. The acceptance test additionally checks that every feature in T10.2 is registered (or logged as omitted), that the core flag matches the table, and that panels cover every included instrument from listing to `DATA_CUTOFF`.

## 7. Acceptance criteria

| ID | Criterion |
|---|---|
| AC-10.1 | Registry contains every feature listed in T10.2 (or a logged reason for omission); dictionary generated |
| AC-10.2 | Future-injection, import-guard and rebuild-equality tests pass |
| AC-10.3 | Every registered feature has at least one unit test (meta-test passes) |
| AC-10.4 | Core feature set defined; for core features, non-null share ≥ 80% in both markets over each market's evaluation window (or exceptions listed) |
| AC-10.5 | Availability matrix and feature EDA produced; transfer risks noted |

## 8. Verification checklist (orchestrator)

- [ ] Open the future-injection test and confirm it perturbs events (`known_at`) as well as numeric series.
- [ ] Spot-check two features by hand on one date (e.g., `f2_so_chg5` for USO on 2020-04-17; `f7_turnover_surge5` for SILVERAG on 2025-10-08).
- [ ] Confirm no feature reads `data/derived/labels`.

## 9. Risks and decision points

| Item | Handling |
|---|---|
| Too many correlated features | Fine for trees; ablation by family in P12 shows which information matters |
| Peer features undefined for small subgroups | Fall back to asset class within market; record |
| Leakage through events dated by `effective_at` | Prevented by the `as_of` accessor and the injection test |

## 10. Walkthrough requirements

Record: final feature count by family and core flag; any added or dropped features with rationale; injection-test design; transfer risks from the scale-free check.

## 11. Handoff

P11 joins features with labels (only inside the evaluation harness) to build folds and baselines.

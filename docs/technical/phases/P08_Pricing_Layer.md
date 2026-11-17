# P08: Pricing Layer (premium, timing diagnostics, Layer 1, total gap, no-arbitrage band, lock classification)

| Field | Value |
|---|---|
| Phase ID | P08 |
| Depends on | P07 |
| Unlocks | P09 and P10 (both read the pricing panel) |
| Estimated effort | 2–3 days |
| Manual interventions | None planned (MI-09 must be DONE for duty rows used by Layer 1; otherwise Layer 1 is null for unverified periods) |
| Canonical references | Research Document §2.2–2.3, §4; System Specification §4.2–4.5, §4.9–4.11 |

## 1. Purpose

Compute, for every instrument-day, the quantities that describe the price–NAV relationship: the ETF premium (Layer 2), the robust baseline and scale, the empirical no-arbitrage band, timing diagnostics, the Indian Layer-1 local-market premium and total investor gap, and the lock classification. Then **prove the measurements are right** by reproducing documented facts from the incident record.

## 2. Scope

**In scope:** the pricing panel; EDA of premium distributions; known-fact reproduction tests; the 1 April 2026 Indian NAV-basis break analysis; a bottom-up arbitrage-cost cross-check for a few ETFs.

**Out of scope:** labels (P09; the label module recomputes baseline/scale itself from the pricing panel's raw premium so that labels and features cannot share code paths that could leak); features (P10).

## 3. Prerequisites

- [ ] P07 `VERIFIED`; `DATA_CUTOFF` set.

## 4. Implementation specification

### T08.1 Pricing panel

`data/derived/pricing/pricing_panel.parquet`, one row per `(instrument_id, date)` on the instrument's listing calendar between listing and min(delisting, `DATA_CUTOFF`), columns:

| Column | Definition |
|---|---|
| `close`, `nav`, `volume`, `traded_value`, `n_trades`, `high`, `low`, `open` | From curated tables |
| `valid` | Price and NAV present and positive; no `nav_spike` flag; not `confirmed_locked` |
| `prem_bps` | System Specification §4.3 |
| `ret_px`, `ret_nav`, `div_bps` | §4.10 |
| `b_bps`, `s_bps`, `dev_bps`, `z` | §4.5 (rolling, strictly before t, over valid rows; *not* episode-frozen here: the episode freeze is a label-module concept) |
| `band_lo_bps`, `band_hi_bps`, `band_width_bps`, `excess_bps` | §4.9 (computed over valid rows strictly before t; in this panel without episode exclusion; the label module produces the episode-aware version) |
| `nav_basis` | From `nav_clock` |
| `post_strike_move_bps` | Underlying move between the NAV strike and the ETF close, where a same-day proxy exists (e.g., gold: `gold_usd_fut` close at settlement vs `gold_usd_navimpl`; international ETFs: not available at daily frequency → null) |
| `lp_bps`, `tg_bps`, `parity_inr`, `domestic_spot_inr`, `duty_total_pct` | §4.4 (India gold/silver only; null elsewhere with `lp_null_reason`) |
| `lock_class`, `band_ref_price`, `band_limit_up`, `band_limit_down` | §4.11 (India; US = `unconstrained`) |
| `issuer_prem_bps`, `issuer_prem_diff_bps` | Where issuer premium data exist: issuer value and our value minus theirs |

Note on `b`, `s`, `band_*` here: these unfrozen versions are what a desk could compute in real time. They are legitimate inputs for features (P10) because they use only past data. The label module (P09) computes its own episode-aware versions independently.

### T08.2 Layer 1 implementation details (India)

- `G(t)`: global price in USD per troy ounce at a time as close as possible to the Indian close. Preference: (1) the global price series used by the old NAV method if recoverable (NAV-implied: before 1 Apr 2026, `NAV ÷ (grams per unit)` gives the parity price; grams per unit can be estimated from the fund's stated metal holdings if available, else this route is skipped); (2) `gold_usd_fut`/`silver_usd_fut` previous US close (known before the Indian close; timing mismatch acknowledged).
- Unit conversions: 1 troy ounce = 31.1034768 g; gold domestic prices usually per 10 g of 999/995 purity; silver per kg of 999 purity. Purity adjustment documented.
- `duty(t)` from `duty` rows with `verified = y` only.
- Report Layer 1 as a 5-day median as well as daily (`lp_bps_med5`) to dampen the timing noise.

### T08.3 Known-fact reproduction (the measurement test)

Implement `tests/acceptance/test_p08_known_facts.py`. Each check uses only data in the panel:

| Check | Expected (from the incident record) | Tolerance / rule |
|---|---|---|
| USO 2020-04-21 premium | ≈ +3,600 bps (36%, USO 10-Q) | Within ±600 bps; if outside, investigate (split basis, NAV date) before proceeding |
| USO 2020-05-01 premium | ≈ +145 bps (S-3/A) | Within ±100 bps |
| UNG Aug 2009 max premium | ≈ +1,900 bps (28 Aug 2009, etf.com) | Max in Aug–Sep 2009 between +1,200 and +2,500 bps |
| LQD March 2020 min premium | ≈ −500 bps | Min over 9–23 Mar 2020 between −700 and −300 bps |
| GLD typical premium | Small | Median |prem| over 2010–2019 < 50 bps |
| SPY typical premium | Tiny | Median |prem| over 2010–2019 < 10 bps |
| Mirae `SILVERAG` Oct 2025 | Positive, several percent (close vs NAV) | Max over 9–16 Oct 2025 ≥ +300 bps; record the actual path |
| Indian international ETF (e.g., `MAFANG`) Apr 2026 | ≈ +2,000 bps | Median over April 2026 between +1,200 and +3,000 bps |
| Issuer premium agreement (6c-11 funds, where issuer uses closing price) | Close agreement | Median |diff| < 5 bps |

If a check fails, the phase stops until the cause is found (data error, definition difference such as NBBO midpoint vs close, or a genuinely different value that the incident record misreports). The resolution goes in the walkthrough; incident-record corrections go into `reference/incidents.csv` notes and the Research Document change log.

### T08.4 Premium EDA

`reports/pricing/premium_eda.md` with figures: premium distribution per group (quantiles 1/5/50/95/99%), robust scale per instrument, time series of premium for 12 key instruments with incident dates marked, share of days with `|z| > 3` by group and year, correlation of `div_bps` with `post_strike_move_bps` for GLD/SLV (evidence of clock mismatch).

### T08.5 The 1 April 2026 Indian NAV-basis break

`reports/pricing/india_nav_basis_break.md`: for Indian gold and silver ETFs, compare (before vs after 1 Apr 2026) the distribution of `prem_bps`, the correlation of NAV returns with domestic spot returns vs with parity returns, and `lp_bps`. Expected: before, NAV tracks parity; after, NAV tracks domestic spot. Confirms or refutes the measurement-break claim (Research Document §4.3) with data.

### T08.6 Bottom-up arbitrage-cost cross-check

For GLD, SLV, USO, LQD and one Indian gold ETF: estimate cost = half the EDGE spread (computed here with `bidask.edge_rolling`, 21-day window) + documented creation fee as bps of a creation-unit value (from prospectus; where unknown, omit) and compare with `band_width_bps`. Report only; not used downstream.

### T08.7 Commands

`esw build pricing`, writing the panel and reports inside a `RunContext(phase="P08")`.

## 5. Deliverables

| Path | Description |
|---|---|
| `src/esw/pricing/{panel,layer1,band,locks,diagnostics}.py` | Code |
| `data/derived/pricing/pricing_panel.parquet` | Panel |
| `reports/pricing/premium_eda.md` (+ figures), `reports/pricing/india_nav_basis_break.md`, `reports/pricing/arbitrage_cost_crosscheck.md` | Reports |
| Tests: `tests/unit/test_premium.py`, `tests/unit/test_layer1.py`, `tests/unit/test_lock_class.py`, `tests/acceptance/test_p08_known_facts.py`, `tests/acceptance/test_p08_acceptance.py` | Passing |

## 6. Tests and validation

- Unit tests: premium sign and scale; baseline uses only prior rows (a test that changes `prem` at t and asserts `b_bps`, `s_bps` at t are unchanged); band percentiles on synthetic data; Layer 1 unit conversion against a hand calculation; lock classification on synthetic band paths for each regime row.
- Known-fact reproduction (T08.3).

## 7. Acceptance criteria

| ID | Criterion |
|---|---|
| AC-08.1 | Panel exists for every included instrument; schema validated; no `prem_bps` on invalid rows |
| AC-08.2 | All known-fact checks in T08.3 pass, or each failure is explained with evidence and accepted by a logged decision |
| AC-08.3 | `b`, `s`, `band_*` are strictly backward-looking (unit test passes) |
| AC-08.4 | Layer 1 computed for Indian gold/silver ETFs wherever inputs are verified; null reasons recorded elsewhere |
| AC-08.5 | Lock classes computed for India; counts per class reported; Feb 2026 lock days visible as `confirmed_locked` or `near_band` |
| AC-08.6 | EDA, NAV-basis-break and cost cross-check reports produced |

## 8. Verification checklist (orchestrator)

- [ ] Open the GLD and SLV premium plots; confirm day-to-day timing noise is visible and incident dates line up.
- [ ] Read the NAV-basis-break report; confirm the conclusion is supported by numbers.
- [ ] Confirm every T08.3 check is reported with the actual value.

## 9. Risks and decision points

| Item | Handling |
|---|---|
| Known facts not reproduced | Stop; investigate; never tune definitions to match press figures without a documented reason |
| Layer-1 global price timing poor | Use 5-day medians in features; state limitation |

## 10. Walkthrough requirements

Record: the actual values for every known-fact check; any definition clarification; Layer 1 coverage; lock-class counts; the NAV-basis-break conclusion.

## 11. Handoff

P09 (labels) and P10 (features) both read `pricing_panel.parquet`. They must not import each other.

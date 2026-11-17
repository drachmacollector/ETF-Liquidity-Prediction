# P06: Underlying, Market-Wide and FX Data Acquisition

| Field | Value |
|---|---|
| Phase ID | P06 |
| Depends on | P02 (series catalogue), MI-07 |
| Can run in parallel with | P03, P04, P05 |
| Unlocks | P07 |
| Estimated effort | 2–3 days |
| Manual interventions | **MI-03** (FRED API key, optional; CSV downloads work without it) |
| Canonical references | Research Document §9.2; System Specification §6.4 (series catalogue), §7 (publication lags) |

## 1. Purpose

Acquire every non-ETF time series the pricing layer and features need: global metal prices, energy futures curves, volatility and credit indicators, interest rates, FX, foreign-market calendars and closure information. Each series is defined once in `reference/series_catalogue.csv` with its publication lag, so point-in-time stamping in P07 is mechanical.

## 2. Scope

**In scope:** all series in the catalogue (System Specification §6.4) plus any added in P02; derivation of NAV-implied benchmark prices where an issuer file provides ounces per share (GLD, SLV if available); continuous-futures roll handling notes; coverage report.

**Out of scope:** licensed benchmarks (LBMA/IBA official prices, iBoxx, ICE indices) unless obtainable within terms; intraday data.

## 3. Prerequisites

- [ ] P02 `VERIFIED`; `reference/series_catalogue.csv` exists.
- [ ] MI-07 DONE for FRED, EIA, yfinance/Stooq.

## 4. Implementation specification

### T06.1 Generic series adapter

`src/esw/ingest/market.py` implements adapters keyed by `source_id` in the catalogue: `fred_csv`/`fred_api`, `eia`, `yf`, `stooq`, `derived`. Each produces staged rows `series_id, date, value, unit, source_id, raw_path, ingested_at` in `data/staged/series/<series_id>.parquet`.

### T06.2 Series to acquire (minimum)

| Group | `series_id` | Source | Notes |
|---|---|---|---|
| Metals (global) | `gold_usd_fut`, `silver_usd_fut`, `platinum_usd_fut`, `palladium_usd_fut` | yfinance/Stooq continuous futures | Continuous series have roll jumps: compute returns only within the same contract where the vendor exposes contract identity; otherwise flag roll dates (large one-day basis jumps on known roll days) and set those returns to null |
| Metals (NAV-implied) | `gold_usd_navimpl`, `silver_usd_navimpl` | Derived from issuer files: NAV ÷ ounces per share (GLD; SLV if available) | ≈ LBMA price at NAV time, net of accrued fees; exactly the benchmark the NAV used |
| Energy curve | `wti_c1..c4`, `hh_c1..c4` | EIA to its last available date (crude stopped after 5 Apr 2024 per P01 check) | Post-2024: `wti_front`, `wti_second` from yfinance contract tickers if P01 found them; else roll-yield features are missing after 2024 (OQ-08) |
| Volatility | `vix`, `ovx` (oil VIX, FRED `OVXCLS`), `gvz` (gold VIX, FRED `GVZCLS`) | FRED | OVX/GVZ start ~2007–2008; missing-aware |
| Credit and rates | `baa10y`, `aaa10y`, `ust10y`, `ust2y`, `tedrate` (to its discontinuation) | FRED | Choose long-history series (OQ-09) |
| Dollar | `usd_broad` | FRED `DTWEXBGS` (from 2006); `DTWEXM` before if needed | |
| FX | `usdinr`, `usdrub`, `usdegp`, `usdtry`, `usdbrl`, `usdmxn`, `usdcny`, `usdjpy`, `usdhkd`, `eurusd` | FRED `DEX*` series where available; others via yfinance | FX of each international ETF's home market |
| FX (India official) | `usdinr_rbi` | RBI/FBIL reference rate | Used for Layer 1 parity (the old Indian NAV method used the RBI reference rate) |
| Foreign equity indices | `idx_<market>` (e.g., EGX30, ATHEX composite, MOEX, CSI300, Nikkei, Hang Seng, Bovespa) | yfinance/Stooq | Used to detect market closures (no new values) and to compute post-NAV-strike moves where timing allows |
| India | `india_vix` (from P05), `nifty50` | NSE | Market-wide stress for India |

### T06.3 Closure detection support

For each foreign market relevant to an included international ETF, produce `data/staged/market_open/<market>.parquet` with `date, scheduled_open (from exchange_calendars or hand list), observed_open (index printed a new value)`. Divergences (scheduled open, no new index value for ≥ 2 days) are candidate unscheduled closures; they are cross-checked against `operational_events.csv` (P03) in P07. Observed data are used only for diagnostics and label checks, never as a feature with future information (a closure is "known" on its first day per System Specification §7).

### T06.4 Commands

`esw ingest series [--series …] [--refresh]`, `esw ingest market-open`.

### T06.5 Coverage report

`reports/data/coverage_series.md` / `data/manifests/coverage_series.csv`: per series first/last date, observations, gaps > 5 business days, unit, publication lag, notes on roll handling or discontinuation.

## 5. Deliverables

| Path | Description |
|---|---|
| `src/esw/ingest/market.py` | Adapters |
| `data/staged/series/*.parquet`, `data/staged/market_open/*.parquet` | Staged series |
| `reports/data/coverage_series.md`, `data/manifests/coverage_series.csv` | Coverage |
| Updated `reference/series_catalogue.csv` | Final list with lags and sources |
| Tests: `tests/unit/test_market_parsers.py`, `tests/acceptance/test_p06_acceptance.py` | Passing |

## 6. Tests and validation

- Golden-file tests for FRED CSV ("." for missing values must parse to null), EIA, yfinance/Stooq frames.
- Roll-flag test: on a synthetic continuous series with a known roll jump, the roll-day return is nulled.
- NAV-implied gold: on a sample of dates, `gold_usd_navimpl` is within 1% of `gold_usd_fut` (they differ by timing and basis; a larger gap flags a parsing error).

## 7. Acceptance criteria

| ID | Criterion |
|---|---|
| AC-06.1 | Every catalogue series is staged or explicitly marked unavailable with a reason and the dependent features listed |
| AC-06.2 | Every series has `publication_lag_days` and timezone recorded in the catalogue |
| AC-06.3 | Coverage spans 2004 → latest for US-relevant series and 2007 → latest for India-relevant series, or gaps are documented |
| AC-06.4 | Roll handling for continuous futures is implemented and tested |
| AC-06.5 | FX series exist for the home market of every included international ETF |
| AC-06.6 | Tests pass; manifest complete |

## 8. Verification checklist (orchestrator)

- [ ] Plot (or inspect) `vix` around March 2020 and `usdrub` around March 2022 to confirm the series are the right ones.
- [ ] Confirm the energy-curve gap after April 2024 is documented and the fallback decision logged.

## 9. Risks and decision points

| Item | Handling |
|---|---|
| Discontinued series | Splice only with a documented overlap check; otherwise leave missing |
| yfinance instability | Cache raw; Stooq fallback; pin version |
| Licensed benchmark needed later | NAV-implied benchmark covers GLD/SLV; elsewhere use proxies and state it |

## 10. Walkthrough requirements

Record: final series list with sources; unavailable series and the features they affect; roll-handling choices; any splices.

## 11. Handoff

P07 stamps `known_at` using the catalogue lags and builds the curated `series_daily` table.

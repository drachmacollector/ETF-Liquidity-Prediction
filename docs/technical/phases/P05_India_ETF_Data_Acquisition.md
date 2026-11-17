# P05: India ETF Data Acquisition (bhavcopy, AMFI NAV, domestic spot, India VIX, monthly AUM)

| Field | Value |
|---|---|
| Phase ID | P05 |
| Depends on | P02 (and MI-07 accepted for these sources) |
| Can run in parallel with | P03, P04, P06 |
| Unlocks | P07 |
| Estimated effort | 3–4 days |
| Manual interventions | **MI-05** (manual download of MCX/IBJA domestic spot history; NSE files only if automated access fails) |
| Canonical references | Research Document §4.3 (two-layer gap), §9.3 (India sources), §9.5 (traps); System Specification §4.1 (India calendar), §6.3, §7 (`known_at`) |

## 1. Purpose

Acquire the full Indian dataset for the transfer test: daily exchange prices for every included Indian ETF since listing (2007 onwards for gold ETFs), official daily NAVs, domestic gold and silver spot prices (for Layer 1), India VIX, and AMFI monthly scheme AUM; and establish the bhavcopy-derived Indian trading calendar.

## 2. Scope

**In scope:** NSE CM bhavcopy backfill in both schemas; BSE fallback for gaps; AMFI NAV history in 90-day windows with an `mfapi.in` fallback; MCX/IBJA spot history (automated or manual); India VIX; AMFI monthly AUM; coverage reporting; the calendar derived from bhavcopy presence.

**Out of scope:** iNAV (no history exists; Research Document §9.4); pre-open auction data; intraday data.

## 3. Prerequisites

- [ ] P02 `VERIFIED`; `reference/instruments_in.csv` complete with ISIN and AMFI code for included instruments.
- [ ] MI-07 DONE for NSE, AMFI, MCX/IBJA, mfapi.in.

## 4. Implementation specification

### T05.1 Bhavcopy adapter (`in_bhav`)

1. **Plan:** one task per date on the preliminary India calendar plus every weekday not on it (to detect unlisted special sessions and holidays by file presence), from 2007-01-01 to today. Weekend dates are attempted only for known special sessions.
2. **URLs:** UDiFF format from 2024-07-08 onward (`…/content/cm/BhavCopy_NSE_CM_0_0_0_YYYYMMDD_F_0000.csv.zip`); legacy format before that (URL pattern confirmed in P01). Use the archive host; respect rate limits (≥ 1 s between requests; NSE is sensitive to bursts).
3. **Raw storage:** keep the full zipped file per day (all securities) in `data/raw/in_bhav/<yyyy>/`. Full files are needed to derive the calendar and to find ETF rows by ISIN.
4. **Parse:** normalise both schemas into `date, isin, symbol, series, open, high, low, close, last, prev_close, volume, traded_value, n_trades, source_schema (legacy|udiff)`. Keep only rows whose ISIN is in `instruments_in.csv` (any `include` value, to allow later inclusion), plus a per-day summary row count for the calendar.
5. **Missing files:** a 404 on a weekday is recorded as `status = not_found` and later treated as a holiday unless contradicted (P07). Repeated 403/blocked responses trigger a pause and the MI-05 fallback for NSE.
6. **Schema mapping:** a single mapping table in code (`BHAV_COLUMN_MAP`) from each schema's column names to canonical names, tested with both golden fixtures.

### T05.2 BSE fallback (`in_bse_bhav`)

Only for instruments or dates missing on NSE (e.g., an ETF listed only on BSE in early years). Same canonical columns plus `exchange = BSE`. Mark rows as fallback; P07 decides precedence.

### T05.3 AMFI NAV adapter (`in_amfi_hist`) and fallback (`in_mfapi`)

1. For each included scheme code, request NAV history in consecutive **90-day windows** from inception to today via the endpoint confirmed in P01. Save each response raw.
2. Parse into `amfi_scheme_code, isin, date, nav, repurchase_price, sale_price, source_id`.
3. If the AMFI endpoint fails or is impractically slow, use `in_mfapi` (`https://api.mfapi.in/mf/<code>`) for full history, and **cross-check** against AMFI on at least 50 random dates per scheme where both exist. Agreement must be exact to the published decimal places; disagreements become quality flags.
4. Daily refresh path: `NAVAll.txt` for the latest date.

### T05.4 Domestic spot (`in_spot_mcx`, `in_spot_ibja`)

- If P01 found an automatable source: download daily gold and silver domestic spot (MCX polled spot if available; else MCX near-month futures settlement as a proxy; else IBJA AM/PM rates) for 2007 → today, recording which series and which time of day (`spot_time_local`).
- If not automatable: the user downloads files per **MI-05**; the adapter parses `data/manual_drop/in_spot/`.
- Canonical staged columns: `metal, date, price_inr, unit (per_10g|per_kg|per_gram), purity, series_type (mcx_polled_spot|mcx_fut_settle|ibja_am|ibja_pm), spot_time_local, source_id`.
- Record clearly in the walkthrough which series covers which period; Layer 1 (P08) depends on it.

### T05.5 India VIX (`in_indiavix`) and monthly AUM (`in_amfi_aum`)

- India VIX daily close history from NSE (method confirmed in P01).
- AMFI monthly scheme-wise AUM (average AUM and/or month-end AUM) for included schemes, with the **publication date** of each monthly file recorded (needed for `known_at`). If publication dates are not available, record `publication_date_estimated = true` (System Specification §7 default rule applies).

### T05.6 Bhavcopy-derived calendar

From the per-day summaries: a date is an NSE trading day if a bhavcopy exists with at least N rows (N = 500 to avoid empty/test files). Compare with the preliminary calendar from P02 and write `reports/data/india_calendar_reconciliation.md` listing every disagreement (expected: special sessions present in data but missing in the library calendar; library holidays where a file exists, or vice versa). P07 adopts the reconciled calendar.

### T05.7 Commands

`esw ingest in-bhav [--start --end --refresh]`, `esw ingest in-nav`, `esw ingest in-spot`, `esw ingest in-vix`, `esw ingest in-aum`, `esw ingest in-all`.

### T05.8 Coverage report

`reports/data/coverage_in.md` / `data/manifests/coverage_in.csv`: per instrument `isin, symbol(s) seen, px_first, px_last, px_days, expected_days (reconciled calendar from first listing day), px_coverage_pct, zero_volume_days, nav_first, nav_last, nav_days, nav_coverage_pct, nav_source, notes`. Plus spot coverage per metal and series, VIX coverage, AUM months.

## 5. Deliverables

| Path | Description |
|---|---|
| `src/esw/ingest/{india_bhav,india_amfi,india_spot,india_misc}.py` | Adapters |
| `data/staged/in_bhav/*.parquet`, `data/staged/in_nav/*.parquet`, `data/staged/in_spot/*.parquet`, `data/staged/in_vix.parquet`, `data/staged/in_aum.parquet` | Staged tables |
| `reports/data/coverage_in.md`, `data/manifests/coverage_in.csv`, `reports/data/india_calendar_reconciliation.md` | Reports |
| Tests: `tests/unit/test_bhav_parsers.py` (both schemas), `tests/unit/test_amfi_parsers.py`, `tests/integration/test_in_ingest_idempotent.py`, `tests/acceptance/test_p05_acceptance.py` | Passing |

## 6. Tests and validation

1. Golden-file tests for legacy and UDiFF bhavcopy, the AMFI history response, `NAVAll.txt`, mfapi JSON and spot files.
2. Symbol-change test: rows for ISIN INF769K01KG6 appear under `SILVRETF` before 15 Sep 2025 and `SILVERAG` after, and are joined to the same instrument.
3. Schema-boundary test: 2024-07-05 (legacy) and 2024-07-08 (UDiFF) both parse to identical canonical columns.
4. Special-session test: a bhavcopy exists and parses for Sunday 2026-02-01.
5. Idempotency as in P04.

## 7. Acceptance criteria

| ID | Criterion |
|---|---|
| AC-05.1 | Every included Indian instrument has staged prices and NAV from listing (or from the earliest available date, explained) to the latest available date |
| AC-05.2 | Price coverage ≥ 97% of reconciled trading days after listing for every included instrument (thinly traded instruments may have zero-volume days, which are still rows if present in bhavcopy; missing rows are counted as gaps) |
| AC-05.3 | NAV coverage ≥ 97% of trading days; AMFI-vs-mfapi cross-check (if mfapi was used) shows exact agreement on ≥ 99% of sampled dates |
| AC-05.4 | Calendar reconciliation report exists; every disagreement is classified (special session, data gap, library error) |
| AC-05.5 | Domestic spot coverage for gold and silver is documented by series and period; any period without spot is listed (Layer 1 will be null there) |
| AC-05.6 | Mirae `GOLDETF` and `SILVERAG` have complete price and NAV series across Oct 2025 and Feb 2026 |
| AC-05.7 | All raw files manifest-logged; idempotency and parser tests pass |

## 8. Verification checklist (orchestrator)

- [ ] Inspect Mirae `SILVERAG` closes and NAVs for 1–20 Oct 2025: the premium (computed by hand for two dates) is visibly positive and of the reported order of magnitude (several percent).
- [ ] Inspect 2026-02-01 and 2026-02-02 rows for a silver ETF: large declines; `high = low = close` on locked days if locked.
- [ ] Confirm the calendar reconciliation report lists 2026-02-01 as a special session.

## 9. Risks and decision points

| Item | Handling |
|---|---|
| NSE throttling or blocking | Slow down (2–3 s between requests); resume from manifest; MI-05 manual fallback for specific ranges |
| AMFI endpoint changes (OQ-20 in v1) | mfapi fallback with cross-check |
| No domestic spot history | Layer 1 restricted; decision logged; transfer test still runs on Layer 2 |
| Legacy bhavcopy lacks ISIN in early years (verify) | Map by symbol via `symbol_history` with date validity; flag rows mapped by symbol |

## 10. Walkthrough requirements

Record: date ranges downloaded per source; blocked periods and how they were filled; spot series chosen per period; calendar disagreements; schema surprises.

## 11. Handoff

P07 adopts the reconciled calendar, merges NSE/BSE, maps ISINs, aligns NAV dates and stamps `known_at`.

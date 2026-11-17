# P02: Reference Data — Universe, Identifiers, Calendars, NAV Clocks and Regime Tables

| Field | Value |
|---|---|
| Phase ID | P02 |
| Depends on | P01 |
| Unlocks | P03, P04, P05, P06 (can run in parallel once P02 is VERIFIED) |
| Estimated effort | 2–3 days |
| Manual interventions | **MI-09** (verification of the India import-duty table and band-regime rows the agent cannot confirm from primary sources) |
| Canonical references | System Specification §3 (`reference/`), §4.1 (calendars), §5 (universe), §6.3 (`instrument`, `symbol_history`, `calendar`, `nav_clock`, `duty`, `band_regime`, `corporate_action`) |

## 1. Purpose

Build the hand-verified reference tables that every other phase joins against. A wrong identifier mapping silently corrupts everything downstream (wrong NAV against a price), so each row is sourced, checked, and quarantined on mismatch. Calendars, NAV-clock definitions, duty rates and price-band regimes are built here because labels, features and the transfer test depend on them being right *for each date*.

## 2. Scope

**In scope:** `reference/instruments_us.csv`, `instruments_in.csv`, `symbol_history.csv`, `nav_clock.csv`, `corporate_actions_manual.csv` (seed), `duty_india.csv`, `band_regimes_india.csv`, `series_catalogue.csv` (initial), `reference/README.md` (column dictionary); loaders and pandera schemas in `esw.reference`; the US calendar; a preliminary India calendar.

**Out of scope:** incidents and operational events (P03); market data download.

## 3. Prerequisites

- [ ] P01 `VERIFIED`, with `universe_feasibility.md` and `source_registry.csv` in place.

## 4. Implementation specification

### T02.1 US instrument table (`reference/instruments_us.csv`)

One row per candidate in System Specification §5.2 (including infeasible ones, with `include = false`). Columns:

`instrument_id, market, ticker, isin, cusip, name, issuer, group, subgroup, underlying, legal_form (open_end|uit|grantor_trust|commodity_pool|etn), rule_6c11 (y/n/unknown), listing_date, delisting_date, currency, nav_source_id, px_source_id, shares_source_id, include, exclude_reason, notes, source_url, verified_by, verified_on`

- `listing_date` and `delisting_date` from the issuer/prospectus or exchange records; cross-check with the first/last dates seen in the P01 probes.
- `legal_form` and `rule_6c11` from the prospectus (P01 primary-text notes). This feeds the report's claims about Rule 6c-11 coverage.
- `subgroup` examples: `gold`, `silver`, `pgm`, `crude`, `natgas`, `broad_commodity`, `agri`, `ig_corp`, `hy_corp`, `muni`, `em_debt`, `loans`, `treasury`, `single_country_em`, `single_country_dm`, `regional`, `large_cap_us`.

### T02.2 India instrument table (`reference/instruments_in.csv`)

Start from the AMFI scheme master (`NAVAll.txt` and the scheme list) filtered to ETFs; keep gold, silver, international, debt (excluding overnight/liquid) and the chosen controls. Columns:

`instrument_id (IN:<ISIN>), market, isin, amfi_scheme_code, name, issuer, is_mirae, group, subgroup, underlying, benchmark_name, nse_symbol_current, bse_code, listing_date, inception_date, creation_unit_units, include, exclude_reason, notes, source_url, verified_by, verified_on`

Rules:

1. **Key on ISIN.** Exactly one AMFI scheme code per ISIN for ETFs (ETFs normally have a single plan/option). Any ISIN with zero or multiple codes is quarantined (`include = false`, `exclude_reason = mapping_conflict`) until resolved.
2. Mirae rows must include at least: Gold ETF (`GOLDETF`), Silver ETF (`SILVERAG`, ISIN INF769K01KG6), NYSE FANG+ ETF (`MAFANG`), S&P 500 Top 50 ETF, Hang Seng TECH ETF, and Mirae equity control ETFs if chosen.
3. `listing_date` from the first bhavcopy appearance (P01 probes or a quick scan in P05; if not yet known, fill from SID/exchange notice and mark for confirmation in P05).
4. Resolve **OQ-18**-type conflicts (e.g., Mirae Silver ETF inception 9 vs 14 Jun 2023) by preferring, in order: AMFI scheme master, SID, exchange listing notice. Record the choice in `notes`.

### T02.3 Symbol history (`reference/symbol_history.csv`)

`instrument_id, exchange (NSE|BSE|NYSEARCA|NASDAQ|CBOE|…), symbol, valid_from, valid_to, source_url`. Must include `SILVRETF → SILVERAG` effective 15 Sep 2025 (verify the date from the exchange notice; v1 research graded it [R]). For US instruments, record listing-exchange moves if found (not critical: prices are fetched by ticker from vendors that handle this, but keep the history for audit).

### T02.4 NAV clock table (`reference/nav_clock.csv`)

`instrument_id, effective_from, effective_to, nav_basis, valuation_time_local, valuation_tz, source_url, notes`. Values of `nav_basis` are listed in System Specification §6.3. Required rows:

- GLD/IAU/GLDM: `lbma_pm` (15:00 Europe/London); SLV/SIVR: `lbma_silver_noon` (12:00 Europe/London); PPLT/PALL: per prospectus (LBMA platinum/palladium prices).
- Futures funds: `futures_settle` (exchange settlement time per contract).
- Bond ETFs: `evaluated_bond` (16:00 America/New_York).
- International equity: `foreign_close` with the home-market close time.
- Domestic US equity: `us_close_16et`.
- Indian gold/silver ETFs: `in_import_parity` until 2026-03-31; `in_domestic_spot` from 2026-04-01 (confirm the exact effective date and any per-AMC transition in P01 notes; OQ-10/OQ-14).
- Indian equity/debt ETFs: `in_close`; Indian international ETFs: `foreign_close` (previous overseas session).

### T02.5 Calendars

- **US:** generate `calendar` rows for `XNYS` from `exchange_calendars` for 2004-01-01 → today + 30 days. `session_type = half` for early closes.
- **India (preliminary):** generate from `exchange_calendars` `XBOM` (or the NSE holiday lists if XBOM is unavailable) for 2007-01-01 → today + 30 days, with special sessions added by hand from exchange circulars (at minimum Sunday 2026-02-01, and Muhurat sessions each Diwali). P05/P07 reconcile this with bhavcopy file presence and the reconciled version becomes canonical.
- Foreign calendars needed for staleness features (`XLON`, `XHKG`, `XTKS`, `XSHG`, others as available) are generated for the same span; record which markets are missing from `exchange_calendars` (e.g., Cairo, Athens, Moscow) — their unscheduled closures come from the operational-event table in P03 and their scheduled holidays from a small hand-built list if the market matters for a feasible instrument.

### T02.6 Corporate actions seed (`reference/corporate_actions_manual.csv`)

`instrument_id, ex_date, type (split|reverse_split|consolidation|unit_split|bonus), ratio, applies_to (price|nav|both), verified (y/n), source_url, notes`. Seed with known events: USO 1-for-8 reverse split (April 2020; confirm exact ex-date), UNG and other USCF/Teucrium reverse splits if any (search filings), Indian ETF unit splits (e.g., some gold ETFs split units; search exchange corporate-action notices) (OQ-19). P07 will detect any that are missed.

### T02.7 India import-duty table (`reference/duty_india.csv`)

`metal (gold|silver), effective_from, effective_to, bcd_pct, aidc_pct, sws_pct, other_pct, total_pct, verified (y/n), source_url, notes`. Cover 2007-01-01 → today. Use CBIC customs notifications and Budget speeches as primary sources. Known anchor: 6% total (5% BCD + 1% AIDC) from July 2024 [K]. **Conflicting reports** exist for February 2026 (unchanged vs reduced) and May 2026 [R]; such rows stay `verified = n` until confirmed, and Layer 1 is not computed for unverified periods (System Specification §4.4). Raise **MI-09** for every row that cannot be confirmed from a primary source the agent can read.

### T02.8 India band-regime table (`reference/band_regimes_india.csv`)

`market, exchange, group (gold_silver|equity_debt|overnight|liquid|international), effective_from, effective_to, base_rule (t2_nav|t1_nav|t1_vwap30), band_init_pct, flex_step_pct, flex_max, cooling_off_note, verified, source_url`. Rows at minimum:

- Pre-2026 regime: ±20% on T-2 NAV for gold/silver and equity/debt ETFs (verify the start date of this rule; earlier periods may differ: mark `verified = n` where unknown so lock class becomes `unknown`).
- Interim from 2026-02-01: gold/silver base T-1 NAV on BSE (and NSE's corresponding arrangement; confirm), still ±20%.
- From 2026-09-07: base T-1 last-30-minute VWAP; gold/silver ±6% initial, 3% flex, uncapped; equity/debt ±10%, 5% flex, max two per direction; overnight ±5%; liquid ±5%.
- International ETFs: applicability unresolved (OQ-11); add a row with `verified = n`.

### T02.9 Series catalogue (initial)

Create `reference/series_catalogue.csv` from System Specification §6.4 with columns `series_id, description, source_id, source_code, unit, frequency, publication_lag_days, tz, start_expected, notes`, using sources confirmed in P01.

### T02.10 Loaders, schemas and the dictionary

- `esw.reference.load(name)` returns a validated DataFrame; pandera schemas enforce types, uniqueness, date ordering (`valid_from < valid_to`), allowed codes, and non-empty `source_url` for every row with `include = true` or `verified = y`.
- `esw reference validate` CLI runs all schemas and cross-table checks (T02.11) and writes `reports/data/reference_validation.md`.
- `reference/README.md` documents every column of every table.

### T02.11 Cross-table checks

1. Every `include = true` instrument has a `nav_clock` row covering its whole listing period.
2. Every Indian instrument has exactly one AMFI code and at least one NSE symbol in `symbol_history`.
3. No two Indian instruments share an NSE symbol on the same date.
4. Every `group` value is one of System Specification §5.1.
5. Feasible counts per group meet the P01 gate.
6. Duty table periods are contiguous and non-overlapping per metal; band-regime periods likewise per exchange and group.

## 5. Deliverables

| Path | Description |
|---|---|
| `reference/instruments_us.csv`, `instruments_in.csv`, `symbol_history.csv`, `nav_clock.csv`, `corporate_actions_manual.csv`, `duty_india.csv`, `band_regimes_india.csv`, `series_catalogue.csv`, `README.md` | Reference tables |
| `src/esw/reference/{loaders,schemas,calendars}.py`; CLI `esw reference validate`, `esw reference build-calendars` | Code |
| `data/curated/calendar.parquet` (preliminary) | US canonical; India preliminary |
| `reports/data/reference_validation.md` | Validation output |
| Tests: `tests/unit/test_reference_schemas.py`, `tests/acceptance/test_p02_acceptance.py` | Passing |

## 6. Tests and validation

- Schema tests with deliberately broken fixture rows (duplicate ISIN, overlapping periods, missing source) must fail.
- Calendar tests: 2026-02-01 is an Indian trading day (`special`); 2020-04-10 (Good Friday) is not a US trading day; the day after Thanksgiving is `half` in the US.
- Acceptance test runs `esw reference validate` with zero errors.

## 7. Acceptance criteria

| ID | Criterion |
|---|---|
| AC-02.1 | All tables exist, validate with zero schema errors, and every included or verified row has a `source_url` |
| AC-02.2 | Cross-table checks T02.11 pass |
| AC-02.3 | Mirae instruments listed in T02.2 are present, included (if feasible) and flagged `is_mirae = true` |
| AC-02.4 | `SILVRETF → SILVERAG` symbol history row exists with a verified date and source |
| AC-02.5 | NAV clock rows cover every included instrument and include the 2026-04-01 basis change for Indian gold/silver ETFs |
| AC-02.6 | Every duty and band-regime row is either `verified = y` with a primary source or listed in MI-09 |
| AC-02.7 | Calendar tests pass; the India calendar is explicitly marked preliminary in the walkthrough |

## 8. Verification checklist (orchestrator)

- [ ] Pick five Indian ISINs at random and confirm name, AMFI code and symbol against `NAVAll.txt` and a bhavcopy fixture.
- [ ] Confirm the GLD and SLV NAV-clock rows match the prospectus notes from P01.
- [ ] Confirm MI-09 lists exactly the unverifiable rows.

## 9. Risks and decision points

| Item | Handling |
|---|---|
| AMFI scheme names change over time | Key on ISIN and code; names are labels only |
| Unknown historical band rules before 2020 | Leave `verified = n`; lock class becomes `unknown`; headline metrics are not affected (only `confirmed_locked` is excluded) |
| Duty history unverifiable | Layer 1 restricted to verified periods; decision logged |

## 10. Walkthrough requirements

Record: counts of included/excluded instruments per group with reasons; every identifier conflict and its resolution; unverified rows and the MI-09 request; any change to the candidate universe and why.

## 11. Handoff

P03–P06 may now run in parallel. P04/P05/P06 read `include = true` instruments and the series catalogue. P07 will replace the preliminary India calendar with the bhavcopy-reconciled one.

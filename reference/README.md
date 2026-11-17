# Reference tables

Hand-checked, version-controlled tables that every other phase joins against (System Specification §3, §6.3; P02). Every row has a source. Load them with `esw.reference.load("<table>")`, which converts types and validates with the pandera schemas in `src/esw/reference/schemas.py`. Run `python -m esw reference validate` after any edit; it also runs the cross-table checks and writes `reports/data/reference_validation.md`.

Conventions: UTF-8 CSV; dates `YYYY-MM-DD`; empty cell = missing; booleans `true`/`false`; flags `y`/`n` (`unknown` where stated). Open-ended periods have an empty end date.

The first versions were assembled in P02 by `src/esw/reference/bootstrap_*.py` from logged raw files (see each module's docstring). After that, **these CSVs are the source of truth**: edit them by hand, with a source, and log corrections in `records/DECISIONS.md`.

## instruments_us.csv — one row per US candidate (System Specification §5.2)

| Column | Meaning |
|---|---|
| `instrument_id` | `US:<ticker>` (primary key) |
| `market` | `US` |
| `ticker` | Current ticker |
| `isin` | ISIN (iShares screener, or `US` + CUSIP + check digit) |
| `cusip` | Current CUSIP (iShares screener or SEC Official List of Section 13(f) Securities; quarter in `notes`). CUSIPs change on reverse splits |
| `cik` | SEC registrant CIK (SEC ticker files); used for EDGAR filings in P03/P04 |
| `name`, `issuer` | Fund name and sponsor |
| `group` | §5.1 group code |
| `subgroup` | `gold`, `silver`, `pgm`, `crude`, `natgas`, `broad_commodity`, `agri`, `ig_corp`, `hy_corp`, `muni`, `em_debt`, `loans`, `treasury`, `single_country_em`, `single_country_dm`, `regional`, `large_cap_us` |
| `underlying` | What the fund holds or tracks |
| `legal_form` | `open_end`, `uit`, `grantor_trust`, `commodity_pool`, `etn` |
| `rule_6c11` | Whether SEC Rule 6c-11 applies: `y`, `n`, `unknown` (P01 notes §1: registered open-end funds only) |
| `listing_date` | First trading day (Tiingo `startDate`), cross-checked with issuer inception |
| `delisting_date` | Last price date for delisted funds (Tiingo `endDate`); see `notes` for halts |
| `currency` | `USD` |
| `nav_source_id`, `px_source_id`, `shares_source_id` | Source IDs from `reference/source_registry.csv` |
| `include` | In the modelling universe (`true`/`false`) |
| `exclude_reason` | Required when `include = false` |
| `notes` | Free text: data status, MI-04 receipts, identifier sources |
| `source_url` | Issuer page or SEC EDGAR registrant page |
| `verified_by`, `verified_on` | Who checked the row and when |

## instruments_in.csv — one row per Indian ETF in scope (System Specification §5.3)

| Column | Meaning |
|---|---|
| `instrument_id` | `IN:<current ISIN>` (primary key) |
| `market` | `IN` |
| `isin` | Current ISIN (unique). Earlier ISINs of the same fund are in `notes` and `symbol_history.isin` |
| `amfi_scheme_code` | AMFI scheme code in the current `NAVAll.txt` (one per ISIN; conflicts are excluded as `mapping_conflict`) |
| `name`, `issuer` | AMFI scheme name; AMC |
| `is_mirae` | `true` for Mirae Asset schemes |
| `group` | `IN_GOLD`, `IN_SILVER`, `IN_INTL`, `IN_DEBT`, `IN_CTRL` (classified by name, D-007) |
| `subgroup`, `underlying`, `benchmark_name` | Descriptive, derived from the scheme name (benchmark blank where not obvious) |
| `nse_symbol_current` | NSE symbol in the 2026-11-16 bhavcopy |
| `bse_code` | BSE scrip code in the 2026-11-16 BSE bhavcopy |
| `listing_date` | First NSE bhavcopy appearance of the fund's lineage (monthly samples from 2007, exact day by bisection). Lower bound if listed before Feb 2007. P05 confirms with the full bhavcopy history |
| `inception_date` | First AMFI/mfapi NAV date (a proxy for inception; SID date in `notes` where read) |
| `creation_unit_units` | Units per creation unit (blank until read from the SID) |
| `include`, `exclude_reason` | As for the US table. Reasons: `liquid_overnight`, `too_short`, `not_listed_on_nse`, `mapping_conflict`, `delisted_or_merged` |
| `notes`, `source_url`, `verified_by`, `verified_on` | As above |

## symbol_history.csv — exchange symbols over time

| Column | Meaning |
|---|---|
| `instrument_id` | Instrument key |
| `exchange` | `NSE`, `BSE`, `NYSEARCA`, `NASDAQ`, `CBOE`, … |
| `symbol` | Ticker / NSE symbol / BSE scrip code |
| `isin` | ISIN the symbol traded under in this period (lets P05 map old bhavcopy rows) |
| `valid_from`, `valid_to` | First and last day (inclusive). Empty `valid_to` = current. Empty `valid_from` = not dated (BSE codes, US rows before the listing date is known) |
| `source_url` | Evidence |

Primary key: (`instrument_id`, `exchange`, `valid_from`).

## nav_clock.csv — when and how each NAV is struck

| Column | Meaning |
|---|---|
| `instrument_id`, `effective_from`, `effective_to` | Period (primary key `instrument_id, effective_from`); periods are contiguous and cover the listing period |
| `nav_basis` | `us_close_16et`, `lbma_pm`, `lbma_silver_noon`, `futures_settle`, `foreign_close`, `evaluated_bond`, `in_import_parity`, `in_domestic_spot`, `in_close` (§6.3) |
| `valuation_time_local`, `valuation_tz` | Clock time and IANA time zone of the valuation input (blank where there is no single time, e.g. EEM) |
| `source_url`, `notes` | Evidence; `[K]` marks well-known facts not yet checked against the prospectus (OQ-06) |

## corporate_actions_manual.csv — splits and unit changes (seed; P07 detects the rest)

| Column | Meaning |
|---|---|
| `instrument_id`, `ex_date`, `type` | `split`, `reverse_split`, `consolidation`, `unit_split`, `bonus` |
| `ratio` | New shares per old share (2-for-1 split = 2; 1-for-8 reverse split = 0.125) |
| `applies_to` | Which **raw** series shows the jump: `price`, `nav` or `both`. iShares NAV files are already split-adjusted, so their splits apply to `price` only |
| `verified` | `y` when two independent sources agree on date and ratio |
| `source_url`, `notes` | Evidence |

## duty_india.csv — import duty on gold and silver (Layer 1)

`metal, effective_from, effective_to, bcd_pct, aidc_pct, sws_pct, other_pct, total_pct, verified, source_url, notes`. Periods are contiguous from 2007-01-01. `total_pct` is blank where the duty was a specific (per-gram) duty. **Layer 1 is computed only for `verified = y` periods** (System Specification §4.4). Unverified rows carry an MI-09 item id (`MI-09 D<n>`) in `notes`. Customs changes announced in a Budget are taken as in force on the day after the Budget speech.

## band_regimes_india.csv — Indian ETF price-band rules (lock classification)

`market, exchange, group, effective_from, effective_to, base_rule (t2_nav|t1_nav|t1_vwap30), band_init_pct, flex_step_pct, flex_max (number of flexes allowed; blank = no cap), cooling_off_note, verified, source_url, notes`. Groups: `gold_silver`, `equity_debt`, `overnight`, `liquid`, `international`. Unverified rows carry `MI-09 B<n>`; lock class is `unknown` for them.

## series_catalogue.csv — market, underlying and FX series (§6.4)

`series_id, description, source_id, source_code, unit, frequency, publication_lag_days, tz, start_expected, notes`.

## calendar_overrides_in.csv — corrections to the preliminary India calendar

`date, is_trading (y|n), session_type, reason, apply (y|n), verified (y|n), source_url`. Used by `esw reference build-calendars` on top of the `exchange_calendars` XBOM sessions. A row is applied only when `apply = y`; NSE bhavcopy presence is the evidence. P05/P07 replace the India calendar with the bhavcopy-derived one.

## calendar_xath_sessions.csv — Athens trading days

One column `date`: days with Athens General Index (`GD.AT`, yfinance) data, used for the `XATH` calendar (Athens is not in `exchange_calendars`). The 29 Jun – 31 Jul 2015 closure appears as non-trading days.

## source_registry.csv — data sources and fallbacks (P01)

Built in P01; see `reports/data/source_probe_report.md`.

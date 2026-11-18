# Quality report (P07)

**DATA_CUTOFF = 2026-11-16** (latest date with price and NAV for ≥ 90% of included instruments in both markets).

## Precedence used

- US prices: Tiingo raw (all instruments; yfinance fallback not needed). US NAV: the issuer source in `instruments_us.nav_source_id`.
- India prices: NSE bhavcopy (BSE fallback not needed). India NAV: AMFI history, mfapi for dates AMFI lacks.
- Rows: px_daily 398,121; nav_daily 328,730 (3,278 from mfapi); India price rows mapped by symbol 10,925.

## Flags by check and severity

| check_id      | severity   |   n |
|:--------------|:-----------|----:|
| gap_gt_25pct  | warn       | 212 |
| nav_spike     | warn       |  14 |
| nav_stale_run | info       | 372 |

## Errors and resolution

Split candidates (`error`) found on the first build: 24, all in Indian ETFs where price and NAV change unit basis on different days (often with an ISIN change). Each was resolved by a verified `unit_split` row (price leg and NAV leg dated separately) in `reference/corporate_actions_manual.csv`; ICICI's 2018-07-03 seed row was dropped (no jump; a gap in the mfapi history). **Unresolved errors: 0.**

Corporate actions applied: 60 (23 US, 37 India).

USO reference test: premium +838 bps (20 Apr 2020), +3,641 (21 Apr), +866 (22 Apr), +145 (1 May); continuous across the 1-for-8 reverse split on 29 Apr (both legs adjusted).

## |close/NAV − 1| > 25% (`warn`), all annotated

| instrument_id   |   days |
|:----------------|-------:|
| IN:INF204KB19I1 |      3 |
| IN:INF247L01AP3 |      5 |
| IN:INF247L01AU3 |     49 |
| IN:INF769K01HF4 |     61 |
| IN:INF769K01HP3 |     47 |
| IN:INF769K01HS7 |     45 |
| US:EWH          |      1 |
| US:USO          |      1 |

Annotations: incident windows from `reference/incidents.csv` (Indian international ETFs under the overseas cap; USO 21 Apr 2020) and `reference/gap_annotations.csv` (EWH Oct 1997, Hang Seng BeES Mar 2020, N100 2018, Axis gold split day).

## NAV spikes (`warn`, excluded from labels in P08)

Rule: NAV return beyond 5 robust SD on t and t+1 with opposite signs, NAV back near its previous level, and the price making neither move. These are timing artefacts on volatile days (London-fixed SLV, Asian closes, Indian March-2020 NAVs).

| instrument_id   | date                |
|:----------------|:--------------------|
| IN:INF200KA1FS1 | 2020-03-31 00:00:00 |
| IN:INF247L01AP3 | 2020-03-13 00:00:00 |
| IN:INF247L01AP3 | 2020-03-16 00:00:00 |
| IN:INF754K01KO2 | 2020-03-20 00:00:00 |
| IN:INF754K01KO2 | 2020-03-31 00:00:00 |
| US:BNO          | 2020-03-18 00:00:00 |
| US:EEM          | 2020-03-20 00:00:00 |
| US:EMB          | 2008-10-14 00:00:00 |
| US:EWH          | 2008-01-22 00:00:00 |
| US:EWJ          | 2016-02-12 00:00:00 |
| US:FXI          | 2008-01-22 00:00:00 |
| US:MUB          | 2020-04-02 00:00:00 |
| US:SLV          | 2011-05-12 00:00:00 |
| US:SLV          | 2011-09-26 00:00:00 |

## Stale NAV runs (`info`)

372 runs of ≥ 3 unchanged NAVs; kept (often a closed-market signal).

## Final coverage

Included instruments: 106 (38 US, 68 India). Per-instrument coverage: `reports/data/coverage_us.md`, `coverage_in.md`.

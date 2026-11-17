# P02 Acceptance Report — Reference Data: Universe, Identifiers, Calendars, NAV Clocks and Regime Tables

| Field | Value |
|---|---|
| Phase | P02 |
| Prepared by / date | Claude Code (executing agent), 2026-11-18 |
| Verified by / date | Claude Code, same session, by re-running the tests, `esw reference validate` and the checklist below (no fresh-session verification) |
| Git commit evaluated | working tree on top of a95d1c4, committed as the P02 commit |
| Overall result | **PASS** (MI-09 requested for 21 unverified duty/band rows; these are excluded from Layer 1 / lock classification until confirmed, as the phase allows) |

## 1. Test suite

| Command | Result |
|---|---|
| `pytest -q` | 100 passed |
| `pytest tests/unit/test_reference_schemas.py tests/acceptance/test_p02_acceptance.py -q` | 31 passed |
| `ruff check .` / `ruff format --check .` | All checks passed / 51 files already formatted |
| `python -m esw reference validate` | 0 errors, 2 warnings (the MI-09 rows) — `reports/data/reference_validation.md` |
| `python -m esw reference build-calendars` | 80,554 rows → `data/curated/calendar.parquet` (run `20261117-191319_calendars`) |

## 2. Acceptance criteria

| ID | Criterion | Result | Evidence |
|---|---|---|---|
| AC-02.1 | All tables exist, validate with zero schema errors, every included or verified row has a `source_url` | PASS | 10 tables in `reference/` + `README.md`; pandera schemas enforce `source_url` when `include = true` / `verified = y`; `test_tables_validate`, `test_ac_02_1_*` |
| AC-02.2 | Cross-table checks T02.11 pass | PASS | `reference_validation.md` "Checks run": NAV-clock coverage, one AMFI code + NSE symbol per included Indian ETF, no shared NSE symbol on a date, group codes, gate, contiguous duty/band periods |
| AC-02.3 | Mirae instruments present, included, `is_mirae = true` | PASS | GOLDETF, SILVERAG, MAFANG, MASPTOP50, MAHKTECH, NIFTYETF (control), plus Mirae debt ETFs; `test_ac_02_3_mirae_instruments` |
| AC-02.4 | `SILVRETF → SILVERAG` row with a verified date and source | PASS | `symbol_history`: MASILVER 2023-06-15 → 2023-08-31; SILVRETF 2023-09-01 → 2025-09-14; SILVERAG from **2025-09-15**, dated from NSE bhavcopies (first file with SILVERAG) |
| AC-02.5 | NAV clocks cover every included instrument, incl. the 2026-04-01 change for Indian gold/silver ETFs | PASS | 158 rows; every included gold/silver ETF has `in_import_parity` to 2026-03-31 and `in_domestic_spot` from 2026-04-01 (SEBI circular 26 Feb 2026) |
| AC-02.6 | Every duty and band row is `verified = y` with a primary source or listed in MI-09 | PASS | Duty: 8 of 19 rows verified (Budget speeches/annexes 2012, 2019, 2021, 2023, 2024); 11 rows → MI-09 D1–D7. Bands: 4 of 14 verified (NSE circular 122/2026); 10 → MI-09 B1–B4. `test_ac_02_6_unverified_rows_listed_in_mi09` |
| AC-02.7 | Calendar tests pass; India calendar marked preliminary | PASS | 2026-02-01 India `special`; 2020-04-10 US closed; day after Thanksgiving `half`; Athens 2015 closure; India calendar stated as preliminary in the walkthrough |

## 3. Deliverables present

| Deliverable | Path | Present |
|---|---|---|
| Reference tables | `reference/{instruments_us,instruments_in,symbol_history,nav_clock,corporate_actions_manual,duty_india,band_regimes_india,series_catalogue,calendar_overrides_in,calendar_xath_sessions}.csv`, `reference/README.md` | Yes |
| Code | `src/esw/reference/{loaders,schemas,calendars,validate}.py` (+ `bootstrap_*.py` builders); CLI `esw reference validate`, `esw reference build-calendars`, `esw manual-register`; `esw.ingest.nse_bhav`, `esw.ingest.manual`, new parsers | Yes |
| Calendar | `data/curated/calendar.parquet` (gitignored; rebuild with the CLI) | Yes |
| Validation report | `reports/data/reference_validation.md` | Yes |
| Tests | `tests/unit/test_reference_schemas.py` (25), `tests/acceptance/test_p02_acceptance.py` (6), parser tests for the MI-04/MI-05 files (4) | Yes |

## 4. Global Definition of Done

- [x] 1 Deliverables exist
- [x] 2 Tests and lint pass
- [x] 3 All criteria evaluated
- [x] 4 Acceptance report and walkthrough written
- [x] 5 Records updated (STATUS, PROGRESS_LOG, DECISIONS D-010–D-014, ISSUES I-001/I-003/I-005 updated and I-006 opened, OPEN_QUESTIONS, MANUAL_ACTIONS)
- [x] 6 Manual interventions: MI-04 essentials and MI-05 VERIFIED; MI-06 DECLINED (D-011); MI-09 REQUESTED (phase allows unverified rows to be listed)
- [x] 7 Committed and pushed under D-003

## 5. Orchestrator verification checklist

| Check | Result |
|---|---|
| Five random Indian ISINs: name, AMFI code, symbol vs `NAVAll.txt` and bhavcopy | 5/5 match (INF109KC1Y56 SILVERIETF, INF846K01W80 GOLDAXIS, INF769K01HP3 MASPTOP50, INF204KB1882 LTGILTBEES, INF769K01KF8 GSEC10YEAR; seed 20261117) |
| GLD and SLV NAV-clock rows match P01 notes | GLD `lbma_pm` 15:00 London (issuer label 10:30am NY); SLV `lbma_silver_noon` 12:00 London |
| MI-09 lists exactly the unverifiable rows | Every `verified = n` duty/band row carries an MI-09 item id that appears in the MI-09 list (acceptance test) |

## 6. Defects found during verification

- Indian ETF classifier treated "Nippon India ETF Hang Seng BeES" as domestic ("India" in the AMC name) and a hybrid ETF as debt. Fixed in `classify_india`; HNGSNGBEES added to `IN_INTL`.
- Lineage builder split one symbol period into several when an illiquid ETF did not trade on a sample day, and missed N100 → MON100 (symbol and ISIN changed together). Fixed (gap merging; `MANUAL_LINKS`).
- P01 statement that the USCF NAV download is split-adjusted was wrong (D-014; OQ-04 amended).

## 7. Sign-off

- Executing agent: Claude Code, 2026-11-18
- Orchestrator: Claude Code (same session), 2026-11-18

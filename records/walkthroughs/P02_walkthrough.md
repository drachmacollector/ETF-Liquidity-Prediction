# P02 Walkthrough — Reference Data: Universe, Identifiers, Calendars, NAV Clocks and Regime Tables

| Field | Value |
|---|---|
| Phase | P02 |
| Status at time of writing | VERIFIED |
| Period | 2026-11-17 → 2026-11-18 |
| Sessions | 1 |
| Author | Claude Code |
| Git commit at end | the commit titled "P02: build the reference tables and trading calendars" |

## 1. Entry conditions

- [x] P01 VERIFIED (a95d1c4), with `universe_feasibility.md` and `source_registry.csv`.
- [x] User reported MI-04 (USO, UNG, BNO, CPER, GREK), MI-05 (MCX gold and silver spot, IBJA 30 days) done and MI-06 not possible (no WRDS).
- [x] User instruction recorded first: automation over manual steps, browser-like clients allowed (D-010).

## 2. Manual items received and checked

| Item | What arrived | Check | Result |
|---|---|---|---|
| MI-04 USO, UNG | USCF NAV CSVs, 2009-01-02 → 2026-11-16 (4,496 rows each) | Parsed (`parse_uscf_navhist`), no duplicate dates | OK. **Not split-adjusted** (USO ×8.44 on 2020-04-29; UNG 4 reverse splits) → D-014. History starts 2009, not at inception (USO 2006, UNG 2007): the 2008 period has no NAV |
| MI-04 BNO, CPER | Same format, from 2010-06-02 / 2011-11-15 | Parsed | OK; BNO's NAV changes basis on 2013-08-28, one day before the price ex-date |
| MI-04 GREK | Global X premium/discount CSV 2015-04-13 → 2026-11-16 (+ a holdings file) | NAV = close − premium ($) | **Correct data.** Covers the 2015 Athens closure (29 Jun – 31 Jul 2015): premium up to +8.35% on 9 Jul 2015. 28 zero placeholder rows dropped. 1-for-3 reverse split on 2020-04-28 visible (raw prices). No shares outstanding; starts 2015, not 2011 |
| MI-05 | MCX "Spot Market Price" exports (HTML saved as .xls): gold 10 g and silver 1 kg, Ahmedabad, 2–5 polls a day | Parsed (`parse_mcx_spot`) | Gold 2005-06-06 → 2026-11-17 (5,758 days), silver 2005-05-14 → 2026-11-17. Purity not stated (OQ-24). IBJA 30-day PDF kept as a cross-check only |
| MI-06 | Institution not registered with WRDS | — | DECLINED; D-011 |

All nine files are logged (`status = manual`, SHA-256, rows, date range) by the new `esw manual-register`.

## 3. What was completed

- T02.1 `instruments_us.csv`: 50 rows; ISIN/CUSIP for all (iShares screener; SEC 13(f) list 2026Q3, 2021Q4/2023Q4 for delisted), SEC CIK, legal form and Rule 6c-11 flag, listing/delisting dates (Tiingo), sources. Done.
- T02.2 `instruments_in.csv`: 100 rows built from `NAVAll.txt`, NSE/BSE bhavcopies and mfapi. Done.
- T02.3 `symbol_history.csv`: 293 rows; NSE periods dated from bhavcopies. Done.
- T02.4 `nav_clock.csv`: 158 rows for every included instrument. Done.
- T02.5 Calendars: `data/curated/calendar.parquet` — XNYS (canonical), XNSE (**preliminary**), XLON, XHKG, XTKS, XSHG, BVMF, XMEX, XIST, XATH. Done.
- T02.6 `corporate_actions_manual.csv`: 23 US rows (all verified), 22 Indian unit-split candidates (unverified). Done.
- T02.7 `duty_india.csv`: 19 rows, 8 verified. Done (MI-09).
- T02.8 `band_regimes_india.csv`: 14 rows, 4 verified. Done (MI-09).
- T02.9 `series_catalogue.csv`: 22 series. Done.
- T02.10 Loaders, pandera schemas, `esw reference validate`, `reference/README.md`. Done.
- T02.11 Cross-table checks: all pass. Done.

## 4. Universe: counts and reasons

**US (50 candidates, 47 included):**

| Group | Included | Excluded | Notes |
|---|---|---|---|
| US_COMM_PHYS | 7 | 0 | SIVR, PPLT, PALL NAV pending (P04) |
| US_COMM_FUT | 15 | 0 | NAV in hand: USO, UNG, BNO, CPER, GSG. Pending: UGA, USL, UNL, USCI, DBC, DBA, DBO, CORN, WEAT, SOYB |
| US_BOND | 9 | 0 | BKLN, BND pending |
| US_INTL | 10 | 3 | RSX, EGPT, ERUS: `nav_unavailable (I-005)`. GREK in hand; ASHR pending |
| US_CTRL | 6 | 0 | QQQ, VOO pending |

"Pending" rows stay `include = true` (D-012) and flip to `false` in P04 if both automation (D-010) and MI-04 fail.

**India (100 rows, 68 included):**

| Group | Included | Excluded | Exclusion reasons |
|---|---|---|---|
| IN_GOLD | 23 | 5 | 3 too short (< 250 NAV days), 2 delisted/merged (MGOLD, RELGOLD) |
| IN_SILVER | 16 | 3 | too short |
| IN_INTL | 6 | 0 | MAFANG, MASPTOP50, MAHKTECH, MON100, MONQ50, HNGSNGBEES (new) |
| IN_DEBT | 17 | 24 | 20 liquid/overnight (Spec §5.3), 2 too short, 2 no longer on NSE (matured) |
| IN_CTRL | 6 | 0 | NIFTYBEES, SBINIFTY50, BANKBEES, JUNIORBEES, SENSEXIETF, NIFTYETF (Mirae) |

Changes to the candidate universe and why: HNGSNGBEES added (classifier bug fixed); SENSEXIETF and Mirae NIFTYETF added as controls; SETFNIF50 is now SBINIFTY50 (renamed 2026-10-30); delisted gold ETFs kept for survivorship; the Mirae hybrid ETF dropped (out of scope).

## 5. Identifier conflicts and resolutions

1. **Symbol and ISIN changes are common in India.** 33 funds in the table changed NSE symbol and 21 changed ISIN (AMC mergers, renames). The key is the current ISIN; each (symbol, ISIN) period is in `symbol_history` with exact dates from bisection of bhavcopies (D-012). Examples: GOLDBEES ISIN INF732E01102 → INF204KB17I5 on 2019-12-20; ICICI gold ETF IPGETF → IGOLD → GOLDIWIN → ICICIGOLD → GOLDIETF with three ISINs; IDBIGOLD → LICMFGOLD (new ISIN 2026-03-06); N100 → MON100 (2021-06, linked by hand).
2. **Mirae Silver ETF:** inception 2023-06-09 (SID; preferred over the first NAV 2023-06-12 per the OQ-18 rule). Symbols MASILVER (from 2023-06-15) → SILVRETF (2023-09-01) → **SILVERAG (2025-09-15)**, confirmed from bhavcopies.
3. **No ISIN with two AMFI codes** among in-scope ETFs; four liquid ETFs without a growth ISIN are excluded anyway.
4. **US CUSIPs change on reverse splits** (USO, UNG, IAU): current CUSIP recorded, note added.
5. **QQQ legal form:** SEC now lists QQQ as a fund series, suggesting a UIT → open-end conversion; `legal_form = uit`, `rule_6c11 = unknown` until checked (OQ-25).

## 6. Key findings

1. **Automation unlocked more data (D-010):** NSE bhavcopies are scriptable back to **2007** on `nsearchives.nseindia.com` (P01: 2016), so Indian prices for the 2008 and 2013 gold episodes are now reachable in P05. The BSE bhavcopy downloads too (BSE scrip codes added).
2. **Splits:** all 22 US split events confirmed by yfinance and Tiingo `splitFactor` on the same day and ratio. iShares NAV files are split-adjusted; SPDR Gold, SSGA and USCF NAV files are not. 22 Indian unit splits (×10, ×50, ×100) found in NAV; the NSE close did not jump on the same days, so price and NAV change basis on different dates (P07 dates the price leg).
3. **Import duty:** confirmed from Budget documents: gold 4% (Mar 2012), 12.5% (Jul 2019), 10.75% (Feb 2021), 6% (Jul 2024); silver 12.5%, 10.75%, 15% (Feb 2023), 6%. The Budget 2026-27 speech made no change. A rise to 15% on 13 May 2026 is reported (unverified, MI-09 D7). Layer 1 is computed only for verified periods (D-013).
4. **Price bands:** NSE circular 122/2026 (verified) gives the 7 Sep 2026 rules: base = T-1 last-30-minute VWAP; gold/silver ±6% with 3% flexes; equity/debt ±10% flexing by 5% up to ±20%; liquid/overnight ±5%. BSE's 1 Feb 2026 switch to T-1 NAV applied for that day only (reports).
5. **India calendar (preliminary):** XBOM sessions plus 29 checked overrides. All 20 Muhurat sessions 2007–2026, Budget sessions (2015, 2020, 2025, 2026) and three Saturday sessions in 2024 confirmed by bhavcopy files. XBOM holidays 2024–2026 and 2026 sessions agree with NSE file presence. P05/P07 build the full bhavcopy-derived calendar.
6. **Athens calendar** built from Athens General Index data (Athens is missing from `exchange_calendars`); the 2015 closure shows as non-trading days. Cairo and Moscow are not built (no feasible instrument).

## 7. Decisions made

| ID | Decision | Decided by |
|---|---|---|
| D-010 | Automation first; browser-like clients allowed | User |
| D-011 | No CRSP | User (fact) / agent |
| D-012 | Universe and identifier rules (current-ISIN key, lineages, pending US rows, controls) | Agent |
| D-013 | Duty/band conventions (Budget + 1 day; primary sources only for `verified = y`) | Agent |
| D-014 | Correction: USCF NAV not split-adjusted | Agent (evidence) |

## 8. Deviations from the plan

| Planned | Actual | Reason | Impact |
|---|---|---|---|
| Hand-typed reference tables | Assembled by `src/esw/reference/bootstrap_*.py` from logged raw files, then reviewed | 100+ Indian rows and dated symbol periods are error-prone by hand | Tables are the source of truth from now on (README) |
| `symbol_history` columns per spec | Extra `isin` column; extra `cik` column in `instruments_us` | Needed to map old bhavcopy rows and EDGAR filings | Documented in README and D-012 |
| `listing_date` from SID/notices where unknown | First bhavcopy appearance by bisection (from 2007) | Data-based and scripted | Thin ETFs may show a late date (I-006); P05 confirms |
| India calendar from XBOM only | XBOM + bhavcopy-checked overrides | Cheap to verify specials | Still preliminary |

## 9. Issues

I-001 and I-005 updated (no CRSP). I-003 updated (predecessor ISINs found; old AMFI codes still needed in P05). I-006 opened (thin ETFs' listing dates). None blocks P03–P06.

## 10. Unverified rows and the MI-09 request

MI-09 REQUESTED with 11 items: D1–D7 (duty: specific duties before 2012; Jan 2012, Jan/Jun/Aug 2013 changes; the 2022 effective date; May 2026) and B1–B4 (pre-Sep-2026 band rule history, international ETFs, BSE Feb 2026, BSE Sep 2026). List in `records/MANUAL_ACTIONS.md`.

## 11. Exact current state

- Data: raw NSE bhavcopies 1,024 files (2007–2026 monthly samples plus bisection and calendar days) in `data/raw/in_bhav/`; BSE bhavcopy 2026-11-16; SEC 13(f) lists and ticker files; Budget speeches; NSE circular; Athens index; manual drops logged. 1,409 lines in the ingest log.
- Reference: 10 tables validated; calendar parquet built.
- Tests: 100 passed.

## 12. How to reproduce

```
.venv/Scripts/python.exe -m esw manual-register
.venv/Scripts/python.exe -m esw reference build-calendars
.venv/Scripts/python.exe -m esw reference validate
.venv/Scripts/python.exe -m pytest -q
```

(The bootstrap builders are one-off; rerunning them overwrites hand edits.)

## 13. Handoff

P03–P06 can start. P04 reads `instruments_us` (`include = true`), retries the pending issuer NAV files automatically (D-010) and uses `corporate_actions_manual` for split bases. P05 uses `instruments_in`, `symbol_history` (with `isin`) to map bhavcopy rows from 2007, finds predecessor AMFI codes (I-003), confirms listing dates (I-006) and builds the bhavcopy calendar. P06 uses `series_catalogue`. P03 uses `cik` for EDGAR filings.

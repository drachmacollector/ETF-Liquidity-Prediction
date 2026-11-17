# P01: Source Verification and Access Probes

| Field | Value |
|---|---|
| Phase ID | P01 |
| Depends on | P00 |
| Unlocks | P02 |
| Estimated effort | 2–3 days |
| Manual interventions | **MI-02** (Tiingo API key), **MI-03** (FRED key, optional), **MI-04** (manual issuer downloads, if probes are blocked), **MI-05** (manual Indian data, if blocked), **MI-06** (WRDS/CRSP check, optional), **MI-07** (terms-of-use acceptance) |
| Canonical references | Research Document §9 (data landscape), §13 (open questions); System Specification §5 (universe), §6 (data contracts), §11 (polite access) |

## 1. Purpose

Find out, **before writing any production ingestion code**, exactly which data can be obtained, from where, how far back, in what format, under what terms, and with what failure modes. The project's largest risk is that US daily NAV history is not obtainable for key ETFs (Research Document §10.1). This phase retires or confirms that risk cheaply, settles the open questions that are answerable by reading primary sources, and decides whether the planned universe is feasible.

## 2. Scope

**In scope:** small, polite probes of every source family; saving small sample files as golden fixtures; reading primary regulatory texts needed for definitions; recording terms of use; a feasibility decision on the universe.

**Out of scope:** full backfills (P04–P06); building curated tables (P07).

## 3. Prerequisites

- [ ] P00 `VERIFIED`.
- [ ] `ESW_ALLOW_NETWORK=1` set in `.env` for this phase.
- [ ] MI-02 started (the Tiingo probe needs the key; other probes do not).

## 4. Implementation specification

### T01.1 Probe framework

Add `src/esw/ingest/probe.py` and CLI `esw probe <source_id> [--instrument …]`. Each probe:

1. Makes at most 3 requests (or the minimum needed to see full history once), with the user agent and rate limit from settings.
2. Saves raw responses to `data/raw/_probes/<source_id>/…` and logs each in `ingest_log.jsonl` with `status`.
3. Parses enough to report: earliest date, latest date, number of rows, column names, presence of NAV / shares outstanding / OHLC / volume, whether prices are adjusted, split handling if visible.
4. Writes one row per (source, instrument or scope) to `reports/data/source_probe_matrix.csv`.

Probe-matrix columns: `source_id, scope, instrument_id, url_pattern, method (api|file|scrape|manual), auth (none|key|login), status (OK|PARTIAL|BLOCKED|MANUAL_ONLY|NOT_FOUND), history_start, history_end, fields, adjusted (y/n/unknown), rate_limit_note, tos_url, tos_summary, notes`.

### T01.2 Probes to run (US)

| Source ID | What to probe | Instruments | Key questions |
|---|---|---|---|
| `us_px_tiingo` | Tiingo daily EOD endpoint | 5 instruments: GLD, USO, LQD, EGPT, SPY | Raw (unadjusted) close available? Split factor field? History depth? Free-tier limits? |
| `us_px_stooq` | Stooq daily CSV | Same 5 | Still downloadable without login? Adjusted or raw? |
| `us_px_yf` | yfinance (fallback only) | Same 5 | Raw close available (`auto_adjust=False`)? |
| `us_iss_spdr_gold` | SPDR Gold "Historical Archive (XLSX)" on the GLD page | GLD (and GLDM if offered) | Columns (NAV, close, LBMA price, ounces, shares outstanding, mid at NAV time?), start date |
| `us_iss_ishares` | iShares fund-page data download (historical NAV / shares) | SLV, IAU, LQD, HYG, ERUS, EWJ, IVV | Full history or truncated? Shares outstanding present? Format (XLS-as-XML is common) |
| `us_iss_ssga` | SSGA NAV history download | JNK, SPY | As above |
| `us_iss_uscf` | USCF historical data | USO, UNG, BNO | NAV, shares, split basis around 2020 reverse split |
| `us_iss_invesco` | Invesco NAV/price history | DBC, DBA, BKLN, QQQ | Depth |
| `us_iss_vaneck` | VanEck NAV history | EGPT, RSX (likely delisted) | Availability; liquidation removal |
| `us_iss_globalx`, `us_iss_xtrackers`, `us_iss_abrdn`, `us_iss_teucrium`, `us_iss_vanguard` | Per-issuer pages | GREK; ASHR; SIVR/PPLT/PALL; CORN/WEAT; BND/VOO | Availability and depth |
| `us_wayback` | Wayback Machine CDX API for archived NAV files of delisted funds | RSX, ERUS, EGPT | Are archived daily files available? |
| `us_edgar` | SEC EDGAR full-text search / filing index | USO, UNG | Can filings (8-K, S-3, 10-Q) be listed and fetched with a compliant user agent? |

SEC EDGAR requires a descriptive User-Agent with contact information under its fair-access policy. Use a generic project identifier; if EDGAR rejects it, record the probe as `MANUAL_ONLY` and handle filings by hand in P03. Do not insert the user's email address without asking (MI-07 records the user's decision).

### T01.3 Probes to run (India)

| Source ID | What to probe | Key questions |
|---|---|---|
| `in_bhav_udiff` | NSE UDiFF CM bhavcopy for 2024-07-08, 2025-10-09, 2026-02-01 (Sunday special session), latest | URL works on the archive host? Column names (`TckrSymb`, `ISIN`, `ClsPric`, `TtlTradgVol`, `TtlTrfVal`, `TtlNbOfTxsExctd`, `SctySrs` …)? |
| `in_bhav_legacy` | Legacy CM bhavcopy for 2007-03-xx, 2013-08-xx, 2020-03-19, 2024-07-05 | URL pattern; columns; ETF series |
| `in_bse_bhav` | BSE equity bhavcopy (one recent day) | Fallback viability |
| `in_amfi_navall` | `NAVAll.txt` | Format; fields; ISIN columns |
| `in_amfi_hist` | AMFI NAV history (new format), one 90-day window for one scheme | Endpoint, parameters, format |
| `in_mfapi` | `api.mfapi.in/mf/<scheme_code>` for Mirae Silver ETF and Nippon Gold BeES | Full history? Matches AMFI on overlapping dates? |
| `in_mcx` | MCX bhavcopy / spot polled prices pages | Automatable? History depth? |
| `in_ibja` | IBJA historical rates | Automatable? History depth? |
| `in_indiavix` | NSE India VIX history | Download method |
| `in_amfi_aum` | AMFI monthly scheme-wise AUM | Format; depth |

### T01.4 Probes to run (market-wide and underlying)

| Source ID | Probe | Key questions |
|---|---|---|
| `mkt_fred` | FRED CSV (`fredgraph.csv?id=VIXCLS`) and API (if key) | `VIXCLS`, `BAA10Y`, `DGS10`, `DTWEXBGS`, `DEXINUS`, a ruble series; history; whether ICE BofA OAS history is truncated (OQ-09) |
| `mkt_eia` | EIA NYMEX futures (crude and natural gas contracts 1–4) | Last available date (OQ-08) |
| `mkt_fut_yf` | yfinance `GC=F`, `SI=F`, `CL=F`, `NG=F` and specific contract tickers | Continuous series history; whether contract-specific series exist for the curve after 2024 |
| `mkt_cal` | `exchange_calendars` for XNYS, XBOM, XLON, XHKG, XTKS, XSHG, XCAI?, XATH?, MISX? | Which needed calendars exist; record gaps (closures like Egypt 2011 and Moscow 2022 are unscheduled and go to the event table regardless) |

### T01.5 Primary-text reading (closing open questions)

Read and summarise (with page/section references) into `reports/data/primary_text_notes.md`:

1. 17 CFR 270.6c-11 and the adopting release's scope section → close **OQ-01**.
2. SEBI circular of 26 Feb 2026 on gold/silver valuation (PDF in Research Document §16) and any AMFI implementation notice → close or narrow **OQ-14**, inform **OQ-10**.
3. Current direct-redemption trigger wording (master circular or a 2026 SID) → **OQ-16**.
4. NSE closing-price methodology → **OQ-02**.
5. Prospectus "net asset value" sections for GLD, SLV, USO, LQD, EGPT → **OQ-06** (valuation clocks).
6. Mirae Silver ETF and Gold ETF SIDs: valuation method, creation unit size → **OQ-10**.

If a site blocks automated reading, record it and add the item to MI-09 (the user verifies by hand).

### T01.6 Terms of use

For each source, record the terms-of-use URL and a two-line summary (research use allowed? redistribution? rate limits? attribution?) in the probe matrix. Compile a one-page summary `reports/data/terms_of_use_summary.md` and ask the user to complete **MI-07**.

### T01.7 Golden fixtures

Copy a small, representative sample of each successfully probed format to `tests/fixtures/<source_id>/` (trim to ≤ 200 rows; keep headers exactly). These become the golden files for parser tests in P04–P06. Do not commit full vendor files.

### T01.8 Universe feasibility decision

Using the probe matrix, fill `reports/data/universe_feasibility.md` with, per candidate in System Specification §5.2–5.3: NAV source and depth, price source and depth, shares outstanding (y/n), status (`FEASIBLE`, `FEASIBLE_MANUAL`, `INFEASIBLE`). Apply the **feasibility gate**:

| Group | Minimum feasible instruments | Must include |
|---|---|---|
| `US_COMM_PHYS` | 3 | GLD, SLV |
| `US_COMM_FUT` | 4 | USO, UNG |
| `US_BOND` | 4 | LQD |
| `US_INTL` | 4 | at least one of EGPT / GREK / RSX / ERUS with NAV through its stress window |
| `US_CTRL` | 3 | SPY or IVV |
| `IN_GOLD` + `IN_SILVER` | 10 | Mirae `GOLDETF` and `SILVERAG` |
| `IN_INTL` | 3 | Mirae `MAFANG` |

If the gate fails, stop and raise a decision for the user with options: (a) manual downloads (MI-04), (b) CRSP via WRDS (MI-06), (c) narrower universe with a stated loss of mechanism coverage. Record the outcome as a decision.

### T01.9 Fill `sources` in settings

Add every working source with its URL pattern, method, rate limit and fallback order to `config/settings.yaml` and create `reference/source_registry.csv` (one row per source; columns as the probe matrix minus instrument-level fields).

## 5. Deliverables

| Path | Description |
|---|---|
| `src/esw/ingest/probe.py`, CLI `esw probe` | Probe framework |
| `reports/data/source_probe_matrix.csv` | One row per probe |
| `reports/data/source_probe_report.md` | Narrative: what works, what does not, fallbacks, risks |
| `reports/data/primary_text_notes.md` | Summaries of primary texts with references |
| `reports/data/terms_of_use_summary.md` | For MI-07 |
| `reports/data/universe_feasibility.md` | Per-candidate feasibility and gate outcome |
| `reference/source_registry.csv` | Sources and fallbacks |
| `tests/fixtures/<source_id>/…` | Golden samples |
| `tests/unit/test_probe_*.py` | Parsing tests on fixtures (offline) |
| Updated `records/OPEN_QUESTIONS.md` | OQ-01, 02, 03, 06, 07, 08, 09, 10, 13, 14, 16, 23 updated |

## 6. Tests and validation

- Offline unit tests parse every fixture and assert the expected columns and date range.
- The acceptance test reads `source_probe_matrix.csv` and checks that every source in T01.2–T01.4 has a row with a non-empty status, and that no `OK` row lacks `history_start`.

## 7. Acceptance criteria

| ID | Criterion |
|---|---|
| AC-01.1 | Every source listed in T01.2–T01.4 has been probed (or marked `MANUAL_ONLY`/`BLOCKED` with the error recorded) |
| AC-01.2 | For every US and Indian candidate instrument, NAV and price availability and depth are recorded in `universe_feasibility.md` |
| AC-01.3 | The feasibility gate (T01.8) is evaluated; if failed, a user decision is recorded before P01 is closed |
| AC-01.4 | OQ-01, OQ-02, OQ-03, OQ-08, OQ-13, OQ-14 and OQ-16 are each either RESOLVED (with evidence) or have an adopted DEFAULT recorded with rationale |
| AC-01.5 | Golden fixtures exist for every source with status OK or PARTIAL, and parser tests pass offline |
| AC-01.6 | Terms-of-use summary written; MI-07 status is DONE (or the phase is closed as `VERIFIED_WITH_PENDING` and MI-07 becomes an entry condition of P04–P06) |
| AC-01.7 | No probe exceeded the rate limits in settings (check timestamps in `ingest_log.jsonl`) |

## 8. Verification checklist (orchestrator)

- [ ] Open `source_probe_matrix.csv`; confirm GLD, SLV, USO, UNG, LQD rows show NAV history start dates close to fund inception (or explain why not).
- [ ] Confirm the USO probe shows how the April 2020 reverse split appears in both price and NAV sources.
- [ ] Confirm a legacy and a UDiFF bhavcopy fixture both exist and parse.
- [ ] Confirm the manual interventions triggered by blocked sources are listed in `records/MANUAL_ACTIONS.md` with status REQUESTED.

## 9. Risks, unresolved issues and decision points

| Item | Handling |
|---|---|
| Issuer sites block scripts | Mark `MANUAL_ONLY`; request MI-04 with an exact file list |
| Issuer history truncated (e.g., last 5 years only) | Check Wayback archives; consider CRSP (MI-06); otherwise accept shorter history and note the loss of events |
| Delisted funds unavailable | Keep incidents as catalogue-only references (P03) |
| MCX/IBJA not automatable | MI-05; if impossible, Layer 1 is restricted (Research Document §10.1) and the decision is logged |
| A source's terms prohibit automated access | Do not automate it; use manual download (if terms allow personal download) or drop it |

## 10. Walkthrough requirements

Record: the probe matrix summary; every blocked source and the fallback chosen; resolved open questions with one-line answers; the feasibility gate outcome; the list of manual interventions requested and their status.

## 11. Handoff to P02

P02 uses `universe_feasibility.md` to build the instrument tables. Any instrument marked `INFEASIBLE` goes into the instrument table with `include = false` and its reason.

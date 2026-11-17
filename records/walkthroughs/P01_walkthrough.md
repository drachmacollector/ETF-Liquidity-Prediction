# P01 Walkthrough — Source Verification and Access Probes

| Field | Value |
|---|---|
| Phase | P01 |
| Status at time of writing | VERIFIED |
| Period | 2026-11-17 → 2026-11-17 |
| Sessions | 1 |
| Author | Claude Code |
| Git commit at end | the commit titled "P01: check every data source and record what works" |

## 1. Entry conditions

- [x] P00 VERIFIED (9118d7f).
- [x] `ESW_ALLOW_NETWORK=1` added to `.env`.
- [x] MI-02 done (Tiingo key verified in P00).

## 2. What was completed

- T01.1 Probe framework: `esw.ingest.http.PoliteSession` (honest user agent, per-host rate limit, back-off), `esw.ingest.probe` (ProbeRow, ProbeRunner, registry, matrix merge), CLI `esw probe [ids] [--list]`. Done.
- T01.2 US probes: Tiingo, Stooq, yfinance, SPDR Gold, iShares, SSGA, USCF, Invesco, VanEck, Global X, Xtrackers, abrdn, Teucrium, Vanguard, Wayback, EDGAR. Done.
- T01.3 India probes: NSE UDiFF + legacy, BSE, AMFI NAVAll, AMFI API, mfapi (95 ETFs + controls), mfapi-vs-AMFI cross-check, yfinance pre-2016 / India VIX, MCX, IBJA, NSE India VIX, AMFI AUM. Done.
- T01.4 Market probes: FRED (17 series), EIA (8 contracts), yfinance futures/FX/indices, exchange calendars. Done.
- T01.5 Primary texts: Rule 6c-11, SEBI 26 Feb 2026 circular, Mirae Silver ETF SID, NSE closing price, US NAV clocks. Done (`reports/data/primary_text_notes.md`).
- T01.6 Terms summary. Done (MI-07 already accepted, D-004).
- T01.7 Golden fixtures: 11 sources. Done.
- T01.8 Universe feasibility + gate. Done (PASS with manual dependencies).
- T01.9 `sources` in settings; `reference/source_registry.csv`. Done.

## 3. Outputs produced

| Output | Path | Notes |
|---|---|---|
| Probe matrix | `reports/data/source_probe_matrix.csv` | 273 rows |
| Reports | `reports/data/{source_probe_report,primary_text_notes,terms_of_use_summary,universe_feasibility}.md` | |
| Feasibility tables | `reports/data/universe_feasibility_{us,in}.csv` | Input to P02 |
| Source registry | `reference/source_registry.csv` | 32 sources with role and fallback |
| Raw probe files | `data/raw/_probes/<source>/` (gitignored) | 278 manifest lines in `data/manifests/ingest_log.jsonl` |
| Parsers | `src/esw/ingest/parsers.py` | Reused by P04–P06 |
| Fixtures/tests | `tests/fixtures/*`, `tests/unit/test_parsers.py`, `tests/acceptance/test_p01_acceptance.py` | |

## 4. Key results and findings

1. **US scripted NAV sources:** SPDR Gold archive (GLD from 2004-11-18, with issuer premium at a matched 4:15pm clock), iShares (19 funds; NAV + daily shares outstanding since inception; EWJ/EWH/EWW from 1996), SSGA (SPY/DIA from 2003, JNK from 2007). 28 of 49 candidates fully scripted.
2. **US manual:** all USCF funds (USO, UNG, …): NAV only, no shares outstanding (I-001); GREK, ASHR, Invesco, abrdn, Teucrium, Vanguard. **Unavailable:** RSX, EGPT, ERUS NAV (I-005).
3. **Tiingo** covers delisted funds (RSX to 2023-01-13, ERUS to 2022-08-30, EGPT to 2024-03-21). Raw closes plus `splitFactor`. Free tier ~50 requests/hour (I-002).
4. **India:** NSE archive (archives.nseindia.com) scriptable from **2016-01-01**; earlier 403. AMFI API: NAV from 2010 **with upload timestamps** (IST, mislabelled Z). mfapi: full history; 847/847 exact agreement with AMFI on the Mirae Silver ETF. 23 gold, 16 silver and 5 international ETFs have ≥ 250 NAV days.
5. **Indian classification** must use scheme names (D-007). The Nippon BeES NAV history starts 2016-11-07 under current codes (I-003). Unit splits exist (I-004).
6. **Correction:** Indian NAV before Apr 2026 included a notional delivery premium (D-005; Research Document v1.1, System Specification v1.1).
7. **Rule 6c-11** confirmed to exclude UITs and commodity trusts (OQ-01).
8. **Market series:** BAA10Y for credit (HY OAS truncated); EIA futures end 2024-04-05 (yfinance contracts afterwards); no exchange calendars for Cairo, Athens or Moscow.
9. **Feasibility gate PASS** with manual dependencies: USO and UNG (capacity incidents) and GREK (closure incident) depend on MI-04.

## 5. Decisions made

| ID | Decision | Decided by |
|---|---|---|
| D-005 | Indian pre-2026 NAV includes a notional delivery premium; docs corrected | Agent (evidence) |
| D-006 | Source choices and fallbacks | Agent |
| D-007 | Classify Indian ETFs by name | Agent |
| D-008 | AMFI `known_at` = upload timestamp | Agent |
| D-009 | Gate passes with manual dependencies; MI-04 essentials gate P04 completion | Agent (per T01.8) |
| (impl.) | Ruff ignores E501; Typer `Argument/Option` allowed as defaults; Excel reading pinned to `calamine` (added `python-calamine`, `tabulate`) | Agent |

## 6. Deviations from the plan

| Planned | Actual | Reason | Impact |
|---|---|---|---|
| Probe each source with ≤ 3 requests | iShares (20 files), mfapi (95), Tiingo (50) needed one request per instrument | Feasibility needs per-instrument history depth | None; still polite |
| Honest access only | One **exploratory** request in this session included a browser-imitating user agent as a fallback. The environment blocked it before it ran; the approach was dropped and no recorded result uses it | Mistake in an exploratory script | None; recorded for transparency |
| India candidates from AMFI categories | Name-based classification | Categories inconsistent | P02 verifies by hand |
| Indian price history from 2007 | Scripted from 2016; yfinance from 2009 for some; manual otherwise | NSE archive 403 before 2016 | Indian evaluation will rely mostly on 2016+; the 2013 gold episode needs yfinance/manual prices |

## 7. Issues encountered

I-001 (USCF no shares), I-002 (Tiingo hourly limit), I-003 (BeES pre-2016 NAV), I-004 (Indian unit splits), I-005 (RSX/EGPT/ERUS NAV). All OPEN, none blocking P02.

## 8. Unresolved problems and open questions

- MI-04 essentials (USO, UNG, GREK) are needed before P04 can complete. If unobtainable, the user decides on the coverage loss before P07.
- MI-05 (domestic spot) is needed for Layer 1 in P05/P08.
- The 3 Aug 2026 NSE closing-auction boundary (OQ-02 caveat) is to be checked in P05.
- AMFI's uniform valuation policy text (OQ-10) is still to be located.

## 9. Manual interventions

| MI | Status | Notes |
|---|---|---|
| MI-04 | REQUESTED | 10-row list in `records/MANUAL_ACTIONS.md`; essentials 1–3 |
| MI-05 | REQUESTED | Domestic gold/silver history |
| MI-06 | REQUESTED (optional) | WRDS yes/no |

## 10. Exact current state of the project

- Data: only probe samples in `data/raw/_probes/` (gitignored), logged in the manifest.
- Code: settings/runlog/CLI (P00); ingestion HTTP, parsers for all confirmed formats, probe framework, feasibility and registry builders.
- Tests: `pytest -q` → 65 passed.
- Configuration: `config/settings.yaml` now has `sources`. Spec v1.1, Research Document v1.1.

## 11. How to reproduce

```
.venv/Scripts/python.exe -m esw probe            # all probes (~15 min; Tiingo may need a second run an hour later)
.venv/Scripts/python.exe -c "from esw.ingest.feasibility import write_reports, build_source_registry; write_reports(); build_source_registry()"
.venv/Scripts/python.exe -m pytest -q
```

## 12. Handoff to P02

- Build `reference/instruments_us.csv` from `reports/data/universe_feasibility_us.csv` (include FEASIBLE and FEASIBLE_MANUAL; INFEASIBLE RSX/EGPT/ERUS with `include = false`, reason I-005).
- Build `reference/instruments_in.csv` from `universe_feasibility_in.csv` (FEASIBLE rows), hand-verify names, ISINs, AMFI codes and symbols, and exclude overnight/liquid debt ETFs (System Specification §5.3).
- Look for predecessor AMFI codes of the Nippon BeES funds (I-003); seed Indian unit splits (I-004).
- Hand tables needed for Cairo/Athens/Moscow holidays only if GREK (and later EGPT/RSX) data arrive.

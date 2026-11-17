# P01 — Source probe report

**Date:** 2026-11-17 · **Runs:** `runs/20261117-155940_probe/` (all 32 probes) and a second run (Tiingo resume, AMFI/mfapi re-probe after fixing ETF classification) · **Machine-readable results:** `reports/data/source_probe_matrix.csv` (one row per source × instrument), `reference/source_registry.csv` (one row per source, with role and fallback order), `reports/data/universe_feasibility.md`.

**Access rule applied throughout:** every request identified itself honestly (`esw-research-bot/0.1`), at most one request per second per host (two seconds for NSE), with retries only on 429/5xx. Where a site served a browser check, stalled non-browser clients, or required a page-issued token, the source was recorded as BLOCKED or MANUAL_ONLY and **not** worked around. (One exploratory request in this phase tried a browser-like user agent as a fallback. The environment correctly refused it, and the approach was removed. All recorded results use the honest user agent.)

## 1. Headline

| Area | Verdict |
|---|---|
| US prices | **Solved.** Tiingo gives raw (unadjusted) OHLCV plus a split factor from listing, including **delisted** funds (RSX to 2023-01-13, ERUS to 2022-08-30, EGPT to 2024-03-21). Free tier ≈ 50 requests/hour, so backfills must be paced (P04). yfinance is the fallback (its `Close` is split-adjusted). Stooq is dropped (browser check). |
| US NAV + shares (scripted) | **Good for 28 of 49 candidates.** SPDR Gold archive (GLD from 2004-11-18, GLDM), iShares (19 funds, NAV + daily shares outstanding since inception, e.g., EWJ/EWH/EWW from 1996, LQD from 2002), SSGA (SPY, DIA from 2003; JNK from 2007). |
| US NAV (manual) | **USCF (USO, UNG, BNO, UGA, USL, UNL, CPER, USCI), Invesco, Global X (GREK), Xtrackers (ASHR), abrdn, Teucrium, Vanguard** need manual downloads (MI-04). USCF's file has NAV only (no shares outstanding). |
| US NAV (unavailable) | **RSX, EGPT, ERUS**: fund pages removed; no archived NAV files in the Wayback Machine. Only CRSP (MI-06, optional) could recover them; otherwise they stay catalogue-only incidents. |
| India prices | **NSE archive works from 2016-01-01** (both bhavcopy formats, including the Sunday 2026-02-01 special session) on `archives.nseindia.com`. Before 2016 the archive returns 403 to scripts; yfinance has some ETFs from 2009 (e.g., GOLDBEES.NS). BSE is blocked. |
| India NAV | **Excellent.** AMFI's API gives NAV history from 2010 **with an upload timestamp for each NAV** (exact `known_at`). mfapi.in mirrors full history (including pre-2010) and matched AMFI exactly on 847/847 overlapping dates for the Mirae Silver ETF. |
| India domestic spot (Layer 1) | **Manual only** (MCX 403; IBJA offers 30-day PDFs; MI-05). |
| India VIX | nseindia.com API does not answer scripts; yfinance `^INDIAVIX` works. |
| Market-wide | FRED works for VIX, OVX, GVZ, BAA10Y, AAA10Y, rates, broad dollar, most FX. **ICE BofA HY OAS is truncated to 2023 on FRED** → use BAA10Y. EIA futures curve **ends 2024-04-05**; yfinance single-contract series (e.g., CLZ26.NYM) cover later dates. |
| Calendars | `exchange_calendars` has NYSE, BSE (`XBOM`; no NSE), London, HK, Tokyo, Shanghai, Istanbul, São Paulo, Mexico, Korea, ASX, Xetra, Paris. **No Cairo, Athens or Moscow** → small hand tables in P02 for the international funds kept. |
| SEC EDGAR | Works with the generic project user agent (no personal email), giving filing acceptance times for `known_at`. |

## 2. Universe feasibility (detail in `universe_feasibility.md`)

**Gate: PASS**, but with manual dependencies:

| Group | Feasible (scripted + manual) | Note |
|---|---|---|
| US_COMM_PHYS | 7 (4 scripted: GLD, GLDM, IAU, SLV) | |
| US_COMM_FUT | 15 (**1 scripted: GSG**) | **USO and UNG (anchor incidents) depend on MI-04 (USCF)** |
| US_BOND | 9 (7 scripted) | LQD, HYG, MUB, EMB, AGG, TLT, JNK scripted |
| US_INTL | 10 (8 scripted) | **The only closure-type stress fund obtainable is GREK (manual)**; EGPT/RSX/ERUS unavailable without CRSP |
| US_CTRL | 6 (4 scripted) | |
| India gold + silver | 39 with ≥ 250 NAV days | 23 gold (9 with history from 2007–2011), 16 silver (from Jan 2022) |
| India international | 5 | MON100 (2011), MAFANG, MASPTOP50, MAHKTECH, MONQ50 |

## 3. Findings that change or refine the plan

1. **Indian NAV basis before April 2026 included a "notional premium"** (SEBI circular para 1; Mirae SID: a delivery premium). Research Document §4.1/§4.3 and System Specification §4.4 are corrected (D-005): `LP_NAV` before 2026-04-01 is a small, slow-moving delivery premium, not zero. P08 estimates it.
2. **AMFI categories are inconsistent** (e.g., GOLDBEES under "Other Scheme – Gold ETF", ICICI Silver ETF under "Other ETFs"). Classification uses scheme names within ETF categories (`esw.ingest.candidates.classify_india`, D-007).
3. **Nippon "BeES" funds (GOLDBEES, NIFTYBEES, BANKBEES, JUNIORBEES) have NAV history only from 2016-11-07** under their current AMFI codes, and are absent from AMFI's 2010 snapshot (predecessor AMCs: Benchmark → Goldman Sachs → Reliance → Nippon). Earlier NAVs, if needed, must be found under predecessor codes in P02/P05. Not blocking: nine other gold ETFs have history from 2007–2011.
4. **Unit splits exist in Indian gold ETFs** (e.g., Kotak Gold ETF NAV ≈ ₹1,657 in Jan 2010 vs ≈ ₹100s now). OQ-19 confirmed as a real issue for P07.
5. **AMFI upload times** cluster around 22:00–23:00 IST, but some are after midnight (minimum hour observed: 02:00 IST). The `known_at` rule must use the actual upload timestamp, never assume "same evening" (System Specification §7 refined in P07).
6. **GLD's archive carries the issuer's own premium at a matched clock** (4:15pm indicative value vs 4:15pm mid), a timing-robust cross-check for the gold measurement problem (Research Document §2.3).
7. **USCF NAV history is restated for the April 2020 1-for-8 reverse split**; Tiingo raw closes are not, but carry `splitFactor` = 0.125 on 2020-04-29. P07 must put both on the same basis (OQ-04 partly resolved).
8. **Tiingo free-tier rate limit** (~50 requests/hour) hit during probing; 5 control tickers (DIA, IVV, IWM, QQQ, VOO) still to be confirmed. They exist on yfinance, so this is not blocking (I-002).

## 4. Manual interventions requested

| MI | What | Priority |
|---|---|---|
| MI-04 | USCF NAV CSVs for USO, UNG (essential), BNO, UGA, USL, UNL, CPER, USCI; Global X GREK (essential for closure-type coverage); Invesco DBC, DBA, DBO, BKLN; Xtrackers ASHR; abrdn SIVR, PPLT, PALL; Teucrium CORN, WEAT, SOYB; Vanguard BND, VOO (lowest) | Essential items before P04 completes |
| MI-05 | MCX or IBJA domestic gold and silver price history (Layer 1); optional: NSE bhavcopy before 2016 | Before P05 completes |
| MI-06 | Optional: check WRDS/CRSP access (would recover RSX, ERUS, EGPT and add daily bid/ask) | Optional |

## 5. Open questions closed or narrowed

OQ-01 resolved (Rule 6c-11 scope); OQ-02 resolved with caveat (ETFs keep 30-minute VWAP; 3 Aug 2026 closing auction applies to F&O stocks); OQ-03 resolved (per-issuer availability above); OQ-04 partly resolved (USCF and iShares restate NAV for splits; Tiingo raw + split factor); OQ-06 partly resolved (GLD 10:30am NY NAV; SLV London silver price); OQ-07 resolved (RSX/EGPT/ERUS NAV unavailable without CRSP); OQ-08 resolved (EIA ends 2024-04-05; yfinance contracts after); OQ-09 resolved (BAA10Y); OQ-13 resolved (MCX/IBJA manual only); OQ-14 resolved (circular text read; AMFI policy text still to locate); OQ-16 resolved (verbatim triggers); OQ-23 resolved (Tiingo works; ~50 requests/hour free tier). Details: `primary_text_notes.md`, `records/OPEN_QUESTIONS.md`.

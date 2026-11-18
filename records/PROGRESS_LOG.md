# Progress Log (append-only)

Format and rules: [`docs/process/Documentation_Logging_and_Phase_Gates.md`](../docs/process/Documentation_Logging_and_Phase_Gates.md) §4. Newest entries at the bottom. Never edit earlier entries; add corrections as new entries.

---

## 2026-11-17 — Documentation — session 1 (planning, not build)
- Done: Archived superseded v0/v1 documents to `archive/` (with `archive/README.md`). Moved the two source proposals to `docs/source/`.
- Done: Wrote the Research Document (`docs/research/ETF_Stress_Research_Document.md`), the System Specification (`docs/technical/00_System_Specification.md`), 18 phase documents (`docs/technical/phases/P00`–`P17`), the documentation/logging/phase-gate protocol and templates (`docs/process/`), 12 manual-intervention guides (`docs/manual/`), and initialised `records/`.
- Research checks performed in this session: SEBI 26 Feb 2026 gold/silver valuation circular (exchange-polled spot from 1 Apr 2026); USO April 2020 premium figures from SEC filings (36% on 21 Apr 2020; 8.66% on 22 Apr; 1.45% on 1 May); UNG July 2009 suspension from 8-K filings; RSX creation suspension (3 Mar 2022) and halt (4 Mar 2022); LQD March 2020 discount (~5%) and BIS Bulletin No. 6; Rule 6c-11 2%/7-day text; SEBI direct-redemption triggers; overseas-ETF limit stops (Feb 2022, Apr 2024); Oct 2025 Indian silver episode details; EIA futures discontinuation (crude after Apr 2024); `bidask` EDGE package; GLD historical archive availability; conflicting reports on Feb 2026 import duty.
- Not done: no code, no data download (build starts at P00).
- Decisions: D-000, D-002 recorded.
- Next step: start P00 in a Claude Code session; request MI-01.

## 2026-11-17 — Documentation — session 2
- Done: Recorded the user's commit policy (D-003: commit and push after every verified phase, simple messages) and terms-of-use acceptance (D-004). MI-01 and MI-07 marked VERIFIED. Confirmed `origin` points to github.com/drachmacollector/ETF-Liquidity-Prediction and `main` is in sync.
- Updated: CLAUDE.md, P00 T00.9 and the phase-gate protocol to state the commit rule.
- Next step: start P00. First user step after that: MI-02 (Tiingo API key) in P01.

## 2026-11-17 — P00 — session 1
- Done: Python project set up with uv (`uv.lock`, `.venv`), package `esw` with settings (all System Spec §4.13 parameters), run tracking, ingest manifest, CLI (`version`, `doctor`, `paths`), `.gitignore`, `.env.example`, 47 tests.
- Evidence: `records/acceptance/P00_acceptance.md`; smoke run `runs/20261117-152551_smoke/`.
- MI-02: user added the Tiingo key; verified with two API calls (200). Tiingo needs `Content-Type: application/json`.
- Decisions: D-001 (uv). Ruff now excludes docs/archive/records/reports.
- Status: P00 VERIFIED. Next step: P01 source probes.

## 2026-11-17 — P01 — session 1
- Done: Probe framework and `esw probe` CLI; 32 probes across US prices/NAV, India prices/NAV/spot, market series and calendars (runs `20261117-155940_probe`, `20261117-161616_probe`; 273 matrix rows; 278 manifest lines). Parsers for every confirmed format with golden fixtures; feasibility report and source registry; `sources` block in settings.
- Primary texts read: Rule 6c-11 (excludes UITs and commodity trusts), SEBI 26 Feb 2026 circular (old NAV included a notional premium → D-005, docs v1.1), Mirae Silver ETF SID (direct-redemption triggers verbatim; inception 9 Jun 2023), NSE closing auction (F&O only from 3 Aug 2026).
- Key results: US scripted NAV for 28/49 candidates (SPDR Gold, iShares, SSGA); USCF/Global X and others manual; RSX/EGPT/ERUS NAV unavailable. NSE archive scriptable from 2016. AMFI API gives NAV upload timestamps. Feasibility gate PASS with manual dependencies.
- Issues: I-001 to I-005 opened. Decisions: D-005 to D-009.
- Note: one exploratory request tried a browser-like user agent; the environment blocked it; approach dropped; no results use it.
- Requested from user: MI-04 (essentials USO, UNG, GREK), MI-05 (domestic spot), MI-06 (optional).
- Status: P01 VERIFIED. Next: P02 (reference data), which does not wait on the manual items.

## 2026-11-17/18 — P02 — session 1
- User input: MI-04 (USO, UNG, BNO, CPER, GREK) and MI-05 (MCX gold/silver spot 2005–2026, IBJA 30 days) done; MI-06 not possible (no WRDS). User allowed browser-like automated access (D-010): CLAUDE.md, System Specification v1.2 §11, `PoliteSession(browser=True)` and the MI-04 guide updated.
- Checked the manual files: GREK file is correct (premium/discount; covers the 2015 Athens closure); USCF NAVs are **not** split-adjusted (D-014, corrects P01/OQ-04); MCX spot covers 2005-2026. New parsers + fixtures; `esw manual-register` logged 9 files.
- Built reference tables: instruments_us (50; 47 included), instruments_in (100; 68 included), symbol_history (293, dated from NSE bhavcopies), nav_clock (158), corporate_actions_manual (45), duty_india (19; 8 verified), band_regimes_india (14; 4 verified), series_catalogue (22), calendar overrides and Athens sessions. Loaders, pandera schemas, `esw reference validate` (0 errors), `esw reference build-calendars`.
- Found: NSE archive scriptable from 2007 on nsearchives host; BSE bhavcopy downloadable; 33 Indian funds changed symbol and 21 changed ISIN (lineages recorded); SETFNIF50 → SBINIFTY50 (2026-10-30); SILVRETF → SILVERAG on 2025-09-15; May 2026 duty rise to 15% reported.
- Decisions D-010–D-014. Issues: I-001/I-003/I-005 updated, I-006 opened. OQ-04, 06, 11, 13, 15, 18, 19 updated; OQ-24, OQ-25 added. MI-09 REQUESTED (11 items).
- Status: P02 VERIFIED. Next: P03 (incident catalogue); P04–P06 may run in parallel.

## 2026-11-18 — P03-P06 — session 1
- User: continue through as many phases as possible; batch manual tasks at the end.
- P03: catalogue built from EDGAR (acceptance times; found EDGAR's "Z" is real UTC) and press sources: 24 incidents, 48 operational events, 596 capacity rows; second pass 22/24 agreement. VERIFIED_WITH_PENDING; MI-08 requested and made an entry condition of P12 (D-016).
- P04: Tiingo for all 50 US candidates; issuer NAV via SPDR, iShares, SSGA, USCF page API (D-010), Invesco API (curl), Global X manual. 9 funds excluded (D-015). VERIFIED.
- P05: 4,918 NSE bhavcopies 2007-2026; AMFI NAV with upload times (100% agreement with mfapi); MCX spot; India VIX. VERIFIED.
- P06: 49 market/FX/futures/index series; curve ends 2024-04-05 (D-017). VERIFIED.
- Decisions D-015 to D-018. MI-08 REQUESTED. Next: P07 curation.

## 2026-11-18 — P07 — session 1
- Curated PIT store built and validated; 24 Indian split candidates resolved (37 verified rows); NAV-spike rule tightened; DATA_CUTOFF 2026-11-16; rebuild deterministic. VERIFIED. Next: P08.

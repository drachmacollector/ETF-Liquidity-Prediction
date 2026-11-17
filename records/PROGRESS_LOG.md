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

# Open Questions Tracker

Seeded from Research Document §13 (which holds the full "why it matters / how to resolve / default" text). Update this table when a question is resolved or a default is adopted; put the evidence path in **Resolution**.

Status: `OPEN` · `RESOLVED` (answered with evidence) · `DEFAULTED` (default adopted, with decision ID) · `CARRIED` (moved to limitations/future work in P17)

| ID | Short question | Blocks | Status | Resolution / evidence | Date |
|---|---|---|---|---|---|
| OQ-01 | Exact scope of Rule 6c-11 (UITs, commodity trusts) | P17 | RESOLVED | Rule defines ETF as a registered open-end management company: excludes UITs and commodity trusts/pools. `reports/data/primary_text_notes.md` §1 | 2026-11-17 |
| OQ-02 | NSE/BSE closing-price methodology for ETFs | P05 | RESOLVED | Close = 15:00–15:30 VWAP; closing auction from 2026-08-03 applies to F&O stocks only; ETFs expected unchanged [R]; P05 checks the 3 Aug 2026 boundary. primary_text_notes §4 | 2026-11-17 |
| OQ-03 | Per-issuer NAV and shares-outstanding history availability | P04 | RESOLVED | Per-issuer availability in `reports/data/universe_feasibility.md` and `source_probe_report.md` §1 | 2026-11-17 |
| OQ-04 | Are issuer NAV histories split-adjusted? | P07 | RESOLVED (amended P02) | iShares: adjusted (no NAV jumps). **USCF CSV, SPDR Gold (GLDM), SSGA (JNK): raw** (D-014; USO ×8.44 on 2020-04-29). Tiingo: raw close + splitFactor. Seeded in `reference/corporate_actions_manual.csv` with `applies_to` | 2026-11-17 |
| OQ-05 | Shares-outstanding timing convention per issuer | P10 | OPEN | | |
| OQ-06 | NAV valuation time per US ETF | P08 | RESOLVED | GLD NAV at 10:30am NY (LBMA PM basis); SLV on London silver price; bond/equity 16:00 ET. P02: per-instrument rows in `reference/nav_clock.csv`; rows marked [K] (futures settlement times, foreign closes, PGM) not yet checked against prospectuses — P08 checks empirically | 2026-11-17 |
| OQ-07 | RSX/ERUS/EGPT/GREK NAV history obtainable? | P04 | RESOLVED | RSX/EGPT/ERUS NAV unavailable (pages removed; no Wayback NAV files). CRSP only (MI-06). Issue I-005 | 2026-11-17 |
| OQ-08 | WTI/Henry Hub futures curve after April 2024 | P06 | RESOLVED | EIA crude and gas futures end 2024-04-05; yfinance single contracts (e.g., CLZ26.NYM) afterwards | 2026-11-17 |
| OQ-09 | Long-history credit-spread series | P06 | RESOLVED | Use FRED BAA10Y (from 1986); ICE BofA OAS truncated to 2023 on FRED | 2026-11-17 |
| OQ-10 | Indian gold/silver NAV method before/after 1 Apr 2026, per scheme | P08 | OPEN | | |
| OQ-11 | Does the Sep 2026 band framework apply to international ETFs? | P16 | OPEN (narrowed) | NSE circular 122/2026 splits only commodity vs other ETFs, so overseas equity ETFs read as ±10% / 5% flex to ±20%. Row kept `verified = n`; MI-09 B2 | 2026-11-17 |
| OQ-12 | Overseas-cap utilisation published anywhere? | P10 | OPEN | | |
| OQ-13 | MCX/IBJA domestic spot history downloadable? | P05 | RESOLVED | MCX polled spot (Ahmedabad) received by hand: gold 2005-06-06 → 2026-11-17, silver 2005-05-14 → 2026-11-17 (MI-05 VERIFIED). P05 tries automated refresh (D-010) | 2026-11-17 |
| OQ-14 | Text of SEBI 26 Feb 2026 circular and AMFI implementation policy | P08 | RESOLVED | Circular read: polled spot of exchanges settling physical derivatives, from 2026-04-01; AMFI uniform-policy text not yet located (kept under OQ-10). primary_text_notes §2 | 2026-11-17 |
| OQ-15 | India gold/silver import-duty history 2007–2026 | P05 | DEFAULTED (D-013) | `reference/duty_india.csv`: 8 of 19 rows verified from Budget speeches/annexes (2012, 2019, 2021, 2023, 2024); Budget 2026-27 made no change; a May 2026 rise to 15% is reported (unverified). Layer 1 only for verified periods; MI-09 D1–D7 | 2026-11-17 |
| OQ-16 | Current wording of SEBI direct-redemption triggers | P09 | RESOLVED | Verbatim in Mirae Silver ETF SID: discount >1% for 7 continuous days; no quotes 3 days; bid size < half creation unit averaged over 7 days. primary_text_notes §3 | 2026-11-17 |
| OQ-17 | Clause mapping 2024 → 2026 MF master circular | P17 | OPEN | | |
| OQ-18 | Historical band rules per exchange/date (incl. Feb 2026 interim) | P07 | OPEN (narrowed) | From 2026-09-07 verified (NSE circular 122/2026). Feb 2026: BSE used T-1 NAV on 1 Feb 2026 only (reports). Pre-2026 ±20% on T-2 NAV start date unknown. MI-09 B1–B4 | 2026-11-17 |
| OQ-19 | Corporate actions in Indian ETFs | P07 | OPEN (seeded) | 22 NAV unit-split candidates (×10/×50/×100, 2015–2026) seeded `verified = n`: NSE close does not jump on the same days, so price and NAV change basis on different dates (often with an ISIN change). P07 dates both | 2026-11-17 |
| OQ-20 | Did US silver ETFs dislocate in Oct 2025 / Jan–Feb 2026? | P14 | OPEN | | |
| OQ-21 | Date and wording of Mirae's overseas-ETF investor caution | P17 | OPEN | | |
| OQ-22 | Useful lead time and alert budget for Mirae's teams | P11 | OPEN | | |
| OQ-23 | Tiingo terms and rate limits for this use | P04 | RESOLVED | Tiingo works with the key; free tier ~50 requests/hour (I-002) | 2026-11-17 |
| OQ-24 | Exact purity and polling convention of the MCX spot file (995 vs 999 gold; which poll is "the" daily price) | P05/P08 | OPEN | File gives commodity, unit, location (Ahmedabad) and 2–5 polls a day, no purity | |
| OQ-25 | Was Invesco QQQ converted from a UIT to an open-end fund, and when? | P17 (Rule 6c-11 coverage claim) | OPEN | SEC ticker file lists QQQ as a fund series (S000101292); `legal_form` kept `uit`, `rule_6c11 = unknown` | |

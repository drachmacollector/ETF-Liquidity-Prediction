# Open Questions Tracker

Seeded from Research Document §13 (which holds the full "why it matters / how to resolve / default" text). Update this table when a question is resolved or a default is adopted; put the evidence path in **Resolution**.

Status: `OPEN` · `RESOLVED` (answered with evidence) · `DEFAULTED` (default adopted, with decision ID) · `CARRIED` (moved to limitations/future work in P17)

| ID | Short question | Blocks | Status | Resolution / evidence | Date |
|---|---|---|---|---|---|
| OQ-01 | Exact scope of Rule 6c-11 (UITs, commodity trusts) | P17 | RESOLVED | Rule defines ETF as a registered open-end management company: excludes UITs and commodity trusts/pools. `reports/data/primary_text_notes.md` §1 | 2026-11-17 |
| OQ-02 | NSE/BSE closing-price methodology for ETFs | P05 | RESOLVED | Close = 15:00–15:30 VWAP; closing auction from 2026-08-03 applies to F&O stocks only; ETFs expected unchanged [R]; P05 checks the 3 Aug 2026 boundary. primary_text_notes §4 | 2026-11-17 |
| OQ-03 | Per-issuer NAV and shares-outstanding history availability | P04 | RESOLVED | Per-issuer availability in `reports/data/universe_feasibility.md` and `source_probe_report.md` §1 | 2026-11-17 |
| OQ-04 | Are issuer NAV histories split-adjusted? | P07 | RESOLVED | iShares and USCF restate NAV history for splits; Tiingo gives raw close + splitFactor. P07 reconciles. source_probe_report §3 item 7 | 2026-11-17 |
| OQ-05 | Shares-outstanding timing convention per issuer | P10 | OPEN | | |
| OQ-06 | NAV valuation time per US ETF | P08 | RESOLVED | GLD NAV at 10:30am NY (LBMA PM basis); SLV on London silver price; bond/equity 16:00 ET (P02 confirms from prospectuses). primary_text_notes §5 | 2026-11-17 |
| OQ-07 | RSX/ERUS/EGPT/GREK NAV history obtainable? | P04 | RESOLVED | RSX/EGPT/ERUS NAV unavailable (pages removed; no Wayback NAV files). CRSP only (MI-06). Issue I-005 | 2026-11-17 |
| OQ-08 | WTI/Henry Hub futures curve after April 2024 | P06 | RESOLVED | EIA crude and gas futures end 2024-04-05; yfinance single contracts (e.g., CLZ26.NYM) afterwards | 2026-11-17 |
| OQ-09 | Long-history credit-spread series | P06 | RESOLVED | Use FRED BAA10Y (from 1986); ICE BofA OAS truncated to 2023 on FRED | 2026-11-17 |
| OQ-10 | Indian gold/silver NAV method before/after 1 Apr 2026, per scheme | P08 | OPEN | | |
| OQ-11 | Does the Sep 2026 band framework apply to international ETFs? | P16 | OPEN | | |
| OQ-12 | Overseas-cap utilisation published anywhere? | P10 | OPEN | | |
| OQ-13 | MCX/IBJA domestic spot history downloadable? | P05 | RESOLVED | MCX returns 403 to scripts; IBJA offers only 30-day PDFs → manual (MI-05) | 2026-11-17 |
| OQ-14 | Text of SEBI 26 Feb 2026 circular and AMFI implementation policy | P08 | RESOLVED | Circular read: polled spot of exchanges settling physical derivatives, from 2026-04-01; AMFI uniform-policy text not yet located (kept under OQ-10). primary_text_notes §2 | 2026-11-17 |
| OQ-15 | India gold/silver import-duty history 2007–2026 | P05 | OPEN | | |
| OQ-16 | Current wording of SEBI direct-redemption triggers | P09 | RESOLVED | Verbatim in Mirae Silver ETF SID: discount >1% for 7 continuous days; no quotes 3 days; bid size < half creation unit averaged over 7 days. primary_text_notes §3 | 2026-11-17 |
| OQ-17 | Clause mapping 2024 → 2026 MF master circular | P17 | OPEN | | |
| OQ-18 | Historical band rules per exchange/date (incl. Feb 2026 interim) | P07 | OPEN | | |
| OQ-19 | Corporate actions in Indian ETFs | P07 | OPEN | | |
| OQ-20 | Did US silver ETFs dislocate in Oct 2025 / Jan–Feb 2026? | P14 | OPEN | | |
| OQ-21 | Date and wording of Mirae's overseas-ETF investor caution | P17 | OPEN | | |
| OQ-22 | Useful lead time and alert budget for Mirae's teams | P11 | OPEN | | |
| OQ-23 | Tiingo terms and rate limits for this use | P04 | RESOLVED | Tiingo works with the key; free tier ~50 requests/hour (I-002) | 2026-11-17 |

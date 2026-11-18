# P05 Walkthrough — India ETF Data Acquisition

| Field | Value |
|---|---|
| Phase | P05 · Status VERIFIED · 2026-11-18 · Claude Code |

## Downloads

| Source | Range | Notes |
|---|---|---|
| NSE CM bhavcopy (nsearchives, browser client, 2 s pacing) | 2007-01-01 → 2026-11-17: 4,918 files, 283 weekday 404s (holidays) | ISIN column from 2011-07; earlier rows mapped by symbol via `symbol_history` (10,925 rows). Some legacy files use 2-digit years (parser fixed) |
| AMFI nav-history API (≤ 4-year windows) | 2010 → 2026, 99 schemes, 134,291 rows | upload timestamps kept for `known_at` (D-008) |
| mfapi.in | full history, 99 schemes | fallback for pre-2010 and gaps; 100% exact agreement with AMFI on sampled dates |
| MCX polled spot (MI-05 manual) | gold 2005-06-06+, silver 2005-05-14+ | duplicates in export de-duplicated (9 conflicting timestamps → median) |
| India VIX (yfinance ^INDIAVIX) | 2008-03-03+ | |
| AMFI monthly AUM | not acquired | D-018 |

## Spot series by period

MCX polled spot, Ahmedabad, the whole span 2005-2026; P08 picks the last poll at or before 15:30 IST. Purity unstated (OQ-24).

## Calendar disagreements

2013-11-14 / 2013-11-15 (library error, Muharram moved). Special sessions all confirmed.

## Schema surprises

UDiFF from 2024-07-08; legacy before. Pre-2011 legacy files lack ISIN and TOTALTRADES. A few legacy files carry `13-Jul-20` style dates.

## Coverage

`reports/data/coverage_in.md`. Shortfalls are genuine no-trade days (thin debt ETFs) and overseas-holiday NAV gaps (international ETFs).

## Blocked periods

None — the browser-like client unblocked the pre-2016 archive (P01 had 403s).

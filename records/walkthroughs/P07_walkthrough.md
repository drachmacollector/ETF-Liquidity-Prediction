# P07 Walkthrough — Curation, Alignment, PIT Store and Data Quality

| Field | Value |
|---|---|
| Phase | P07 · Status VERIFIED · 2026-11-18 · Claude Code |

## Built

`src/esw/curate/{build,pit,splits,schemas,report}.py`; `esw curate`, `esw rebuild --curated`. Curated tables: instrument, calendar (India reconciled to bhavcopy presence for past dates), px_daily (398k rows), nav_daily (329k), issuer_premium, series_daily, in_spot_polls, symbol_history, corporate_action, operational_event, incident, capacity, duty, band_regime, nav_clock, quality_flag. `ingested_at` comes from the manifest, so rebuilds are byte-stable.

## Precedence used

US prices Tiingo (yfinance only for cross-check); US NAV the issuer source per instrument; India prices NSE; India NAV AMFI then mfapi (3,278 rows).

## Resolved splits

All 23 US events (P02) applied with `applies_to` per raw series. India: 24 detected candidates → 37 verified `unit_split` rows: NIFTYBEES, BANKBEES, GOLDBEES, HNGSNGBEES (price 19 Dec 2019, NAV 23 Dec 2019 — the Nippon ISIN change), Kotak Gold (2015, 2021), ICICI gold (2016, 2018, with ISIN changes), HDFC, SBI, ABSL, UTI, Axis, Quantum (1:50), Motilal N100/MON100 (2021), and same-day splits in 2026 (Kotak Silver, Groww gold/silver, DSP gold/silver, LIC gold, Invesco gold). ICICI's 2018-07-03 seed row dropped (gap artefact).

## NAV anomalies

The first spike rule flagged genuine crash days (2008, 2020, 2026) because it did not check the price. Tightened to the spec's intent: NAV jumps and reverses back near its previous level **and the price makes neither move** → 14 flags (SLV London-clock days, Asian/Indian March 2020 NAVs); USO 21 Apr 2020 correctly not flagged. 372 stale-NAV runs kept as information.

## DATA_CUTOFF

2026-11-16.

## Rules that proved impractical

None. FRED lags are business days; the AMFI fallback 23:59 IST is used only for mfapi rows.

# P06 Acceptance Report — Underlying, Market-wide and FX Data

| Field | Value |
|---|---|
| Phase | P06 |
| Prepared / verified | Claude Code, 2026-11-18 (same session) |
| Overall result | **PASS** |

## Tests

`pytest -q` 154 passed; `tests/unit/test_market_parsers.py` + `tests/acceptance/test_p06_acceptance.py` 9 passed.

## Criteria

| ID | Criterion | Result | Evidence |
|---|---|---|---|
| AC-06.1 | Every catalogue series staged or marked unavailable with dependent features | PASS | 49 series staged; unavailable: silver_usd_navimpl, usdinr_rbi, post-2024 curve, CSI300/HSTECH/EGX30/MOEX indices (`coverage_series.md`) |
| AC-06.2 | Lag and time zone for every series | PASS | `reference/series_catalogue.csv` (54 rows) |
| AC-06.3 | 2004 → latest (US), 2007 → latest (India) or gaps documented | PASS | US series from ≤ 2004 except vol indices (OVX 2007, GVZ 2008), dollar index 2006 (DTWEXM before), curve to 2024-04-05 (D-017) |
| AC-06.4 | Roll handling implemented and tested | PASS | `flag_rolls` (6 robust SD, trailing window known at t−1); synthetic roll test |
| AC-06.5 | FX for every included international ETF's home market | PASS | JPY, HKD, CNY, BRL, MXN, INR, TRY, EUR, broad USD |
| AC-06.6 | Tests and manifest | PASS | all raw files logged |

## Checklist

- VIX March 2020 peak 82.69 (16 Mar 2020); USD/RUB peaked at 139 in March 2022 — the expected series.
- Curve gap after 2024-04-05 documented, decision D-017.
- NAV-implied gold vs COMEX front month: median absolute difference 0.31%, 88% of days within 1% (timing and contango).

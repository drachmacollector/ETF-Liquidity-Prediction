# P07 Acceptance Report — Curation, Alignment, PIT Store and Data Quality

| Field | Value |
|---|---|
| Phase | P07 |
| Prepared / verified | Claude Code, 2026-11-18 (same session) |
| Overall result | **PASS** |
| Note | Started with P03 VERIFIED_WITH_PENDING (D-016); P07 uses incident dates/events only, not mechanism labels |

## Tests

`pytest -q` all pass; `tests/unit/test_pit_rules.py` (8), `test_split_detection.py` (1), `tests/integration/test_rebuild_determinism.py` (1), `tests/acceptance/test_p07_acceptance.py` (6).

## Criteria

| ID | Criterion | Result | Evidence |
|---|---|---|---|
| AC-07.1 | Curated tables exist and validate | PASS | 18 tables in `data/curated/`; pandera schemas `esw.curate.schemas` (keys unique, known_at UTC, positive prices/NAV) |
| AC-07.2 | Zero unresolved errors for included instruments | PASS | 24 split candidates (Indian unit splits with price and NAV legs on different days) resolved by 37 verified rows; 0 errors left; 212 gap > 25% warnings all annotated |
| AC-07.3 | USO continuous across April 2020; other splits pass | PASS | +838 / +3,641 / +866 / +145 bps on 20/21/22 Apr and 1 May 2020; no ×8 jump; no split candidates remain anywhere |
| AC-07.4 | known_at on every time-stamped row; PIT tests | PASS | px, nav, series, capacity, events; one test per §7 rule |
| AC-07.5 | DATA_CUTOFF set and recorded | PASS | 2026-11-16 (`config/settings.yaml`, `data/curated/DATA_CUTOFF.txt`) |
| AC-07.6 | Rebuild determinism | PASS | two rebuilds, identical content hashes for all tables |
| AC-07.7 | Quality report and data dictionary | PASS | `reports/data/quality_report.md`, `quality_flags.csv`, `data_dictionary.md` |

## Checklist

- Every `|close/NAV−1| > 25%` flag is annotated (Indian international ETFs under the overseas cap, USO 21 Apr 2020, EWH Oct 1997, Hang Seng BeES Mar 2020, N100 2018, Axis gold split day).
- Reconciled India calendar contains 2026-02-01 (`special`).
- DATA_CUTOFF 2026-11-16 is the latest US/India trading day with ≥ 90% coverage in both markets.
- US cross-source close check: Tiingo vs yfinance, 200 random instrument-dates, 99.5% within 0.5% (`reports/data/px_crosscheck_us.csv`).

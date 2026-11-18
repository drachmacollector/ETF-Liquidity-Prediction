# P05 Acceptance Report — India ETF Data Acquisition

| Field | Value |
|---|---|
| Phase | P05 |
| Prepared / verified | Claude Code, 2026-11-18 (same session) |
| Overall result | **PASS** (coverage shortfalls explained per instrument) |

## Tests

`pytest -q` 154 passed; `tests/unit/test_bhav_parsers.py` + `tests/acceptance/test_p05_acceptance.py` 8 passed.

## Criteria

| ID | Criterion | Result | Evidence |
|---|---|---|---|
| AC-05.1 | Prices and NAV from listing for every included instrument | PASS | 68/68 included have both; bhavcopies from 2007 (D-010), NAV AMFI from 2010 + mfapi earlier |
| AC-05.2 | Price coverage ≥ 97% or explained | PASS (explained) | 59/68 ≥ 97%; 9 thin debt/control ETFs below because bhavcopies omit untraded securities (listed in `coverage_in.md`) |
| AC-05.3 | NAV coverage ≥ 97%; AMFI vs mfapi agreement ≥ 99% | PASS (explained) | 64/68 ≥ 97%; 4 below because NAV is not struck on overseas-market holidays (MAHKTECH, HNGSNGBEES…); AMFI vs mfapi exact agreement 100% on 99 schemes × 50 dates |
| AC-05.4 | Calendar reconciliation report, disagreements classified | PASS | `india_calendar_reconciliation.md`: 2 library errors (Muharram 2013 moved); 29 special sessions agree |
| AC-05.5 | Domestic spot coverage documented | PASS | MCX polled spot gold 2005-06-06 → 2026-11-17, silver 2005-05-14 → 2026-11-17; no gap period |
| AC-05.6 | Mirae GOLDETF, SILVERAG complete across Oct 2025 and Feb 2026 | PASS | test; only 2025-10-21 (Muhurat session) has no NAV |
| AC-05.7 | Manifests; idempotency and parser tests | PASS | BhavStore caches files and remembers 404 days; parser tests for both schemas and 2-digit years |

## Checklist

- SILVERAG 1–20 Oct 2025, close vs NAV: +1.4% (8 Oct), +1.5% (9 Oct), −1.8% (10 Oct), +2.0% (14 Oct), −3.5% (16 Oct). The reported 5–10% premiums were vs **iNAV**; against the official NAV (then import parity + notional premium, which itself rose with the domestic market) the gap is small. P08 tests the known fact and records this.
- 2026-02-01 SILVERAG: open 297.00, high 297.00, low = close = 256.65 (closing at the lower band, consistent with a lock); 2026-02-02 close 220.35 vs NAV 241.86 (−8.9%).
- Reconciled calendar lists 2026-02-01 as a special session.

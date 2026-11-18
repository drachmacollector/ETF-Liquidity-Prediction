# P04 Acceptance Report — US ETF Data Acquisition

| Field | Value |
|---|---|
| Phase | P04 |
| Prepared / verified | Claude Code, 2026-11-18 (same session) |
| Overall result | **PASS** (accepted gaps logged in D-015) |

## Tests

| Command | Result |
|---|---|
| `pytest -q` | 154 passed |
| `pytest tests/unit/test_us_parsers.py tests/acceptance/test_p04_acceptance.py -q` | 8 passed |

## Criteria

| ID | Criterion | Result | Evidence |
|---|---|---|---|
| AC-04.1 | Staged price and NAV for every included instrument; others excluded with a reason; gate passes | PASS | 38 included, all with Tiingo prices and issuer NAV; 9 excluded in P04 (D-015) + 3 earlier (I-005); gate 4/12/8/9/5 |
| AC-04.2 | Price ≥ 98%, NAV ≥ 95% of expected days | PASS | min price 99.81%, min NAV 99.28% (`reports/data/coverage_us.md`); longest gaps 2 days (GREK 14: issuer file placeholders, Mar-Apr 2022) |
| AC-04.3 | GLD, SLV, USO, UNG, LQD NAV within 30 days of listing or explained | PASS | GLD 0, SLV −7, LQD −4 days; USO/UNG from 2009-01-02, accepted in D-015 (covers UNG 2009 and USO 2020) |
| AC-04.4 | Every raw file logged with checksum; checksums re-verified | PASS | `test_ac_04_4_raw_checksums_unchanged` (all US raw files) |
| AC-04.5 | Idempotency and parser tests | PASS | `test_fetcher_idempotent_and_isolated` (skipped_cached, failure isolation), USCF/Invesco golden files |
| AC-04.6 | Manual drops logged `status = manual`; MI-04 checklist done | PASS | 9 files logged by `esw manual-register`; MI-04 essentials VERIFIED |

## Checklist

- USO across April 2020: Tiingo `splitFactor` 0.125 on 2020-04-29; USCF NAV jumps ×8.44 the same day (both raw) — reconciled in P07.
- UNG NAV includes July–September 2009 (from 2009-01-02).
- Re-running a fetch logs `skipped_cached` (test).

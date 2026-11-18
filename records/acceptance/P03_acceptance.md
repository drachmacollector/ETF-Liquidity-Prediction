# P03 Acceptance Report — Incident and Operational-Event Catalogue

| Field | Value |
|---|---|
| Phase | P03 |
| Prepared by / date | Claude Code, 2026-11-18 |
| Verified by / date | Claude Code, same session (no fresh-session verification) |
| Git commit evaluated | working tree, committed as the P03 commit |
| Overall result | **VERIFIED_WITH_PENDING** — all criteria met except AC-03.5 (MI-08 user review), which is an entry condition of P12 (D-016) |

## 1. Tests

| Command | Result |
|---|---|
| `pytest -q` (full) | 154 passed |
| `pytest tests/unit/test_catalogue_schema.py tests/acceptance/test_p03_acceptance.py -q` | 11 passed |
| `python -m esw catalogue validate` | 0 errors |

## 2. Acceptance criteria

| ID | Criterion | Result | Evidence |
|---|---|---|---|
| AC-03.1 | ≥ 18 incidents (≥ 12 US, ≥ 6 India) incl. every T03.3 row | PASS | 24 incidents (17 US, 7 India); all 21 required IDs present; 3 added (INC-US-2022-WEAT, INC-US-2009-UNG-MAY, INC-US-2007-UNG-NOV), found by EDGAR full-text search |
| AC-03.2 | ≥ 30 operational events with effective_at, known_at (or month precision), source, grade | PASS | 48 events (2 with month precision); 22 dated by EDGAR acceptance timestamps |
| AC-03.3 | Capacity rows for USO and UNG covering 2009 and 2020 with EDGAR known_at | PASS | `reference/capacity_us.csv`: 596 rows (USCF LP funds from 10-Q/10-K "registered a total of" and balance-sheet units; 8-K remaining-share counts; WEAT; GLD/SLV registration type) |
| AC-03.4 | Mechanism codes and primary family; double-review agreement reported | PASS | Pass 1 vs pass 2: 22/24 agree on primary family (91.7%); disagreements INC-US-2022-RUSSIA, INC-IN-2020-COVID flagged (`reports/catalogue/second_pass.csv`) |
| AC-03.5 | MI-08 completed | **PENDING** | MI-08 REQUESTED 2026-11-18; entry condition of P12 (D-016) |
| AC-03.6 | `esw catalogue validate` zero errors | PASS | 0 errors |

## 3. Verification checklist

| Check | Result |
|---|---|
| Five `known_at` spot checks | UNG suspension 2009-07-07T17:52:02Z, USO suspension 2020-04-21T13:00:37Z, USO registration 2020-06-12T13:05:56Z, WEAT suspension 2022-03-07T15:11:21Z, SLV warning 2021-02-05T22:51:29Z — all match EDGAR acceptance times (UTC; checked that EDGAR's "Z" is real UTC: EFFECT notices land at 04:15Z in summer and 05:15Z in winter) |
| No row uses effective_at as known_at without justification | EDGAR rows use acceptance times; press rows use publication date 18:00 local (protocol); closures use first closed session 00:00 local |
| Near-misses present | 6 (SLV 2021, GOLD-EFP 2020, US silver Oct 2025, WEAT 2022, UNG May 2009, UNG Nov 2007) |

## 4. Notes

- 89 of 107 source pages saved under `data/raw/catalogue_sources/` (gitignored, logged); 16 failed (Business Wire, etf.com 403; MOEX unreachable; morningstar 202). URLs and grades stay in the tables.
- Pass 2 was a later re-read by the same agent, not blind to pass 1: the agreement statistic overstates independence (stated in the report).

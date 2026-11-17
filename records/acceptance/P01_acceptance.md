# P01 Acceptance Report — Source Verification and Access Probes

| Field | Value |
|---|---|
| Phase | P01 |
| Prepared by / date | Claude Code (executing agent), 2026-11-17 |
| Verified by / date | Claude Code, same session, by re-running the tests and the checklist below (no fresh-session verification) |
| Git commit evaluated | working tree on top of 9118d7f, committed as the P01 commit |
| Overall result | **PASS** (gate passes with manual dependencies, D-009) |

## 1. Test suite

| Command | Result |
|---|---|
| `pytest -q` | 65 passed |
| `pytest tests/acceptance/test_p01_acceptance.py -q` | 6 passed |
| `ruff check .` | All checks passed |

## 2. Acceptance criteria

| ID | Criterion | Result | Evidence |
|---|---|---|---|
| AC-01.1 | Every source in T01.2–T01.4 probed or marked MANUAL_ONLY/BLOCKED with the error recorded | PASS | 32 probes, 273 matrix rows (`reports/data/source_probe_matrix.csv`); runs `20261117-155940_probe`, `20261117-161616_probe`; `test_every_required_source_probed` |
| AC-01.2 | NAV and price availability recorded for every US and Indian candidate | PASS | `reports/data/universe_feasibility.md` (49 US candidates; 95 Indian ETFs + controls) |
| AC-01.3 | Feasibility gate evaluated; user decision if failed | PASS | All 8 gate rows pass (FEASIBLE_MANUAL counted as T01.8 allows). Essential manual items become an entry condition for completing P04 (D-009) |
| AC-01.4 | OQ-01, 02, 03, 08, 13, 14, 16 resolved or defaulted | PASS | All seven RESOLVED in `records/OPEN_QUESTIONS.md` (plus OQ-04, 06, 07, 09, 23) |
| AC-01.5 | Golden fixtures for every OK/PARTIAL source; parser tests pass offline | PASS | 11 fixture folders under `tests/fixtures/`; `tests/unit/test_parsers.py` (13 tests) passes offline |
| AC-01.6 | Terms-of-use summary written; MI-07 DONE | PASS | `reports/data/terms_of_use_summary.md`; MI-07 VERIFIED (D-004) |
| AC-01.7 | No probe exceeded the settings rate limits | PASS with note | All requests went through `PoliteSession` (≥ 1 s between requests per host; 2 s for NSE). The *vendor's* Tiingo free-tier hourly limit (~50/hour) was hit, giving HTTP 429 for 5 tickers. The settings now include `tiingo_requests_per_hour: 45` (I-002) |

## 3. Deliverables present

| Deliverable | Path | Present |
|---|---|---|
| Probe framework + CLI | `src/esw/ingest/{probe,http,parsers,candidates,probes_us,probes_in,probes_mkt,feasibility}.py`; `esw probe` | Yes |
| Probe matrix | `reports/data/source_probe_matrix.csv` | Yes |
| Probe report | `reports/data/source_probe_report.md` | Yes |
| Primary-text notes | `reports/data/primary_text_notes.md` | Yes |
| Terms summary | `reports/data/terms_of_use_summary.md` | Yes |
| Universe feasibility | `reports/data/universe_feasibility.md` (+ `_us.csv`, `_in.csv`) | Yes |
| Source registry | `reference/source_registry.csv`; `config/settings.yaml: sources` | Yes |
| Fixtures + parser tests | `tests/fixtures/*`, `tests/unit/test_parsers.py` | Yes |
| Updated open questions | `records/OPEN_QUESTIONS.md` | Yes |

## 4. Global Definition of Done

- [x] 1 Deliverables exist
- [x] 2 Tests and lint pass
- [x] 3 All criteria evaluated
- [x] 4 Acceptance report and walkthrough written
- [x] 5 Records updated (STATUS, PROGRESS_LOG, DECISIONS D-005–D-009, ISSUES I-001–I-005, OPEN_QUESTIONS, MANUAL_ACTIONS)
- [x] 6 Required MIs for this phase done (MI-02, MI-07). MI-04/MI-05 requested for P04/P05
- [x] 7 Committed and pushed under D-003

## 5. Orchestrator verification checklist

| Check | Result |
|---|---|
| GLD, SLV, USO, UNG, LQD NAV start near inception, or explained | GLD 2004-11-18 ✓, SLV 2006-04-21 ✓, LQD 2002-07-22 ✓; USO/UNG MANUAL_ONLY (USCF), explained, MI-04 essential |
| USO April 2020 reverse split visible in both sources | Tiingo `splitFactor` 0.125 on one row in Mar–May 2020 (fixture test); USCF page states NAV is restated for the split |
| Legacy and UDiFF bhavcopy fixtures exist and parse | Yes (2020-03-19 legacy; 2025-10-09 UDiFF) |
| Blocked sources have MIs REQUESTED with item lists | MI-04 (10 rows), MI-05 (3 rows), MI-06 optional |

## 6. Defects found during verification

- OQ-18 had been wrongly marked resolved (an old v1 numbering mix-up). Reverted to OPEN; reports corrected.
- The NAVAll fixture originally omitted category headers. The fixture builder (`trim_navall`) was fixed and the test now passes.

## 7. Sign-off

- Executing agent: Claude Code, 2026-11-17
- Orchestrator: Claude Code (same session), 2026-11-17

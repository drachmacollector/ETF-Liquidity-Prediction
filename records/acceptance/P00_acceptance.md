# P00 Acceptance Report — Environment, Repository and Governance Setup

| Field | Value |
|---|---|
| Phase | P00 |
| Prepared by / date | Claude Code (executing agent), 2026-11-17 |
| Verified by / date | Claude Code, same session, by re-running every check from a clean command line (no fresh-session verification) |
| Git commit evaluated | working tree on top of 6e740ef, committed as the P00 commit |
| Overall result | **PASS** |

## 1. Test suite

| Command | Result |
|---|---|
| `.venv/Scripts/python.exe -m pytest -q` | 47 passed, 0 failed, 0 skipped |
| `.venv/Scripts/python.exe -m pytest tests/acceptance/test_p00_acceptance.py -q` | 5 passed |
| `ruff check .` / `ruff format --check .` | All checks passed / 24 files already formatted |

## 2. Acceptance criteria

| ID | Criterion | Result | Evidence |
|---|---|---|---|
| AC-00.1 | Environment created and pinned; `esw version` works | PASS | `uv.lock` (104 packages); `esw 0.1.0 (git 6e740ef…)` |
| AC-00.2 | `esw doctor` exits 0, all core deps importable | PASS | All 22 core packages "ok"; `test_doctor_passes` |
| AC-00.3 | settings.yaml has every §4.13 parameter at default | PASS | `tests/unit/test_config.py` (25 parametrised default checks + presence test + grid) |
| AC-00.4 | pytest passes; ruff clean | PASS | Section 1 |
| AC-00.5 | Smoke run folder + registry row | PASS | `runs/20261117-152551_smoke/` (config.yaml, git_commit.txt, README.md, metrics.json); row in `runs/registry.csv` |
| AC-00.6 | `.env` gitignored, untracked; no secrets in tracked files | PASS | `git check-ignore .env` ok; `git log -- .env` empty; `test_no_secret_values_in_tracked_files` |
| AC-00.7 | D-001, D-002, D-003 recorded | PASS | `records/DECISIONS.md` |
| AC-00.8 | STATUS, PROGRESS_LOG, acceptance report, walkthrough updated | PASS | This file; `records/walkthroughs/P00_walkthrough.md`; STATUS row P00 |

## 3. Deliverables present

All deliverables in P00 §5 present: `pyproject.toml`, `uv.lock`, `src/esw/**` (config, runlog, paths, cli + 11 stub subpackages), `config/settings.yaml`, `.env.example`, `.gitignore`, tests (unit ×2, acceptance ×1, conftest), `runs/registry.csv`, `data/manifests/ingest_log.jsonl`, `app/streamlit_app.py` placeholder.

## 4. Global Definition of Done

- [x] 1 Deliverables exist
- [x] 2 Tests and lint pass
- [x] 3 All criteria evaluated
- [x] 4 Acceptance report and walkthrough written
- [x] 5 Records updated
- [x] 6 Required MIs done (MI-01 VERIFIED; MI-02 VERIFIED early)
- [x] 7 Committed and pushed under D-003

## 5. Orchestrator verification checklist

| Check | Result |
|---|---|
| Re-run `esw doctor` and `pytest -q` | Pass (47 passed) |
| Spot-check 3 parameters vs System Spec §4.13 | `ABS_FLOOR_BPS: 200`, `EMBARGO: 10`, `DEV_END: 2019-12-31` match |
| No `data/raw`, `.env`, `.venv` staged | `git add -A --dry-run` lists none |
| MI-01 status | VERIFIED (D-003) |

## 6. Defects found during verification

None.

## 7. Sign-off

- Executing agent: Claude Code, 2026-11-17
- Orchestrator: Claude Code (same session), 2026-11-17

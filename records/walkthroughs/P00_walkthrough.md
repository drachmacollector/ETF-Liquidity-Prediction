# P00 Walkthrough — Environment, Repository and Governance Setup

| Field | Value |
|---|---|
| Phase | P00 |
| Status at time of writing | VERIFIED |
| Period | 2026-11-17 → 2026-11-17 |
| Sessions | 1 |
| Author | Claude Code |
| Git commit at end | the commit titled "P00: set up Python project, settings, logging and tests" |

## 1. Entry conditions (checked at start)

- [x] Documentation set exists (`docs/`, `records/`, `CLAUDE.md`) — commit 39ecf27 and 6e740ef.
- [x] Git available; branch `main`, in sync with `origin`.
- [x] Python 3.11.9 available.

## 2. What was completed

- T00.1 Environment: `uv` 0.13.9 installed with pip; `.venv/` via `uv sync --all-extras --python 3.11` (D-001). Done.
- T00.2 `pyproject.toml`: package `esw`, hatchling build, `src/` layout, extras `fallback` (yfinance) and `dev` (pytest, pytest-cov, ruff), ruff and pytest config. Done.
- T00.3 Package skeleton: `config`, `paths`, `runlog`, `cli` implemented; 11 subpackages as documented stubs; Streamlit placeholder. Done.
- T00.4 Configuration: `config/settings.yaml` with every System Spec §4.13 parameter, the sensitivity grid, http and runtime settings; strict Pydantic model (unknown keys rejected; cross-field checks: embargo ≥ label lookahead, lockbox after dev end, threshold ordering). `.env.example`. Done.
- T00.5 Run tracking: `RunContext` (run folder, config snapshot, git commit, README, metrics, registry row, failure capture), `append_ingest_log` (schema-checked JSONL), `fingerprint` / `parquet_content_hash`, logging with run IDs. Done.
- T00.6 CLI: `esw version`, `esw doctor [--fix] [--smoke-run]`, `esw paths`. Done.
- T00.7 `.gitignore` as specified (plus `models/`, coverage files, OS files). Done.
- T00.8 Tests: 47 tests (config, runlog, acceptance). Done.
- T00.9 Records and commit policy: MI-01 was already done (D-003). Done.

## 3. Outputs produced

| Output | Path | Notes |
|---|---|---|
| Package | `src/esw/` | 4 working modules + 11 stubs |
| Settings | `config/settings.yaml` | Parameter names match the spec in UPPER_CASE |
| Lockfile | `uv.lock` | 104 packages |
| Tests | `tests/unit/test_config.py`, `tests/unit/test_runlog.py`, `tests/acceptance/test_p00_acceptance.py`, `tests/conftest.py` | `network` marker skipped unless `ESW_ALLOW_NETWORK=1` |
| Run registry | `runs/registry.csv` | 1 row (smoke run) |
| Smoke run | `runs/20261117-152551_smoke/` | Evidence for AC-00.5 |
| Ingest manifest | `data/manifests/ingest_log.jsonl` | Empty |

## 4. Key results and findings

- Installed versions of note: pandas, lightgbm 4.7.0, shap 0.51.0, scikit-learn 1.9.1, pandera 0.36.0, duckdb 2.0.0, exchange_calendars 4.13.3, bidask 2.1.0, streamlit 1.67.0, yfinance 1.8.0.
- **Tiingo key verified (MI-02):** `GET https://api.tiingo.com/api/test` → 200 "You successfully sent a request"; `GET /tiingo/daily/gld` → 200 with metadata. **Tiingo requires the header `Content-Type: application/json`**; without it the test endpoint returns a warning message. The P04 adapter must send it.
- Run IDs use UTC timestamps (`20261117-152551` = 20:55 IST); log lines use local time. Both are intended (System Spec §12 uses UTC for runs).

## 5. Decisions made

| ID | Decision | Why | Decided by |
|---|---|---|---|
| D-001 | Use uv + `uv.lock` | Installed cleanly; fast reproducible env | Agent |
| (implementation) | Ruff excludes `docs/`, `archive/`, `records/`, `reports/` | Ruff's formatter also reformats Python code blocks inside Markdown; documents should not be rewritten by tooling | Agent |

## 6. Deviations from the plan

| Planned | Actual | Reason | Impact |
|---|---|---|---|
| P00 T00.9: ask user for MI-01 | Already done before P00 (D-003) | User answered in advance | None |
| — | Ruff's first format run reflowed two Python snippets in `P04` and `P10` docs (whitespace/line-wrap only, no content change) | Ruff formats Markdown code blocks | Kept (cosmetic); docs now excluded |
| — | MI-02 verified during P00 instead of P01 | User added the key early | P01 can run the Tiingo probe immediately |

## 7. Issues encountered

None open.

## 8. Unresolved problems and open questions

None for P00. Open research questions are unchanged (`records/OPEN_QUESTIONS.md`).

## 9. Manual interventions

| MI | Status | Notes |
|---|---|---|
| MI-01 | VERIFIED | D-003 |
| MI-02 | VERIFIED | Key works (see §4) |
| MI-07 | VERIFIED | D-004 |

## 10. Exact current state of the project

- Data present: none (only an empty ingest manifest).
- Code complete: environment, settings, logging/run tracking, manifest writer, CLI basics. All other subpackages are stubs.
- Tests: `pytest -q` → 47 passed; P00 acceptance → 5 passed.
- Configuration: `config/settings.yaml` at spec defaults; `DATA_CUTOFF`, `THR_WATCH`, `THR_HIGH` null; `sources: {}` (filled in P01).

## 11. How to reproduce

```
python -m pip install uv
python -m uv sync --all-extras --python 3.11
.venv/Scripts/python.exe -m esw doctor --fix
.venv/Scripts/python.exe -m pytest -q
```

## 12. Handoff to P01

- Use `.venv/Scripts/python.exe -m esw …` (or `python -m uv run esw …`).
- Set `ESW_ALLOW_NETWORK=1` in `.env` for P01 probes.
- Tiingo adapter: send `Content-Type: application/json` and `Authorization: Token <key>`.
- First three things: (1) build `esw.ingest.probe` and the probe-matrix writer; (2) run the US price probes (Tiingo/Stooq/yfinance) and the issuer NAV probes (GLD archive first); (3) run the NSE/AMFI probes.

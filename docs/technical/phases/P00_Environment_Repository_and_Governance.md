# P00: Environment, Repository and Governance Setup

| Field | Value |
|---|---|
| Phase ID | P00 |
| Depends on | Nothing (first phase) |
| Unlocks | P01 |
| Estimated effort | 0.5–1 day |
| Manual interventions | **MI-01** (commit policy and optional GitHub remote): decision needed during this phase |
| Canonical references | System Specification §3 (layout), §4.13 (parameters), §11 (tooling), §12 (conventions); [process document](../../process/Documentation_Logging_and_Phase_Gates.md) |

## 1. Purpose

Create a working, reproducible Python project skeleton inside this repository, with configuration, logging, run tracking, the CLI entry point, the test harness and the records structure, so that every later phase writes code, data and evidence in the same places and the same way. Nothing project-specific is downloaded yet.

**Why first:** every acceptance check in later phases relies on the run registry, the ingestion manifest, the settings file and the test layout created here. Retrofitting them later causes untraceable numbers.

## 2. Scope

**In scope:** Python environment; `pyproject.toml` and lockfile; package skeleton `src/esw/`; CLI (`python -m esw`); `config/settings.yaml` with all parameters from the System Specification §4.13; `.env.example`; `.gitignore`; logging and run-tracking utilities; ingestion-manifest writer; test layout and first tests; records bootstrap; commit policy.

**Out of scope:** any data download (P01 onwards); any modelling code beyond empty module stubs.

## 3. Prerequisites (entry checklist)

- [ ] The documentation set exists (`docs/`, `records/`, `CLAUDE.md`).
- [ ] Git is available (`git --version`) and the repository is on branch `main` or a working branch.
- [ ] Python 3.11+ is available (`python --version`).

## 4. Implementation specification

### T00.1 Environment

1. Check `python --version` (expect 3.11.x on this machine). Record the exact version in the walkthrough.
2. Try `python -m pip install uv`. If it succeeds, use `uv` for environment and locking (`uv venv`, `uv pip install -e .[dev]`, `uv pip compile` or `uv lock`). If it fails, use `python -m venv .venv` and `pip`, and produce `requirements-lock.txt` with `pip freeze`.
3. Record the choice as decision **D-001** in `records/DECISIONS.md`. (D-002, "use Python 3.11", is pre-recorded by the documentation.)

### T00.2 `pyproject.toml`

- Project name `esw`, `src/` layout, `requires-python = ">=3.11"`.
- Dependencies as in System Specification §11 (core + optional extras `[fallback]` for `yfinance`, `[dev]` for pytest, pytest-cov, ruff).
- `[project.scripts] esw = "esw.cli:app"` (so both `esw …` and `python -m esw …` work).
- Ruff configuration: line length 110, target py311, rules `E,F,W,I,B,UP,SIM`.
- Pytest configuration: `testpaths = ["tests"]`, markers `slow`, `network`, `acceptance`. Tests marked `network` are skipped unless `ESW_ALLOW_NETWORK=1`.

### T00.3 Package skeleton

Create these modules with docstrings stating their responsibility (System Specification §2.2) and no logic yet unless listed:

```
src/esw/__init__.py            (__version__ = "0.1.0")
src/esw/__main__.py            (calls cli.app)
src/esw/cli.py                 (Typer app; commands: version, doctor, paths; later phases add commands)
src/esw/config.py              (Settings model; load_settings())
src/esw/runlog.py              (logging setup, RunContext, registry, manifest writer, fingerprint)
src/esw/paths.py               (all canonical paths derived from settings)
src/esw/reference/__init__.py
src/esw/ingest/__init__.py
src/esw/curate/__init__.py
src/esw/pricing/__init__.py
src/esw/labels/__init__.py
src/esw/features/__init__.py
src/esw/evaluation/__init__.py
src/esw/models/__init__.py
src/esw/explain/__init__.py
src/esw/reporting/__init__.py
src/esw/brief/__init__.py
app/streamlit_app.py           (placeholder page that says "Not built yet: see P16")
```

### T00.4 Configuration

- `config/settings.yaml` contains: `paths` (all directories in System Specification §3), `params` (every parameter in §4.13 with the default value and a comment naming the section), `sources` (placeholders filled in P01), `http` (user agent from env, rate limit 1 req/s/host, retries 5, back-off base 2 s), `seed`.
- `esw.config.Settings` is a Pydantic model; unknown keys are an error; values are validated (e.g., `ABS_FLOOR_BPS > 0`).
- `.env.example` lists `TIINGO_API_KEY=`, `FRED_API_KEY=`, `ESW_USER_AGENT=esw-research-bot/0.1`, `ESW_ALLOW_NETWORK=0`. `.env` is gitignored.

### T00.5 Run tracking and manifests (`esw.runlog`)

- `RunContext(phase, purpose, slug)`: context manager that creates `runs/<YYYYMMDD-HHMMSS>_<slug>/`, writes `config.yaml` (resolved settings), `git_commit.txt` (`git rev-parse HEAD` + dirty flag), sets up logging with `run_id`, and on exit appends a row to `runs/registry.csv` with status `ok` or `failed` and writes `README.md` with start/end time, purpose and metrics keys found.
- `append_ingest_log(record: dict)`: validates the record against the schema in System Specification §6.2 and appends a JSON line to `data/manifests/ingest_log.jsonl`.
- `fingerprint(paths) -> dict`: SHA-256 of each file (Parquet files hashed by content), used in `data_fingerprint.json`.
- Logging setup per System Specification §12.6.

### T00.6 CLI commands

- `esw version`: prints version and git commit.
- `esw doctor`: prints Python version, platform, package versions of every core dependency, whether `.env` exists, which secret names are set (never values), whether each canonical directory exists (creates missing ones with `--fix`), and exits non-zero on any failure.
- `esw paths`: prints the resolved canonical paths.

### T00.7 `.gitignore`

Ignore: `.venv/`, `.env`, `__pycache__/`, `*.pyc`, `.pytest_cache/`, `.ruff_cache/`, `data/raw/`, `data/manual_drop/`, `data/staged/`, `data/curated/`, `data/derived/`, `outputs/` (except `outputs/samples/`), `logs/`, `models/`, `runs/*/predictions.parquet`, `runs/*/*.pkl`, `runs/*/models/`, `desktop.ini`. Do **not** ignore `data/manifests/`, `runs/registry.csv`, `reference/`, `reports/`, `records/`.

### T00.8 Tests

- `tests/unit/test_config.py`: settings load; every parameter in System Specification §4.13 is present with its documented default (the test hard-codes the expected table); invalid values raise.
- `tests/unit/test_runlog.py`: `RunContext` creates the folder and registry row (use a temp directory); manifest writer rejects malformed records.
- `tests/acceptance/test_p00_acceptance.py`: runs `esw doctor` in a subprocess and asserts exit code 0; asserts `.env` is not tracked by git (`git ls-files .env` is empty).

### T00.9 Records and commit policy

1. Confirm `records/STATUS.md`, `PROGRESS_LOG.md`, `DECISIONS.md`, `ISSUES.md`, `OPEN_QUESTIONS.md`, `MANUAL_ACTIONS.md` exist (they are created with the documentation). Set P00 to `IN_PROGRESS` at the start.
2. **MI-01 is already done** (D-003, 17 Nov 2026): commit and push to `origin main` after every verified phase, with short plain messages (e.g., `P00: set up Python project and tools`). Confirm `git remote -v` shows the GitHub repository, then commit and push P00 when it is VERIFIED.

## 5. Deliverables

| Path | Description |
|---|---|
| `pyproject.toml`, `uv.lock` or `requirements-lock.txt` | Package definition and pinned environment |
| `src/esw/**` | Skeleton as in T00.3 with working `config`, `runlog`, `paths`, `cli` |
| `config/settings.yaml` | All parameters with defaults |
| `.env.example`, `.gitignore` | As specified |
| `tests/unit/test_config.py`, `tests/unit/test_runlog.py`, `tests/acceptance/test_p00_acceptance.py` | Passing tests |
| `runs/registry.csv` | Header row (and one row from a smoke run, see AC-00.5) |
| `data/manifests/ingest_log.jsonl` | Empty file created |
| `records/acceptance/P00_acceptance.md`, `records/walkthroughs/P00_walkthrough.md` | From templates |

## 6. Tests and validation

Run `pytest -q`, `ruff check .`, `ruff format --check .`, `python -m esw doctor`, and a smoke run: `python -m esw doctor --smoke-run` which creates a run folder through `RunContext` with purpose `smoke`.

## 7. Acceptance criteria

| ID | Criterion | How verified |
|---|---|---|
| AC-00.1 | Environment created and pinned; `python -m esw version` works | Command output in acceptance report |
| AC-00.2 | `python -m esw doctor` exits 0 with every core dependency importable | Acceptance test |
| AC-00.3 | `config/settings.yaml` contains every parameter of System Specification §4.13 at its default value | `test_config.py` |
| AC-00.4 | `pytest -q` passes; `ruff check` and `ruff format --check` clean | Command outputs |
| AC-00.5 | A smoke run created a run folder with `config.yaml`, `git_commit.txt`, `README.md` and a registry row | Inspect `runs/` |
| AC-00.6 | `.env` is gitignored and not tracked; no secret values in any tracked file | `git ls-files`, grep for key-like strings |
| AC-00.7 | D-001, D-002, D-003 recorded in `records/DECISIONS.md` | Inspect file |
| AC-00.8 | STATUS, PROGRESS_LOG, acceptance report and walkthrough updated | Inspect files |

## 8. Verification checklist (orchestrator)

- [ ] Re-run `python -m esw doctor` and `pytest -q` yourself; do not rely on the executing agent's report alone.
- [ ] Open `config/settings.yaml` and spot-check three parameters against System Specification §4.13.
- [ ] Confirm `git status` shows no `data/raw`, `.env` or `.venv` paths staged.
- [ ] Confirm MI-01 status in `records/MANUAL_ACTIONS.md`.

## 9. Risks and decision points

| Risk / decision | Handling |
|---|---|
| `uv` cannot be installed (corporate proxy, permissions) | Fall back to `venv` + `pip`; record D-001 |
| `lightgbm` wheel fails on Windows | Use the official wheel from PyPI (Windows wheels exist); if it still fails, record an issue and try `pip install lightgbm --prefer-binary`; escalate to the user only if both fail |
| `shap` build issues | Install a version with a prebuilt wheel for Python 3.11; pin it |
| User has not answered MI-01 | Proceed without committing; P00 can still be VERIFIED with "commit pending" noted, but D-003 must exist before P01 completes |

## 10. Walkthrough requirements (phase-specific)

Record: Python and key package versions; environment tool chosen; any installation workarounds; the exact commands to recreate the environment from scratch; the commit policy decided.

## 11. Handoff to P01

P01 can start when P00 is `VERIFIED`. P01 will add `esw probe` commands and fill `sources` in `config/settings.yaml`. If MI-02 (Tiingo key) is not yet done, P01 can start with the other probes and run the Tiingo probe when the key arrives.

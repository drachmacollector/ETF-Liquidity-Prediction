# CLAUDE.md — Operating instructions for Claude Code sessions

This repository builds the **ETF Arbitrage-Stress Early Warning System**: a research prototype that forecasts, 1–5 trading days ahead, the onset of persistent ETF price–NAV dislocations, explains them by mechanism, links them to past incidents, is validated on US ETFs, and is tested for transfer to Indian ETFs. It is not investment advice and not a trading system.

## Read first (every session)

1. `records/STATUS.md` — where the project is.
2. Last 3 entries of `records/PROGRESS_LOG.md`; open items in `records/ISSUES.md` and `records/MANUAL_ACTIONS.md`.
3. The latest file in `records/walkthroughs/`.
4. The current phase document in `docs/technical/phases/`.
5. `docs/technical/00_System_Specification.md` for any definition, parameter, schema or convention.

Document map: `docs/00_INDEX.md`. Rationale and facts: `docs/research/ETF_Stress_Research_Document.md`.

## Non-negotiable rules

- **Follow the phase order and gates** (System Specification §13). Do not start a phase until its prerequisites are `VERIFIED`. Never mark a phase `VERIFIED` because code exists: tests, acceptance report, walkthrough and record updates are required (System Specification §14).
- **Definitions live in the System Specification.** Do not invent or tweak parameters, label rules or metrics. Changes need a logged decision; parameters marked "frozen at P11" and anything touching the pre-registration or lockbox need **user approval**.
- **Point-in-time discipline.** Features use only data with `known_at ≤ decision time` through `esw.features.pit`. `esw.features` must never import `esw.labels`. Never use `effective_at` as `known_at`.
- **Lockbox.** No use of US data from 2020-01-01 or of any Indian data for modelling choices before MI-11 sign-off. P12 runs must end at `DEV_END`. The lockbox evaluation runs once with `--frozen`.
- **Report results whatever they are.** Negative results are valid outcomes.
- **Raw data are immutable**; every downloaded or manually dropped file is logged in `data/manifests/ingest_log.jsonl`. Be polite to servers (rate limits, user agent from settings).
- **Secrets** only in `.env` (gitignored). Never print, log or commit them. Never ask the user to paste keys into chat. Do not put the user's email or personal details in request headers unless the user explicitly chose that in MI-07.
- **Manual interventions:** when user action is needed, set the MI to `REQUESTED` in `records/MANUAL_ACTIONS.md`, point the user to the guide in `docs/manual/`, continue with independent work, and verify the result when the user reports it done.
- **Commits:** follow decision D-003 (MI-01). Until D-003 exists, do not commit.
- **Language in outputs:** descriptive only; no buy/sell/recommend wording; every brief and view carries "Model estimate. Not investment advice."

## Recording work

- End of every session: append to `records/PROGRESS_LOG.md`; update `records/STATUS.md`.
- Decisions → `records/DECISIONS.md`; problems → `records/ISSUES.md`; open questions → `records/OPEN_QUESTIONS.md`.
- Every model/evaluation command runs inside `RunContext` (creates `runs/<run_id>/` and a `runs/registry.csv` row).
- End of every phase: `records/acceptance/PXX_acceptance.md` and `records/walkthroughs/PXX_walkthrough.md` from the templates in `docs/process/templates/`.

## Environment

Windows 11, Python 3.11, package `esw` in `src/esw/`, CLI `python -m esw <command>`. No Makefile. Use `pathlib`; keep code OS-neutral. Tests: `pytest -q`; lint: `ruff check .` and `ruff format --check .`.

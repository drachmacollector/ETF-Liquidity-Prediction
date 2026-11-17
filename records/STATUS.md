# Project Status Board

Single source of truth for **actual** progress. Status vocabulary and update rules: [`docs/process/Documentation_Logging_and_Phase_Gates.md`](../docs/process/Documentation_Logging_and_Phase_Gates.md) §3.

**Last updated:** 2026-11-17 — P01 VERIFIED (all data sources probed; feasibility gate PASS with manual dependencies, D-009).
**Current phase:** P02 (NOT_STARTED)
**Waiting on user:** MI-04 (US fund NAV downloads; essentials USO, UNG, GREK, needed before P04 completes), MI-05 (Indian domestic gold/silver prices, needed before P05 completes), MI-06 (optional WRDS check). None blocks P02 or P03.
**Commit policy:** commit and push after every verified phase, simple messages (D-003).

## Phases

| Phase | Title | Status | Started | Implemented | Verified | Walkthrough | Acceptance | Blockers | Notes |
|---|---|---|---|---|---|---|---|---|---|
| P00 | Environment, repository and governance | VERIFIED | 2026-11-17 | 2026-11-17 | 2026-11-17 | [P00](walkthroughs/P00_walkthrough.md) | [P00](acceptance/P00_acceptance.md) | | 47 tests pass; uv env (D-001) |
| P01 | Source verification and access probes | VERIFIED | 2026-11-17 | 2026-11-17 | 2026-11-17 | [P01](walkthroughs/P01_walkthrough.md) | [P01](acceptance/P01_acceptance.md) | | 65 tests pass; D-005–D-009; I-001–I-005 |
| P02 | Reference data: universe, identifiers, calendars | NOT_STARTED | | | | | | | May need MI-09 |
| P03 | Incident and operational-event catalogue | NOT_STARTED | | | | | | | Needs MI-08 |
| P04 | US ETF data acquisition | NOT_STARTED | | | | | | MI-04 essentials (USO, UNG, GREK) before completion | MI-06 optional |
| P05 | India ETF data acquisition | NOT_STARTED | | | | | | MI-05 before completion | NSE scriptable from 2016 |
| P06 | Underlying, market-wide and FX data | NOT_STARTED | | | | | | | Optional MI-03 |
| P07 | Curation, alignment, PIT store, data quality | NOT_STARTED | | | | | | | |
| P08 | Pricing layer | NOT_STARTED | | | | | | | |
| P09 | Labels: episodes and targets | NOT_STARTED | | | | | | | Event-count gate |
| P10 | Feature engineering | NOT_STARTED | | | | | | | |
| P11 | Evaluation harness, baselines, pre-registration A | NOT_STARTED | | | | | | | Optional MI-10 |
| P12 | Model development, pre-registration B | NOT_STARTED | | | | | | | |
| P13 | Explainability: tags, reasons, analogues | NOT_STARTED | | | | | | | Requests MI-11 |
| P14 | US lockbox evaluation and replays | NOT_STARTED | | | | | | | Hard gate: MI-11 |
| P15 | India transfer test | NOT_STARTED | | | | | | | |
| P16 | Daily Stress Brief and dashboard | NOT_STARTED | | | | | | | MI-12 (wording) |
| P17 | Final validation and readiness | NOT_STARTED | | | | | | | MI-12 (sign-off) |

## Key frozen artefacts (filled as they are created)

| Artefact | Value | Recorded in |
|---|---|---|
| `DATA_CUTOFF` | — | P07 |
| Pre-registration Part A hash | — | D-P11-PREREG-A |
| Pre-registration Part B hash | — | D-P12-PREREG-B |
| Pre-registration final hash | — | D-P13-PREREG-EXPL |
| MI-11 sign-off date | — | MANUAL_ACTIONS |
| Lockbox run ID | — | P14 |
| India transfer run ID | — | P15 |
| Production model IDs | — | P16 |

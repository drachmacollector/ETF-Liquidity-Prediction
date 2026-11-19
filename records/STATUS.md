# Project Status Board

Single source of truth for **actual** progress. Status vocabulary and update rules: [`docs/process/Documentation_Logging_and_Phase_Gates.md`](../docs/process/Documentation_Logging_and_Phase_Gates.md) §3.

**Last updated:** 2026-11-19 — P08 VERIFIED (pricing panel; known facts reproduced, one explained).
**Current phase:** P09 (labels)
**Waiting on user:** MI-08 (incident label review; entry condition of P12, D-016) and MI-09 (11 India duty/band facts). Automation first (D-010).
**Commit policy:** commit and push after every verified phase, simple messages (D-003).

## Phases

| Phase | Title | Status | Started | Implemented | Verified | Walkthrough | Acceptance | Blockers | Notes |
|---|---|---|---|---|---|---|---|---|---|
| P00 | Environment, repository and governance | VERIFIED | 2026-11-17 | 2026-11-17 | 2026-11-17 | [P00](walkthroughs/P00_walkthrough.md) | [P00](acceptance/P00_acceptance.md) | | 47 tests pass; uv env (D-001) |
| P01 | Source verification and access probes | VERIFIED | 2026-11-17 | 2026-11-17 | 2026-11-17 | [P01](walkthroughs/P01_walkthrough.md) | [P01](acceptance/P01_acceptance.md) | | 65 tests pass; D-005–D-009; I-001–I-005 |
| P02 | Reference data: universe, identifiers, calendars | VERIFIED | 2026-11-17 | 2026-11-18 | 2026-11-18 | [P02](walkthroughs/P02_walkthrough.md) | [P02](acceptance/P02_acceptance.md) | | 100 tests pass; D-010–D-014; MI-09 requested |
| P03 | Incident and operational-event catalogue | VERIFIED_WITH_PENDING | 2026-11-18 | 2026-11-18 | 2026-11-18 | [P03](walkthroughs/P03_walkthrough.md) | [P03](acceptance/P03_acceptance.md) | MI-08 gates P12 (D-016) | 24 incidents, 48 events, 596 capacity rows |
| P04 | US ETF data acquisition | VERIFIED | 2026-11-18 | 2026-11-18 | 2026-11-18 | [P04](walkthroughs/P04_walkthrough.md) | [P04](acceptance/P04_acceptance.md) | | 38 US included; D-015 |
| P05 | India ETF data acquisition | VERIFIED | 2026-11-18 | 2026-11-18 | 2026-11-18 | [P05](walkthroughs/P05_walkthrough.md) | [P05](acceptance/P05_acceptance.md) | | 4,918 bhavcopies 2007-2026 |
| P06 | Underlying, market-wide and FX data | VERIFIED | 2026-11-18 | 2026-11-18 | 2026-11-18 | [P06](walkthroughs/P06_walkthrough.md) | [P06](acceptance/P06_acceptance.md) | | 49 series; D-017 |
| P07 | Curation, alignment, PIT store, data quality | VERIFIED | 2026-11-18 | 2026-11-18 | 2026-11-18 | [P07](walkthroughs/P07_walkthrough.md) | [P07](acceptance/P07_acceptance.md) | | DATA_CUTOFF 2026-11-16 |
| P08 | Pricing layer | VERIFIED | 2026-11-19 | 2026-11-19 | 2026-11-19 | [P08](walkthroughs/P08_walkthrough.md) | [P08](acceptance/P08_acceptance.md) |  | 315k rows; D-019, D-020 |
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
| `DATA_CUTOFF` | 2026-11-16 | P07 |
| Pre-registration Part A hash | — | D-P11-PREREG-A |
| Pre-registration Part B hash | — | D-P12-PREREG-B |
| Pre-registration final hash | — | D-P13-PREREG-EXPL |
| MI-11 sign-off date | — | MANUAL_ACTIONS |
| Lockbox run ID | — | P14 |
| India transfer run ID | — | P15 |
| Production model IDs | — | P16 |

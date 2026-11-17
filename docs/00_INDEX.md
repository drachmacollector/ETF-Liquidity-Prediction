# Documentation Index — ETF Arbitrage-Stress Early Warning System

**Documentation set version:** 1.0 · **As-of:** 17 November 2026 · **Status:** active, single source of truth

## 1. Reading order

| Order | Document | Role | Who needs it |
|---|---|---|---|
| 1 | [Research Document](research/ETF_Stress_Research_Document.md) (RD-01) | Why and what: ETF mechanics, the arbitrage pipe and how it breaks, NAV clocks and the two-layer gap, incident record, regulation (US/India), Mirae context and business value, literature, data landscape, feasibility, rationale, critical reassessment of the proposal, open questions | Everyone |
| 2 | [System Specification](technical/00_System_Specification.md) (TS-00) | Canonical definitions (premium, dislocation, episode, target), parameters, architecture, repository layout, data contracts, point-in-time rules, modelling and evaluation summary, outputs, tooling, Definition of Done, phase map | Builders, reviewers |
| 3 | Phase documents (below) | What to build, in order, with deliverables, tests, acceptance criteria and verification checklists | Builders, orchestrator |
| 4 | [Documentation, Logging and Phase-Gate Protocol](process/Documentation_Logging_and_Phase_Gates.md) (PR-01) | How progress, decisions, issues, runs and verification are recorded; walkthrough standard; session ritual | Builders, orchestrator |
| 5 | [Manual interventions](manual/MI-00_Index.md) | Step-by-step guides for everything the user must do | The user |
| — | [Source proposals](source/) | The two PDFs that define the revised direction | Context |

## 2. Phase documents

| Phase | Document | Depends on |
|---|---|---|
| P00 | [Environment, repository and governance](technical/phases/P00_Environment_Repository_and_Governance.md) | — |
| P01 | [Source verification and access probes](technical/phases/P01_Source_Verification_and_Access_Probes.md) | P00 |
| P02 | [Reference data: universe, identifiers, calendars, NAV clocks, regime tables](technical/phases/P02_Reference_Data_Universe_and_Calendars.md) | P01 |
| P03 | [Incident and operational-event catalogue](technical/phases/P03_Incident_and_Operational_Event_Catalogue.md) | P02 |
| P04 | [US ETF data acquisition](technical/phases/P04_US_ETF_Data_Acquisition.md) | P02 |
| P05 | [India ETF data acquisition](technical/phases/P05_India_ETF_Data_Acquisition.md) | P02 |
| P06 | [Underlying, market-wide and FX data](technical/phases/P06_Underlying_Market_and_FX_Data_Acquisition.md) | P02 |
| P07 | [Curation, alignment, point-in-time store, data quality](technical/phases/P07_Curation_Alignment_PIT_Store_and_Data_Quality.md) | P03–P06 |
| P08 | [Pricing layer](technical/phases/P08_Pricing_Layer.md) | P07 |
| P09 | [Labels: dislocation episodes and targets](technical/phases/P09_Labels_Dislocation_Episodes_and_Targets.md) | P08 |
| P10 | [Feature engineering: stress signals](technical/phases/P10_Feature_Engineering_Stress_Signals.md) | P08 |
| P11 | [Evaluation harness, baselines, pre-registration (A)](technical/phases/P11_Evaluation_Harness_Baselines_and_Preregistration.md) | P09, P10 |
| P12 | [Model development, pre-registration (B)](technical/phases/P12_Model_Development.md) | P11 |
| P13 | [Explainability: root-cause tags, reasons, analogue finder](technical/phases/P13_Explainability_Root_Cause_and_Analogue_Finder.md) | P12, P03 |
| P14 | [US lockbox evaluation and event replays](technical/phases/P14_US_Lockbox_Evaluation_and_Event_Replays.md) | P13 + MI-11 |
| P15 | [India transfer test](technical/phases/P15_India_Transfer_Test.md) | P14 |
| P16 | [Daily ETF Stress Brief and dashboard](technical/phases/P16_Daily_Stress_Brief_and_Dashboard.md) | P13 (P14/P15 for evidence) |
| P17 | [Final validation, verification and readiness](technical/phases/P17_Final_Validation_Verification_and_Readiness.md) | P14–P16 |

```
P00 → P01 → P02 ─┬→ P03 ─────────────┐
                 ├→ P04 ─┐            │
                 ├→ P05 ─┼→ P07 → P08 ┼→ P09 ─┐
                 └→ P06 ─┘            │       ├→ P11 → P12 → P13 ─[MI-11]→ P14 → P15 ─┐
                                      └→ P10 ─┘                  └──────→ P16 ─────────┴→ P17
```

## 3. Records (actual progress)

[`records/STATUS.md`](../records/STATUS.md) · [`PROGRESS_LOG.md`](../records/PROGRESS_LOG.md) · [`DECISIONS.md`](../records/DECISIONS.md) · [`ISSUES.md`](../records/ISSUES.md) · [`OPEN_QUESTIONS.md`](../records/OPEN_QUESTIONS.md) · [`MANUAL_ACTIONS.md`](../records/MANUAL_ACTIONS.md) · [`walkthroughs/`](../records/walkthroughs/) · [`acceptance/`](../records/acceptance/)

## 4. Precedence when documents disagree

Logged decision amending a section → frozen pre-registration → System Specification → phase documents → Research Document (facts and rationale only). Contradictions are logged as issues, never resolved silently.

## 5. Changelog

| Version | Date | Change |
|---|---|---|
| 1.0 | 2026-11-17 | First full documentation set for the revised direction; v0/v1 material archived |

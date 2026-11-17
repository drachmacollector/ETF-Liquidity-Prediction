# P16: Daily ETF Stress Brief, Operational Pipeline and Dashboard

| Field | Value |
|---|---|
| Phase ID | P16 |
| Depends on | P13 (can start building with development outputs); evidence views need P14 and P15 |
| Unlocks | P17 |
| Estimated effort | 3–5 days |
| Manual interventions | **MI-12** (optional: hosting the dashboard; reviewing the brief's wording) |
| Canonical references | System Specification §4.12 (risk levels), §10 (outputs); Research Document §6.4 (guardrails), §7.2 (who acts) |

## 1. Purpose

Deliver the system in the form its users would actually consume: a **daily pipeline** that refreshes recent data, scores every ETF, and writes predictions; a **Daily ETF Stress Brief** (HTML and Markdown) that a product, sales or compliance reader can understand in two minutes; and a **Streamlit dashboard** with a watchlist, ETF detail, incident replay and model-evidence views. This turns the research into a demonstrable prototype.

## 2. Scope

**In scope:** production models (retrained on all US data to `DATA_CUTOFF` with frozen settings); `esw daily` command; incremental refresh for recent dates; deterministic monitors; brief templates; routing table; dashboard; forward log (optional); tests; runbook.

**Out of scope:** real-time/intraday data; alerts by email/SMS; authentication; LLM-written text (parked); production deployment inside an AMC.

## 3. Prerequisites

- [ ] P13 `VERIFIED` (P14/P15 VERIFIED before the evidence views are finalised).

## 4. Implementation specification

### T16.1 Production models

`esw model train-production`: train `full_us` and `core_transfer` with the frozen configurations on all US rows up to `DATA_CUTOFF`, calibrate per the frozen method (calibration block = the last 20% of dates), assign model IDs `full_us@<cutoff>` and `core_transfer@<cutoff>`, save to `models/production/` (gitignored; the run folder records hashes). These are used only for dates after `DATA_CUTOFF` (the forward window) and for demonstration; all evaluation numbers come from P14/P15.

### T16.2 Daily pipeline

`esw daily --market US|IN|all --asof YYYY-MM-DD [--refresh-days 30]`:

1. Refresh raw data for the last `refresh-days` days for each source (adapters from P04–P06; idempotent).
2. Rebuild curated tables incrementally (or fully if fast enough; target < 10 minutes for both markets).
3. Pricing, features (as of `asof`), predictions with production models (US: `full_us`; India: `core_transfer` with India thresholds), SHAP/tags/reasons/analogues, deterministic monitors.
4. Write `outputs/predictions/predictions_<market>_<asof>.parquet`, append to `predictions_all.parquet`, render the brief, and (if enabled) append to `outputs/forward_log/forward_log.csv`.
5. Data-freshness check: if NAV for `asof` is missing for > 10% of instruments, the brief is still produced but carries a prominent "Data incomplete" banner and affected rows are `INSUFFICIENT_DATA`.

Historical mode: `esw daily --asof` for any past date within `[2010-01-01, DATA_CUTOFF]` renders the brief from the **stored point-in-time predictions** of P14/P15 (not from production models), so historical briefs show what the backtested system would have said that day.

### T16.3 Deterministic monitors

| Monitor | Definition | Shown |
|---|---|---|
| Absolute level | Descriptive band of `|prem|` (System Specification §4.12) | Always |
| SEC counter | Consecutive days with `|prem| > 200 bps` (shows "n of 8") | US; India as analogue |
| SEBI counter | Consecutive days with `prem < −100 bps` ("n of 7") | India |
| No-quote counter | Consecutive zero-volume days ("n of 3") | India |
| Band distance | Distance of close from the current band limit (India, regime-aware) | India |
| Layer 1 | `lp_bps_med5` for gold and silver with its own episode state | India |
| ACTIVE state | Real-time persistence rule (System Specification §4.12) | Always |

### T16.4 Routing table ("who acts")

`config/routing.yaml` maps tags and monitors to teams with neutral, descriptive guidance text:

| Trigger | Product & Ops | Sales & Distribution | Risk & Compliance |
|---|---|---|---|
| `CREATION_CONSTRAINT` HIGH | "Review creation capacity and FoF subscription settings" | "Expect client questions about premiums" | "Note potential disclosure needs" |
| `UNDERLYING_SQUEEZE` HIGH | "Check domestic vs global metal prices and market-maker inventory" | "Context: domestic metal premium" | — |
| `STALE_NAV` HIGH | "Check NAV valuation inputs" | "Context: NAV may lag market prices" | "Note valuation-timing caveat" |
| `LIQUIDITY_DRAIN` HIGH | "Contact market makers about quoting" | — | "Watch SEBI bid-size trigger" |
| SEBI counter ≥ 5 of 7 | — | — | "Direct-redemption trigger approaching" |

The wording is reviewed by the user (MI-12). The test in T16.7 enforces banned-word rules.

### T16.5 Brief content (`src/esw/brief/templates/brief.html.j2`, `brief.md.j2`)

1. Header: market, as-of date, decision time, data cutoff/freshness, model IDs, "Model estimate. Not investment advice. For internal discussion."
2. Summary strip: counts of HIGH, WATCH, ACTIVE; number of ETFs scored; changes since previous day.
3. **Mirae products** box (always shown): each Mirae ETF with level, premium, monitors.
4. Watchlist table sorted by `p`: ETF, issuer, premium (bps and descriptive level), `p`, level, tag, top reason, analogue.
5. ACTIVE episodes: ETF, days active, current and peak premium, tag at onset.
6. Alert cards for every HIGH (and WATCH for Mirae products): probability, tag and share, three reasons with values, closest past incident with one-line description, routing lines, monitors, a 60-day premium sparkline.
7. Regulatory monitors near triggers.
8. Layer-1 panel (India): domestic gold/silver vs import parity.
9. Data notes (missing data, locked days, regime notes, e.g., "commodity ETF bands: ±6% initial since 7 Sep 2026").
10. Footer: methodology link (report), glossary of terms (premium, NAV, iNAV, WATCH/HIGH meaning: "probability that a persistent dislocation starts within 5 trading days"), disclaimer.

Every number in the brief has an as-of date. Probabilities are shown as percentages with no decimals below 10% ("4%") and with the WATCH/HIGH thresholds stated.

### T16.6 Dashboard (`app/streamlit_app.py`)

| View | Content |
|---|---|
| **Watchlist** | Market and date selectors; table as in the brief (Mirae rows highlighted); filters by group/level/tag; download as CSV |
| **ETF detail** | Price vs NAV and premium chart with robust band; probability history with WATCH/HIGH lines; family-SHAP stacked bars over time; reasons; analogues (top 2) with links to replays; peers comparison; event markers (operational events by `known_at`) |
| **Incident replay** | Choose an incident; date slider; "what the system would have said that day" from stored point-in-time predictions |
| **Model evidence** | Headline verdict table (H1–H9), reliability diagrams, recall vs alert budget, lead-time histogram, value-of-creation-data comparison, limitations |

Design rules: readable on a projector; colour-blind-safe palette; tooltips define premium, NAV, probability, WATCH/HIGH; visible disclaimer; no auto-refresh. Use Plotly for charts.

### T16.7 Tests

- Snapshot test: rendering the brief for a fixed historical date (e.g., India 2025-10-08) from fixture predictions matches a stored snapshot (allowing for timestamps).
- Banned-word scan over rendered briefs and routing text.
- Streamlit smoke test with `streamlit.testing.v1.AppTest`: all four views load with sample data without exceptions.
- Daily pipeline integration test on a fixture date with network disabled (uses cached raw files).
- Timing: the daily pipeline for both markets completes in < 15 minutes on the user's laptop (measured and recorded).

### T16.8 Forward log (optional stretch)

If enabled in settings and D-003 allows commits: after each daily run, append the day's predictions (one row per ETF: `asof, instrument_id, p, level, tag`) to `outputs/forward_log/forward_log.csv` and commit with message `forward-log <market> <asof>`. Commit timestamps give independent evidence that predictions preceded outcomes. A small scorecard (`esw report forward`) compares forward predictions with realised outcomes once ≥ 20 trading days exist; no claims beyond the days available.

### T16.9 Runbook

`docs/operations/RUNBOOK.md` (created in this phase): how to run the daily pipeline, where outputs go, how to read the brief, what to do when a source fails, how to regenerate a historical brief, how to update production models after new data (retrain only with the frozen configuration; any change in configuration is a new research cycle).

## 5. Deliverables

| Path | Description |
|---|---|
| `src/esw/brief/{render,monitors,routing}.py`, templates; `config/routing.yaml` | Brief |
| `src/esw/cli.py` commands `daily`, `model train-production`, `report forward` | Pipeline |
| `app/streamlit_app.py` (+ `app/components/`) | Dashboard |
| `outputs/samples/` (tracked): brief for 3 historical dates (US 2020-04-20, India 2025-10-08, India 2026-01-30) and the latest date | Samples |
| `docs/operations/RUNBOOK.md` | Runbook |
| Tests (T16.7) | Passing |

## 6. Tests and validation

See T16.7. The acceptance test (`tests/acceptance/test_p16_acceptance.py`) runs the daily pipeline on a cached fixture date, renders the three historical sample briefs, runs the Streamlit smoke test and the banned-word scan.

## 7. Acceptance criteria

| ID | Criterion |
|---|---|
| AC-16.1 | `esw daily --market all --asof <latest>` runs end to end and writes predictions and briefs |
| AC-16.2 | Historical briefs for the three sample dates are produced from stored point-in-time predictions |
| AC-16.3 | Dashboard views load (smoke test) and show Mirae products highlighted |
| AC-16.4 | Banned-word scan passes; disclaimer present on every brief and view |
| AC-16.5 | Pipeline run time recorded (< 15 minutes target; if exceeded, documented with the bottleneck) |
| AC-16.6 | Runbook written; MI-12 completed or explicitly declined |

## 8. Verification checklist (orchestrator)

- [ ] Open the India 2025-10-08 brief; confirm it uses only information available that morning (compare with the replay).
- [ ] Open the dashboard locally (`streamlit run app/streamlit_app.py`) and click through all views.
- [ ] Read one alert card aloud: is it understandable to a non-technical reader?

## 9. Risks and decision points

| Item | Handling |
|---|---|
| Source refresh failures on the day | Brief still renders with banners; failures logged |
| Wording drifting toward advice | Banned-word test; MI-12 review |
| Mirae branding | Use plain text "Mirae Asset" in tables; do not embed logos unless the user decides to (MI-12) |

## 10. Walkthrough requirements

Record: production model IDs and hashes; pipeline timing; any data-refresh issues; screenshots of the dashboard views (saved under `reports/figures/dashboard/`); user feedback from MI-12.

## 11. Handoff

P17 includes the brief samples and dashboard in the final verification and report.

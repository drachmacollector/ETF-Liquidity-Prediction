# ETF Premium Early-Warning for Gold & Silver ETFs
## Technical Master Specification (Scoped Demonstration Project)

**Document role:** the build blueprint. It is deliberately small: one clear problem, one AI core, one demonstration. A companion Project Research Document holds the market, regulatory and data context. This document is self-contained for building.
**Spec as-of date:** 4 November 2026 (IST). **Status:** pre-build.
**Tags:** [V] verified against an official document, [R] reported/secondary, [A] assumption, [REC] design decision, [OQ-xx] open question (closed in Phase 0).

---

## 1. The Problem and the Solution in One Page

### 1.1 The problem
Gold and silver ETFs in India are meant to trade close to their NAV. They usually do, but not always. In October 2025 silver ETFs traded **5-10% above their indicative NAV for five straight sessions from 9 Oct** while several fund houses halted inflows into silver ETF fund-of-funds; in late January-February 2026 gold and silver ETFs crashed, with silver ETFs hitting the 20% lower circuit on a 10-15% decline. [R] Sales teams and distributors learned of these dislocations after the fact. Nothing public tells an ETF desk *in advance* that a given ETF is likely to trade at an unusual premium or discount tomorrow.

### 1.2 The question the project answers
> **"Which gold and silver ETFs are likely to trade at an unusually large premium or discount to NAV tomorrow, and how confident can we be?"**

### 1.3 The solution
A machine-learning forecaster that, each trading day, outputs for every gold/silver ETF:
1. a **calibrated prediction interval** for tomorrow's premium/discount (in basis points), and
2. the **probability of a tail dislocation** (an unusually large move away from the ETF's own normal premium),
3. with **plain-language reason codes** (which factors drove the risk),
all evaluated honestly against simple baselines, on a walk-forward backtest and two real events.

### 1.4 What this project is and is not
| Is | Is not |
|---|---|
| A rigorous, reproducible demonstration that a model can give useful advance warning | A production system, API, or software product for Mirae |
| Built on free daily public data | Dependent on paid, intraday, or order-flow data |
| Honest about negative results | A trading signal or investment advice |
| Directly relevant to Mirae's silver/gold ETFs and sales narrative | A GenAI, alerting, or multi-module platform |

### 1.5 Why it is impactful for Mirae (kept simple)
Mirae runs live gold and silver ETFs (`GOLDETF`; silver ETF now `SILVERAG`, ISIN INF769K01KG6) [V], gold/silver ETFs were reported as 54% of all ETF flows in Feb 2026 [R], and its ETF sales team speaks to distributors about exactly these products. The demonstration shows (a) what an advance-warning signal would have looked like in Oct 2025, (b) how Mirae's ETFs compare with peers, and (c) a repeatable method Mirae's own team could adopt with its licensed data.

---

## 2. Scope

### 2.1 In scope
- Gold and silver ETFs (all listed issuers with enough history) plus a few large equity ETFs as **quiet controls**.
- Daily data only (exchange close, AMFI NAV, benchmark/FX proxies).
- Two models (premium interval; tail probability), three baselines, SHAP reason codes.
- Walk-forward backtest, two event replays, a short forward test log.
- A small demo dashboard and a short written report.

### 2.2 Out of scope (parked as future work, documented in the research document)
Price-band simulation under SEBI's 7 Sep 2026 rules; international-ETF structural premiums; anomaly detection; intraday iNAV and pre-open data; GenAI briefs/notice extraction; alerts; REST API, React front end, databases and orchestration; Overnight/Liquid ETFs; any order-flow or creation/redemption modelling (the data does not exist publicly).

### 2.3 Design principles [REC]
1. **One clear question, answered well.**
2. **Probabilities and calibration over raw accuracy.**
3. **Point-in-time honesty:** no information the desk could not have had at the decision time.
4. **Baselines first:** the model must beat the best simple rule, out of sample.
5. **Report negative results.**
6. **Simple tooling:** a laptop, Python, files.

### 2.4 Universe
| Group | Members | Purpose |
|---|---|---|
| **Gold ETFs** | All listed gold ETFs (incl. Mirae `GOLDETF`) with ≥ 250 trading days of history | Core |
| **Silver ETFs** | All listed silver ETFs (incl. Mirae `SILVERAG`, formerly `SILVRETF`) with ≥ 250 trading days | Core; primary event study |
| **Controls** | 4 large liquid equity ETFs (e.g., Nifty 50, Sensex, Bank Nifty, Nifty Next 50) | The model should stay quiet here |
The universe is a small, **hand-verified table** (Section 5.3). ETFs are keyed by **ISIN**, never by ticker (tickers change).

---

## 3. Definitions and Prediction Tasks

### 3.1 Core definitions
- `P(i,t)`: exchange closing price of ETF *i* on day *t* (NSE primary; BSE fallback). Assumed ≈ last-30-minute VWAP [A, OQ-03].
- `NAV(i,t)`: official AMFI NAV for date *t*.
- **Premium in basis points:** `prem(i,t) = 10000 × (P(i,t) − NAV(i,t)) / NAV(i,t)` (positive = premium, 1 bp = 0.01%).
- **Clock caveat:** gold/silver trade globally while the ETF trades 09:15-15:30 IST, and the NAV is struck at a valuation time that may differ from the close [A, OQ-04]. Some measured premium is therefore information timing, not mispricing. The model is told this explicitly via a feature (Section 6), and results are reported with and without high-volatility days.
- **Own-normal premium:** `m60(i,t)` = trailing 60-day median of `prem`; `MAD60(i,t)` = trailing 60-day median absolute deviation. Using the ETF's own normal avoids mislabelling chronic offsets as events.
- **Regime flag:** `regime(t)` ∈ {R0: until 30 Jan 2026; R1: 1 Feb-4 Sep 2026; R2: from 7 Sep 2026}, reflecting changes in exchange price-band rules [V/R]. Used as a feature and for split reporting only; the rules are not simulated.
- **Circuit-lock flag:** `lock(i,t)=1` if the day's close is within 1% of a ±20% move from the prior close (premium on such days can be an artefact of a pinned price). Flagged, kept in data, excluded from headline metrics and reported separately.

### 3.2 Decision time
Forecasts for day *t+1* are produced after day *t* data are complete, including the NAV for *t* (published late in the evening). For the demo, this is a nightly/morning script. Features at day *t* use only data known by then. **Primary horizon h = 1 trading day.**

### 3.3 Task A: premium interval
Predict `prem(i,t+1)`. Output quantiles at **5%, 25%, 50%, 75%, 95%**, calibrated so the 90% interval (5-95%) covers about 90% of outcomes.

### 3.4 Task B: tail dislocation
`E(i,t+1) = 1{ |prem(i,t+1) − m60(i,t)| ≥ max(τ, 3·MAD60(i,t)) }`, where `τ` is a fixed threshold in bps.
- **Choice of τ (frozen before testing):** in Phase 2, choose τ per group (gold, silver, controls) so that the event rate in the *training* period is roughly 2-5% of ETF-days; commodity starting guess 200 bps, controls 50 bps [A]. Report sensitivity at ½τ and 1.5τ.
- Output: calibrated probability `P(E)`.

### 3.5 Risk levels (output mapping)
`Normal` / `Watch` / `High`. Seed rule: Watch if `P(E) ≥ 10%`; High if `P(E) ≥ 30%`. Thresholds are tuned on training data to satisfy an **alert budget**: controls should produce essentially no High alerts, and commodity ETFs no more than about one High alert per ETF-month in non-event periods [REC, to be ratified in Phase 2].

### 3.6 What the system does not claim
Exact premium size or duration; intraday timing; returns; causes; any statement about creation/redemption flows.

---

## 4. Architecture (deliberately simple)

```
 NSE bhavcopy ─┐
 AMFI NAV ─────┤
 Benchmark+FX ─┼─► download scripts ─► raw files (kept untouched)
 Hand-made ────┘                         │
 tables (universe, events)               ▼
                               clean + validate ─► Parquet tables (queried with DuckDB)
                                         │
                       feature builder (point-in-time) ──► labels (separate module)
                                         │                         │
                              baselines + LightGBM models ◄────────┘
                              (A: intervals, B: probabilities, SHAP reasons)
                                         │
                       backtest ─► metrics, event replays, plots
                                         │
                       predictions.csv ─► Streamlit demo ─► short report
```

### 4.1 Technology choices [REC]
| Concern | Choice | Why |
|---|---|---|
| Language | Python 3.12 | ML ecosystem |
| Data | `pandas` + **Parquet + DuckDB** | Small data; fast SQL on files; no servers |
| Models | **LightGBM** (quantile and binary objectives), `scikit-learn` (isotonic calibration), `shap` | Strong on tabular panel data with few events; native quantile loss; explainable |
| Calibration | **Conformalized quantile regression (CQR)** implemented directly; isotonic regression for probabilities | Honest intervals and probabilities |
| Dashboard | **Streamlit + Plotly** | Interactive demo from one Python file; free hosting available |
| Tracking | Plain folders: one run folder per experiment with `config.json`, metrics, plots | No MLflow needed |
| Quality | `pytest`, `pandera` (data checks), `ruff` | Light but real tests |
| Version control | Git/GitHub | Also provides timestamps for the forward log |
**Why gradient-boosted trees rather than deep learning:** events are rare, data are small and tabular; trees are strong, fast, and explainable here. A neural sequence model is a possible later comparison, not part of this project.

### 4.2 Repository layout
```
etf-premium-watch/
  README.md  pyproject.toml  Makefile
  config/ (universe.csv, events.csv, settings.yaml, pre_registration.md)
  data/ (raw/, curated/)           # raw never edited
  src/pw/ (ingest/, clean/, features/, labels/, models/, backtest/, app/)
  tests/
  runs/                            # one folder per experiment
  reports/                         # figures, final report
  forward_log.csv                  # appended daily (optional stretch)
```

---

## 5. Data

### 5.1 Sources used
| ID | Data | Source | Fields used | History | Frequency |
|---|---|---|---|---|---|
| D1 | Exchange end-of-day prices | NSE UDiFF CM bhavcopy (`nsearchives.nseindia.com/content/cm/BhavCopy_NSE_CM_0_0_0_YYYYMMDD_F_0000.csv.zip`); BSE equivalent as fallback | trade date, ISIN, symbol, series, open, high, low, close, last, previous close, volume, turnover, trades (UDiFF headers such as `TckrSymb`, `ClsPric`, `TtlTradgVol`, `TtlTrfVal`, `TtlNbOfTxsExctd`; confirm from a sample file) | Legacy format discontinued 8 Jul 2024: two schemas to normalise [V] | Daily |
| D2 | Official NAV | AMFI `NAVAll.txt` (latest) and NAV-history download (**max 90 days per request**) [V] | scheme code, ISIN(s), scheme name, NAV, date | From launch | Daily |
| D4 | Underlying proxy | Free daily gold/silver series (global futures/spot) converted at USD/INR, plus peer-ETF median NAV return | proxy price, daily return, volatility | Multi-year | Daily |
| D5 | FX | USD/INR daily reference (RBI/FBIL or a public source) | rate | Multi-year | Daily |
| D7 | Scheme master (hand-built) | AMFI scheme list + AMC scheme documents | ISIN, AMFI code, NSE/BSE symbols and history, issuer, metal, inception date, creation unit, benchmark name | Current | Static + change log |
| D10 | Trading calendar | NSE holiday list and special-session notices | open/closed, special sessions (e.g., Sunday 1 Feb 2026) | Annual | Annual |
| Events | Hand-made event table (about 10-15 rows) | Public notices and press (research document §3) | date, type (FoF halt/resume, symbol change, regime change), ETFs affected, source URL | Oct 2025 onward | Static |
**Benchmark note:** Mirae's ETFs track the "Domestic Price of Gold/Silver" [V]; the exact index methodology is unconfirmed [OQ-11], so D4 is a **proxy**, and this is stated wherever it is used.

### 5.2 Ingestion approach
- Simple, idempotent Python scripts: download → save raw file with date and checksum → parse → append to curated Parquet.
- Be polite to servers: identifying user-agent, delays, retry with back-off. Prefer the NSE archive host; keep raw files to avoid re-downloading. Check terms of use for NSE/BSE/AMFI data [OQ-09]; the demonstration uses data for research only.
- **Backfill:** bhavcopy from each ETF's listing (both schemas); AMFI in ≤90-day windows; proxies and FX for the same span.
- **Daily refresh (for the demo and forward log):** run after the NAV is published (late evening) or next morning.

### 5.3 Hand-verified universe table (`universe.csv`)
Columns: `isin, amfi_scheme_code, issuer, metal_or_control, nse_symbol_history, bse_code, inception_date, creation_unit, benchmark_name, include_from, exclude_reason`. **Each row is checked by hand** against the scheme document and AMFI list. A wrong mapping silently corrupts everything, so a mismatch quarantines the ETF. Known trap: Mirae's silver ETF symbol changed `SILVRETF → SILVERAG` on 15 Sep 2025 [R].

### 5.4 Data checks (kept short, enforced by `pandera`)
1. Price sanity: `high ≥ max(open, close, low)`, `low ≤ min(...)`, volume ≥ 0, one row per ISIN/date.
2. NAV sanity: positive; day-over-day NAV change compared with the proxy's return (large gaps flag NAV-timing issues).
3. Cross-source: `|close/NAV − 1| > 25%` goes to manual review.
4. Mapping: every universe ISIN has exactly one AMFI code and at least one exchange symbol.
5. Coverage report per ETF (first/last date, missing days) saved with each run.

### 5.5 Point-in-time rules
- Each feature row for day *t* uses only data dated ≤ *t* where NAV(*t*) is assumed available only after the market close (so premium at *t* is usable for forecasting *t+1* but not for same-day trading).
- Trading-day arithmetic uses the calendar table (holidays, special sessions).
- **Leak test:** an automatic test injects a future value into one input and asserts that the features do not change. Labels live in a separate module that the feature code cannot import.

### 5.6 Known data traps (handled in code)
Symbol and scrip changes; two bhavcopy schemas; NAV valuation time vs close; holiday gaps and special sessions; thin-trade days where close is a stale last price (use trades count); possible unit splits/bonus (check each ETF [OQ-19]); AMFI endpoint format changes [OQ-20]; circuit-lock days (flagged, Section 3.1).

---

## 6. Features

Computed per ETF-day *t*. About 35-45 features in five groups; every feature has a documented lookback and a unit test.

| Group | Features (examples) | Rationale |
|---|---|---|
| **F1 Premium dynamics** | `prem` lags 0-5; rolling mean/median/std over 5/20/60 days; MAD60; z-score vs own 60 days; 5-day slope; max/min over 10 days; days since `|prem|` exceeded τ | Mean-reversion and persistence |
| **F2 Liquidity proxies** | Turnover ÷ 20-day average (ratio and z-score); trades count z-score; (high − low) ÷ close; zero/low-volume days in last 30; stale-price flag | Demand surges and thin trading (proxies only) |
| **F3 Underlying and volatility** | Proxy return over 1/3/5 days; realised volatility over 5/20 days; largest overnight gap in last 5 days; drawdown from 10-day high; **NAV-vs-proxy return residual** (NAV clock-mismatch signal) | Crash/gap conditions and timing mismatch |
| **F4 Peer cross-section** | Peer-group median premium; own premium minus peer median; peer dispersion; share of peers beyond τ | Contagion within gold or silver |
| **F5 Context** | Metal (gold/silver/control); issuer; days since listing; regime flag; days to major demand dates (e.g., Dhanteras/Diwali, Akshaya Tritiya); Union Budget window; holiday-adjacency; active FoF-halt flag (from events table) | Heterogeneity and known demand windows |
**Handling:** robust scaling by group, winsorise extremes, explicit missing-value flags (no silent imputation), and the first 60 days after listing of each ETF are excluded from training (but predicted, flagged "low history").

---

## 7. Models

### 7.1 Baselines (must be beaten)
| ID | Task | Baseline |
|---|---|---|
| B0 | A | **Persistence:** `prem(t+1) = prem(t)`, interval from the ETF's own recent forecast errors |
| B1 | A/B | **Rolling-volatility rule:** event flagged if `|prem(t) − m60| > k·MAD60` (k fitted on training); interval from rolling empirical quantiles |
| B2 | A/B | **Peer-median model:** peer-group rolling quantiles |
The best applicable baseline defines "better".

### 7.2 Core models
- **Task A (premium interval):** LightGBM quantile regression, one model per quantile (5/25/50/75/95%). Pooled across ETFs with metal, issuer and regime as features.
- **Task B (tail probability):** LightGBM binary classifier; class weights tuned in time-ordered validation; probabilities calibrated with isotonic regression on the most recent calibration block.
- **Interval calibration:** conformalized quantile regression using a rolling, time-ordered calibration window (the latest ≥ 250 ETF-days), widening/narrowing intervals to reach the target coverage.
- **Regularisation:** shallow trees, minimum leaf size scaled to event counts, feature subsampling; hyper-parameters picked by Optuna inside **time-series cross-validation on training data only**.
- **Explainability:** SHAP values per prediction mapped to short templates ("turnover 3.2× its 20-day average", "peer silver ETFs trade 180 bps above NAV") → the reason codes shown in the demo.
- **Ablation (one small study):** drop each feature group in turn (F1-F5) and report the loss in skill; this shows *which information drives early warning*.

### 7.3 Why this is the "AI core"
The model learns which combinations of premium history, liquidity stress, underlying volatility and peer behaviour precede dislocations in an *India-specific, event-driven setting* where simple thresholds struggle, and it quantifies its own uncertainty. The value to a desk is the calibrated probability and its explanation, not a point forecast.

---

## 8. Validation and Evaluation

### 8.1 Splitting
- **Walk-forward, expanding window:** train through *T*, test the next block, refit monthly. No shuffling.
- **Purge/embargo:** drop training rows whose label window overlaps the test block; embargo of 5 trading days for rolling features.
- Test blocks begin only after a minimum training history (set in Phase 2 once event counts are known).
- **Regime-split reporting:** results shown for R0, R1 and R2 separately (R2 will be short; say so).

### 8.2 Metrics
| Task | Primary | Also report |
|---|---|---|
| A | **Pinball loss** (mean over quantiles) and % improvement vs best baseline | Coverage of the 90% and 50% intervals; Kupiec test for coverage |
| B | **Brier skill score** vs best baseline | PR-AUC; reliability diagram; precision/recall at the Watch and High thresholds; **lead time** (days of warning before an episode); false alerts per ETF-month; alerts per week |
**Statistics:** block bootstrap (about 10-day blocks, resampling by ETF and time) for 95% confidence intervals; always print the **number of events** next to a metric. With few events, avoid claims whose intervals include "no improvement".

### 8.3 Event studies (the headline demonstration)
| Event | Window | Question | Output |
|---|---|---|---|
| **E1 Silver premium squeeze** | 22 Sep-24 Oct 2025 | Using only data available at the time, did silver ETFs reach `Watch` or higher at least one session before the 5-10% premiums began on 9 Oct 2025, without raising false alarms on controls? | Day-by-day replay: premium, forecast interval, probability, reason codes, peers vs Mirae |
| **E2 Crash stress test** | 26 Jan-13 Feb 2026 | How did the model behave during the crash? (A stress test of the premium model; circuit-lock days are flagged because a pinned price distorts premium.) | Same replay, with lock days marked |
- **Pre-registration:** the definitions of events, τ, thresholds and success criteria are written to `config/pre_registration.md` and frozen before the test runs. Results are reported whatever they are.
- The Oct 2025 event is only a handful of days: treat it as a **case study with context (peers, controls, false-alarm rate)**, not as statistical proof.

### 8.4 Forward test (optional stretch, small)
From the first production run, append each day's predictions to `forward_log.csv` and commit to GitHub (commit timestamps give independent evidence that predictions preceded outcomes). After a few weeks, a simple scorecard compares forecasts with realised premiums, split by R2. No claims beyond the days available.

### 8.5 Hypotheses and pass criteria (numbers fixed in Phase 2 after baselines are measured; none invented in advance)
| ID | Hypothesis | Pass criterion |
|---|---|---|
| H1 | The Task A model beats the best baseline on out-of-sample pinball loss | Improvement with bootstrap 95% CI excluding 0 |
| H2 | Intervals are calibrated | 90% interval coverage within a pre-set tolerance of 90%; Kupiec not rejected at 5% |
| H3 | Task B probabilities are calibrated and add skill | Positive Brier skill vs best baseline; reliability close to the diagonal |
| H4 | E1 is flagged ahead of onset | ≥ 1 silver ETF at `Watch`+ at least one session before 9 Oct 2025, within the false-alert budget |
| H5 | Controls stay quiet | No more than a pre-set number of High alerts per control ETF-month |
A negative result on any hypothesis is reported plainly and discussed.

---

## 9. The Demonstration Deliverable

### 9.1 Streamlit demo (three views, runs locally; optional free hosting)
1. **Risk table:** one row per ETF (Mirae products highlighted): latest premium (bps), 5-95% interval for tomorrow, `P(tail)`, risk level, 20-day premium sparkline, top reason code. Date selector to see any past day.
2. **ETF detail:** price vs NAV chart with premium panel; **forecast fan** (the quantile ribbon with past forecasts vs actuals); probability gauge; reason-code panel; comparison with same-metal peers; event markers (FoF halts, symbol change, regime change).
3. **Event replay:** date slider for E1 and E2 showing "what the system would have said that day", including the Mirae silver ETF vs peers.
Design rules: every number carries its as-of date; tooltips define "premium" and "NAV"; a visible "not investment advice; model estimate" line; clean, readable on a projector.

### 9.2 Written report (about 8-12 pages) and a 2-page summary
Problem and evidence; data and method; baselines and results (with confidence intervals and event counts); event studies; limitations; how a team like Mirae's could use or adopt it; future work. The 2-page summary is the pitch artefact.

### 9.3 Output files
`predictions.csv` (per ETF per day): `isin, asof_date, target_date, regime, prem_now_bps, q05, q25, q50, q75, q95, p_tail, risk_level, top_reasons, lock_flag, low_history_flag, model_id`. Backtest outputs: `metrics.json`, calibration and reliability plots, event replay tables.

---

## 10. Testing (light but real)
| Area | Tests |
|---|---|
| Ingestion | Golden-file tests for both bhavcopy schemas and AMFI file variants; re-run idempotency |
| Universe | One ISIN ↔ one AMFI code; symbol-history lookups (e.g., `SILVRETF`/`SILVERAG`) |
| Calendar | Prior-trading-day logic around holidays and the Sunday 1 Feb 2026 special session |
| Features | Per-feature unit tests; **future-value injection (leak) test**; rebuild-equality test |
| Labels | Isolated module; synthetic-path tests; import-guard test |
| Models | Fixed-seed reproducibility; calibration check on a frozen sample |
| Backtest | Purge/embargo correctness; a "leaky canary" feature (equal to the future label) must be flagged |
| App | Smoke test that the three views load from a sample `predictions.csv` |

---

## 11. Delivery Plan

| Phase | Content | Exit criteria | Rough effort [A] |
|---|---|---|---|
| **P0 Verify and set up** | Close priority open questions (OQ-03, 04, 11, 18, 19, 20); inspect sample bhavcopy/AMFI files; build and verify `universe.csv`; draft `pre_registration.md`; create repo | Sample ingestion works for 3 ETFs; universe table verified | ~1 week |
| **P1 Data** | Backfills; cleaning; checks; calendar; events table; coverage report | Full universe loaded; checks pass; rebuild from raw reproducible | ~1-2 weeks |
| **P2 Features, labels, baselines, EDA** | F1-F5 with tests; labels; baselines B0-B2; premium distributions and event counts; choose and freeze τ, thresholds | Baseline metrics produced; τ frozen; hypotheses' numeric gates set | ~1-2 weeks |
| **P3 Models and backtest** | LightGBM A and B; calibration; SHAP; ablation; walk-forward results; E1 and E2 replays | Backtest report with confidence intervals; H1-H5 evaluated | ~2 weeks |
| **P4 Demo and report** | Streamlit app; report; 2-page summary; optional forward log; README | Demo runs end to end; report complete | ~1-2 weeks |
**Total:** about 6-9 weeks part-time, depending on availability [A]. **Minimum pitch-ready cut:** P0-P3 plus the E1 replay chart and the 2-page summary; the dashboard polishes it.

### 11.1 Stakeholder validation (small, optional but valuable) [OQ-13]
If access to Mirae's ETF team is possible, ask: How do you learn today that an ETF is at a premium? What happened in Oct 2025 and Feb 2026 and what information was missing? What would a useful morning risk list contain? How much advance warning matters? Which products matter most? Use the answers to adjust thresholds and the demo framing.

---

## 12. Success Criteria and Expected Outcome
- **Technical:** H1-H5 evaluated honestly; calibrated intervals/probabilities within pre-set tolerances; controls stay quiet; results reproducible from raw data with one command.
- **Impact:** a clear, defensible answer to "could public daily data have warned a desk before the Oct 2025 silver premium?", shown for Mirae's silver ETF against peers, with a repeatable method.
- **Integrity:** every number in the report traces to a script; limitations are stated.
**Expected outcome:** a clean repository, a backtest report, an interactive demo, and a 2-page summary. If the data show that early warning is genuinely hard on daily data, that is itself a useful, honestly reported finding (and a reason to evaluate the parked intraday/iNAV extension).

---

## 13. Risks and Limitations
| Risk | Impact | Mitigation |
|---|---|---|
| Few extreme events | Low statistical power | Pooled panel, simple models, event case studies, confidence intervals, no over-claiming |
| NAV clock mismatch inflates apparent premium | Spurious signals | Clock features, NAV-vs-proxy residual, high-volatility subset reporting |
| Benchmark proxy differs from the fund's true index | Biased features | State clearly; check proxy-vs-NAV return correlation; OQ-11 |
| Regime changes (1 Feb and 7 Sep 2026; 1 Apr 2027 planned) | Non-stationarity | Regime feature and split reporting; short R2 sample acknowledged |
| Data access/format changes | Pipeline break | Keep raw files; golden-file tests; fallbacks |
| ISIN/symbol mapping errors | Silent corruption | Hand verification; quarantine on mismatch |
| Data terms of use | Legal exposure | Research use only; check terms (OQ-09) |
| Over-claiming | Credibility loss | Pre-registration; limitations section |
| Scope creep | Delay | Parked-features list below; phase gates |

---

## 14. Open Questions and Assumptions (scoped)
| ID | Item | Phase |
|---|---|---|
| OQ-03 | Is NSE/BSE `ClsPric` for ETFs the last-30-minute VWAP? (affects premium timing) | P0 |
| OQ-04 | NAV valuation time/method for gold/silver ETFs (per scheme document) | P0 |
| OQ-09 | Terms of use for NSE/BSE/AMFI data | P0 |
| OQ-11 | Methodology of "Domestic Price of Gold/Silver" used by Mirae; choice of proxy | P0-P1 |
| OQ-13 | What Mirae's ETF sales/product team actually needs; internship timeline | P0, ongoing |
| OQ-18 | Conflicting facts (e.g., Mirae silver ETF inception date: 9 vs 14 Jun 2023) | P0 |
| OQ-19 | Corporate actions (unit splits/bonus) in the universe | P1 |
| OQ-20 | Stability of AMFI download format | P1 |
| A-1 | Daily data carry some early signal of building premium pressure | P3 (the core empirical question) |
| A-2 | Boosted trees are adequate for this panel | P3 |
| A-3 | An alert budget of about one High alert per ETF-month is acceptable to a desk | P2/P4 with feedback |

---

## 15. Parked Future Extensions (not built; groundwork exists in the research document)
1. **Price-band simulator** for SEBI's 7 Sep 2026 rules (base price, ±10%/±6% bands, cooling-off, flexing) with counterfactual replay of Feb 2026.
2. **International ETF structural-premium monitor** (e.g., Mirae NYSE FANG+ trading 20-30%+ above NAV because of overseas limits).
3. **Anomaly detection** running alongside the supervised models.
4. **Intraday iNAV and pre-open auction capture** for intraday premium forecasts.
5. **GenAI layer**: grounded daily briefs and structured extraction from exchange/AMC notices.
6. **Production features:** API, authentication, alerts, databases, orchestration, monitoring, deployment inside an AMC with licensed data.
7. **Attention/news features** and **distributor-intelligence** modelling.

---

## 16. Glossary
- **NAV / iNAV:** official end-of-day net asset value per unit / intraday indicative estimate.
- **Premium/discount:** ETF market price relative to NAV (positive = premium); in basis points (1 bp = 0.01%).
- **Market maker:** exchange member appointed by the AMC to quote two-way prices and create/redeem units directly with the AMC.
- **Fund-of-funds (FoF):** a fund that buys an ETF and is bought at NAV through the AMC.
- **Pinball loss:** loss function for quantile forecasts. **CQR:** conformalized quantile regression (calibrates interval coverage). **Brier score:** mean squared error of a probability forecast; **Brier skill score** compares it with a baseline. **Reliability diagram:** predicted probability vs observed frequency.
- **Walk-forward:** train on the past, test on the next block, roll forward. **Purge/embargo:** removing overlapping data to prevent leakage.
- **Regimes R0/R1/R2:** rule periods defined in §3.1.

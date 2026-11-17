# ETF Liquidity Early-Warning System (ELEWS)
## Technical Master Specification: Architecture, Data, Models, Validation, Serving, Delivery

### NOTE : THIS IS THE OLDER VERSION, and it has been superseded by "final ETF_Liquidity_Technical_Master_Specification (1).md". This old version is kept for reference as it contains details that are out of scope of the project, however you may refer to it incase additional in-depth knowledge on any topic mentioned in "final ETF_Liquidity_Technical_Master_Specification (1).md" is required. Do not refer to this for any out of scope information or model architecture or training data, it should be strictly implemented using the new specification document i.e. "final ETF_Liquidity_Technical_Master_Specification (1).md".

**Document role:** the definitive build blueprint. A companion Project Research Document holds the evidence, regulation and market context; this document restates only what the build needs and refers to research IDs (`OQ-xx`, archetypes A-E) by name where helpful. It is written so that detailed phase-level implementation plans can be derived from it directly.
**Spec as-of date:** 4 November 2026 (IST). **Status:** pre-build; no code exists.
**Evidence tags used:** [V] verified against an official document, [R] reported/secondary, [A] assumption, [REC] design recommendation, [OQ-xx] open question to be closed in Phase 0.

---

## 1. Product Definition

### 1.1 One-paragraph description
ELEWS ingests daily exchange prices, official NAVs, commodity/FX benchmarks, event notices and (forward-collected) iNAV/pre-open snapshots for a defined universe of Indian ETFs; maintains a point-in-time feature store; and produces, every trading day before the open, **calibrated probabilistic forecasts** of (A) next-session premium/discount to NAV, (B) tail-dislocation events, (C) extreme-excursion / price-band stress under SEBI's 7 Sep 2026 framework, (D) structural (cap-driven) premium shifts for international ETFs, plus (E) an independent anomaly flag. A GenAI layer converts those structured outputs into number-grounded **sales and product briefs** and extracts structured events from exchange/AMC notices. A React dashboard and a REST API serve the results; a monitoring layer tracks data health, calibration and drift; and an **immutable forward ledger** records every prediction so that out-of-sample claims are verifiable.

### 1.2 Who it is for and what they do with it
| Persona | Need | Primary surface |
|---|---|---|
| **ETF sales head / national sales team / relationship managers** | "Which of our ETFs is at risk today, what do I tell distributors?" | Risk Board, Sales Brief, event replay pack |
| **ETF product manager / fund manager** | Early read on premium/stress for FoF gating, NFO timing, market-maker quality, regime effects | ETF Detail, Product & Regime view, Alerts |
| **Compliance/risk (secondary)** | Audit trail, wording safety, regime tracking | Ledger, model cards, brief logs |
| **Evaluator (internship panel)** | Evidence the AI works, honestly measured | Event replays, backtest report, forward ledger |

### 1.3 Design principles [REC]
1. **Operational usefulness over academic novelty:** every model output maps to a decision a sales/product person makes (use cases U1-U8 in the research document).
2. **Probabilities, not points; calibration over accuracy.**
3. **Point-in-time or nothing:** no feature may use information unavailable at the decision time.
4. **Baselines first, always reported alongside.**
5. **Honest scope:** descriptive risk language; no returns forecasts; no buy/sell advice.
6. **AI is central, but grounded:** ML for forecasting; LLMs only on structured inputs with validators.
7. **Version the regime:** market rules are part of the data-generating process.

---

## 2. Scope

### 2.1 Tiered scope
| Tier | Content | Phase |
|---|---|---|
| **T1 (MVP, pitch-ready)** | Data platform (D1, D2, D4, D5, D7, D10); features; labels; baselines; Tasks A, B, C(excursion), E; walk-forward backtest; two event replays; dashboard (board, detail, replay); forward ledger started | P0-P5 |
| **T2** | Band engine with counterfactual replay; Task D (international structural monitor); GenAI briefs and notice extraction; alerts; forward iNAV/pre-open capture | P4, P6 |
| **T3** | Alternative-data module (attention/news) with ablation; sequence-model comparison; intraday collector upgrade; distribution-intelligence extension | P8 |

### 2.2 Out of scope (do not silently expand)
Trading/execution or position sizing; return/price-direction forecasting; creation/redemption order-flow modelling (data does not exist); Overnight and Liquid ETFs (fixed ±5% band, cash-management use); investor-level personalisation; any client-facing distribution without compliance review.

### 2.3 ETF universe
| Segment | Members | Role |
|---|---|---|
| **U1 Commodity** | All listed gold and silver ETFs, all issuers, incl. Mirae `GOLDETF` and Mirae Silver ETF (`SILVERAG`, formerly `SILVRETF`, ISIN INF769K01KG6) | Core; archetypes A, B, C |
| **U2 International** | Mirae NYSE FANG+ (`MAFANG`), Mirae Hang Seng TECH, other listed overseas-underlying ETFs | Archetype D |
| **U3 Controls** | 6-8 large liquid equity ETFs (Nifty 50, Sensex, Bank Nifty, Next 50) | Negative controls: model must stay quiet |
| **U4 Thin/thematic** | Mirae `DEFENCE` (ISIN INF769K01QC2) and other 2026 launches, sector/thematic ETFs | Archetype E |
| **U5 Monitor-only** | Hybrid ETF (listed Jul 2026), ETFs with <120 trading days | Forward monitoring, not trained on |
Universe membership is a versioned table with `valid_from/valid_to`; delisted/merged ETFs remain (survivorship).

---

## 3. Domain Definitions (normative)

### 3.1 Prices and premium
- `P_close(i,t)`: exchange close for ETF *i* on day *t* (NSE primary, BSE fallback), with `ClsPric` assumed ≈ last-30-min VWAP [A, OQ-03].
- `NAV(i,t)`: official AMFI NAV for valuation date *t*.
- **Daily premium (bps):** `prem(i,t) = 10000 × (P_close(i,t) − NAV(i,t)) / NAV(i,t)`.
- **Clock-risk flag:** `clock_risk(i,t)=1` if underlying trades outside domestic hours or the NAV valuation time differs from the close (all gold/silver and international ETFs) [A, OQ-04]. Used as a feature and for reporting; it is not used to "correct" the label.
- **iNAV-based intraday premium** is out of the MVP target (no free history). It is collected forward (Section 7.5) for later use.

### 3.2 Regimes
| Regime | Window | Rule set |
|---|---|---|
| **R0** | until 30 Jan 2026 | ±20% band on T-2 NAV (overnight ±5%) [V] |
| **R1** | 1 Feb - 4 Sep 2026 | Interim: exchanges (BSE circular 1 Feb 2026) used T-1 NAV/price reference for gold/silver, ±20% [R]; NSE treatment to confirm [OQ-10/OQ-14] |
| **R2** | from 7 Sep 2026 | SEBI 15 Jun 2026 framework (T-1 last-30-min VWAP base; ±10%/±6% dynamic bands; gold/silver pre-open auction) [V] |
| **R3 (planned)** | from 1 Apr 2027 | T-1 closing NAV as base price target [V] |
`regime_id(date)` is a table; every feature row, label and prediction carries it.

### 3.3 Band engine definitions (R2)
- `Base(i,t)` = T-1 last-30-min VWAP; fallbacks: LTP of day; else latest closing NAV; adjusted for corporate actions.
- **Equity/debt ETFs:** initial ±10%; cooling-off trigger at ±9.90% from base; flex +5% of base on the side hit, max 2 flexes per direction (hard ±20%).
- **Commodity ETFs:** initial ±6%; trigger at ±5.90%; flex +3% of base on the side hit; no cap, no limit on flex count; exchange may additionally relax in 3% stages when international moves exceed ±9%.
- Cooling-off: 15 minutes; 5 minutes if triggered in the last 30 minutes. Flex only in the direction of the move; flex on one exchange applies on the other. [V]

### 3.4 Archetypes (A-E)
Physical supply squeeze, demand surge, crash/band lock-up, structural cap-driven premium, thin-liquidity drift (see research document §2.4). `archetype_group` is a field on the security master, and an ETF can carry multiple tags.

---

## 4. Prediction Tasks and Label Definitions

**Decision time:** forecasts are issued after day *t* data (including NAV(t), published late evening) are available and are re-issued at 08:15 IST on *t+1*; the **Morning Brief** goes out by 08:30, before pre-open (09:00). **Primary horizon h=1 trading day**; secondary h=3 (cumulative max).

| Task | Target | Output | Applies to | Evaluation |
|---|---|---|---|---|
| **A. Premium distribution** | `prem(i,t+1)` in bps | Quantiles q ∈ {0.05, 0.10, 0.25, 0.50, 0.75, 0.90, 0.95}, conformally calibrated | U1-U4 | Pinball loss, coverage, PIT |
| **B. Tail dislocation** | `E_k = 1{ abs(prem(i,t+1) − m60(i,t)) ≥ max(τ_k(group), 3·MAD60(i,t)) }` with `m60` the trailing 60-day median (removes chronic offsets such as international premiums) | `P(E_1)`, `P(E_2)`, `P(E_3)` (calibrated) | U1-U4 | Brier, PR-AUC, reliability, lead time |
| **C. Extreme excursion / band stress** | `X_c(i,t+1)=1{ max(abs(High−Base), abs(Low−Base))/Base ≥ θ(category) }`, θ = 5.9% (commodity), 9.9% (equity/debt) | `P(X)` plus expected-excursion quantile; band-state features in R2 | U1-U4 | Brier, PR-AUC, event recall at fixed alert budget |
| **D. Structural premium shift (international)** | Change in 20-day median premium ≥ δ (e.g., 300 bps) within 20 days; and classification of "primary market open/closed" state from FoF/notice events | `P(shift up)`, `P(shift down)`, state label | U2 | Brier, state accuracy, event timing |
| **E. Anomaly** | Unsupervised score on the multivariate feature vector (no label) | Score percentile + flag | All | Event recall at alert budget; false alerts per ETF-month |

Notes:
- **τ_k(group)** (initial, to be ratified in Phase 0 once distributions are measured): commodity {100, 200, 300 bps}, equity broad {30, 60, 100}, thematic/thin {100, 200, 300}. Thresholds are frozen *before* test periods are evaluated.
- **Task C is regime-independent by construction** (an excursion vs the prior close is observable historically), so it can be trained and backtested on R0-R1 data. Two documented caveats: (i) old-regime prices were censored by the ±20%/T-2 band (lock-ups), and (ii) behaviour under cooling-off/flex differs, so R2 performance must be reported separately and the pre-R2 result labelled counterfactual. [REC]
- **Labels use only data of day t+1** and are generated by a dedicated labelling module that cannot be imported by feature code (leak guard, Section 10.4).
- **What the system does not claim:** exact premium magnitude/duration; intraday timing; returns; causal attribution; any statement about creation/redemption order flow.

### 4.1 Risk levels (output mapping)
`Normal / Elevated / High / Critical`, derived from calibrated probabilities and the anomaly flag with per-group operating thresholds chosen to meet an **alert budget** (target: ≤ 1 High alert per ETF-month in non-event periods; ratified after baseline measurement). Default seed rule: Elevated if P(E_2) ≥ 10% or anomaly p ≥ 97.5; High if P(E_2) ≥ 30% or P(X) ≥ 25%; Critical if P(E_3) ≥ 30% or P(X) ≥ 50%. [REC]

---

## 5. System Architecture

### 5.1 Logical architecture
```
 SOURCES                      INGESTION                 STORAGE                    ML / LOGIC                     SERVING
 NSE/BSE bhavcopy (D1) ─┐
 AMFI NAV (D2/D7) ──────┤    Prefect flows       ┌─► Raw zone (immutable files)
 MCX/IBJA/LBMA, FX (D4/5)┼──► per-source adapters ┤   S3-compatible / local FS
 Calendar, circulars (D9/10)┤  + validators        ├─► Curated zone (Parquet, DuckDB)
 iNAV & pre-open snaps ──┤   + contract tests      └─► PostgreSQL (serving + registry)
 (forward-collected)    ─┘                                     │
                                                     Feature builder (point-in-time) ──► Labeler (isolated)
                                                              │                                   │
                                  Baselines ◄─────────────────┼────────────────► Core models (LightGBM quantile/classifiers
                                                              │                    + conformal calibration; Task A-D)
                                                              ├──► Anomaly (IForest + robust Mahalanobis + BOCPD)
                                                              ├──► Band engine (R2 rules, simulator, counterfactual replay)
                                                              ▼
                                            Prediction service ──► Forward ledger (hash-chained, append-only)
                                                              │
                                    GenAI layer (notice extraction; brief writer; validators)
                                                              │
                                    FastAPI (REST, auth) ──► React dashboard │ Alerts (email/Telegram) │ PDF/CSV export
 Monitoring: data-health, calibration, drift, pipeline SLA ──► Admin page + alerts   MLflow registry
```

### 5.2 Modules and responsibilities
| Module | Responsibility | Interfaces |
|---|---|---|
| `ingest/` | One adapter per source (bhavcopy, AMFI, benchmarks, FX, circulars, snapshots); retries, backoff, checksums; writes raw then curated | Input: schedules; output: raw files + curated tables |
| `security_master/` | ISIN-keyed master, symbol history, scheme-code mapping, archetype tags, universe versions | Used by every module |
| `calendar/` | NSE trading days, special sessions, T-1 resolution, regime table | Feature/label timing |
| `quality/` | Data contracts (pandera), cross-source reconciliations, freshness SLAs | Blocks bad data from curated zone |
| `features/` | Point-in-time feature builder with `asof` semantics | Output: feature Parquet + metadata |
| `labels/` | Label generation for Tasks A-D (isolated package) | Backtest only |
| `models/` | Baselines, LightGBM models, conformal calibration, anomaly detectors, (T3) sequence models | MLflow-tracked |
| `band_engine/` | Deterministic implementation of SEBI rules, scenario simulator, historical counterfactual replay | Library + API |
| `backtest/` | Walk-forward engine, event studies, statistical tests, reports | Reproducible CLI |
| `ledger/` | Append-only prediction log with hash chain; outcome joiner | Forward evidence |
| `genai/` | Notice extractor, brief writer, validators, eval harness | LLM API, strict JSON schemas |
| `api/` | FastAPI app, auth, schemas | React, exports |
| `web/` | React dashboard | API |
| `monitor/` | Drift, calibration decay, pipeline health, alerting | Admin page |

### 5.3 Technology choices and rationale [REC]
| Concern | Choice | Why |
|---|---|---|
| Language | **Python 3.12** (ML/data/API), **TypeScript** (frontend) | ML ecosystem; type safety on UI |
| Analytical store | **Parquet + DuckDB** | Tiny data (hundreds of ETFs × years), fast SQL on files, zero ops, reproducible snapshots |
| Operational DB | **PostgreSQL 16** (managed free tier, e.g., Neon/Supabase) | Serving tables, registry, ledger metadata; JSONB for payloads |
| Orchestration | **Prefect** (or cron + `make` for MVP) | Python-native flows, retries, run history; trivial to self-host |
| Modelling | **LightGBM** (quantile + binary), `scikit-learn` (isotonic, IForest), `shap`, `ruptures`/custom BOCPD; T3: PyTorch + `pytorch-forecasting` (TFT) | Tabular panel data with few events: boosted trees are strong, fast, explainable; quantile objective is native |
| Calibration | **Conformalized quantile regression** and isotonic regression on time-ordered calibration windows | Coverage guarantees under exchangeability approximation; honest probabilities |
| Experiment tracking | **MLflow** | Registry and lineage |
| API | **FastAPI + Pydantic v2** | Typed schemas, OpenAPI docs |
| Frontend | **React 18 + Vite + TypeScript + TanStack Query + Apache ECharts + Tailwind** | Fits skills in React/JS; ECharts handles fan charts, band overlays, heatmaps |
| Auth | **Firebase Auth** (JWT verified in FastAPI) or API-key for MVP | Reuses known stack; simple |
| LLM | An Anthropic model via API (verify current model strings at build time; e.g., `claude-sonnet-5-5`), strict JSON output + validators | Quality of extraction/brief writing; guardrails are code, not prompts |
| Packaging/CI | Docker, docker-compose, **GitHub Actions** | Reproducible |
| Quality | `pytest`, `hypothesis`, `pandera`, `ruff`, `mypy`, `pre-commit` | Data-contract and property tests |
| Hosting (MVP) | Frontend on Firebase Hosting/Vercel; API + jobs on one small VM or Cloud Run; free-tier Postgres | Near-zero cost |
**Why not deep learning first:** large premium events are rare; boosted trees on engineered panel features typically generalise better with few events and are explainable. A sequence model is a *comparison*, not the default. This is an empirical question, settled in P3 and reported either way.

---

## 6. Data Platform

### 6.1 Zones and lineage
- **Raw zone:** every downloaded file stored unmodified, named by source/date/checksum, with fetch metadata. Never overwritten.
- **Curated zone (Parquet):** normalised schemas, one table per entity, partitioned by date; every row has `source_file`, `ingested_at`, `known_at`.
- **Serving DB (PostgreSQL):** latest features, predictions, ledger, events, alerts, briefs, registry pointers.
- **Snapshots:** versioned dataset snapshots (DuckDB file + manifest) for each backtest run (reproducibility).

### 6.2 Core schemas (abridged DDL)
```sql
-- identity
security_master(isin PK, amfi_scheme_code, amc, scheme_name, category, archetype_group,
  benchmark_id, benchmark_name, inception_date, creation_unit, status, listed_nse bool, listed_bse bool,
  universe_tier, valid_from, valid_to);
symbol_history(isin, exchange, symbol, scrip_code, valid_from, valid_to, PRIMARY KEY(isin,exchange,valid_from));
trading_calendar(date PK, nse_open bool, bse_open bool, session_type text, notes text, regime_id int);

-- market data
eod_price(isin, exchange, date, open, high, low, close, last, prev_close, volume, turnover, trades,
  source_file, ingested_at, PRIMARY KEY(isin, exchange, date));
nav(isin, amfi_scheme_code, nav_date, nav, published_at_observed, known_at, source_file, PRIMARY KEY(isin, nav_date, known_at));
benchmark_price(series_id, date, value, unit, source, known_at, PRIMARY KEY(series_id,date,known_at));
fx_rate(pair, date, rate, source, known_at);
inav_snapshot(isin, ts_ist, inav, last_price, source, PRIMARY KEY(isin, ts_ist));
preopen_snapshot(isin, ts_ist, indicative_price, matched_qty, unmatched_buy, unmatched_sell, PRIMARY KEY(isin, ts_ist));  -- R2+, forward-collected

-- events (LLM-extracted + manual)
event(event_id PK, isin NULL, event_type, announced_at, effective_date, source_url, extracted_json, review_status, reviewer, created_at);
  -- types: SUBSCRIPTION_HALT, SUBSCRIPTION_RESUME, FOF_LIMIT, BAND_RELAXATION, MM_CHANGE, SYMBOL_CHANGE,
  --        CREATION_UNIT_CHANGE, TER_CHANGE, NFO, LISTING, CORPORATE_ACTION, REGULATORY_CIRCULAR

-- modelling
feature_row(isin, asof_date, regime_id, feature_set_version, features JSONB, PRIMARY KEY(isin, asof_date, feature_set_version));
prediction(prediction_id PK, isin, asof_date, target_date, model_id, task, horizon, quantiles JSONB, probs JSONB,
  risk_level, anomaly_score, anomaly_flag, reason_codes JSONB, regime_id, created_at, prev_hash, row_hash);
outcome(prediction_id, realized JSONB, joined_at);
model_registry(model_id PK, task, algo, trained_through, params JSONB, metrics JSONB, mlflow_run, status);
alert(alert_id, isin, prediction_id, level, channel, sent_at, acked_by, usefulness_label);
brief(brief_id, isin, asof_date, audience, json_content, validator_report, model_version, created_at);
backtest_run(run_id, config JSONB, dataset_snapshot, metrics JSONB, report_uri, created_at);
data_quality_log(check_id, run_ts, source, check_name, status, details JSONB);
```
Principle: `known_at` makes every datum bitemporal (valid date vs when we could have known it). Joins for features use `known_at <= decision_time`.

### 6.3 Ingestion jobs (IST schedule on trading days)
| Time | Job | Source | Notes |
|---|---|---|---|
| 08:10 | Calendar/notice sweep | Exchange circular pages, AMC notice pages | LLM extraction queue |
| 09:00-09:15 | **Pre-open snapshots** (R2, gold/silver ETFs) | NSE/BSE pre-open pages | Every 30-60 s; store final indicative price/matched qty (D8) |
| 09:15-15:30 | **iNAV/price snapshots** every 5 min for U1-U4 | NSE/BSE/AMC iNAV | Forward archive for future intraday work |
| 16:30-18:00 | **EOD bhavcopy** (NSE UDiFF; BSE) | `nsearchives.nseindia.com/content/cm/…` | Retry every 15 min until present |
| 18:00-23:30 | **AMFI NAV** (`NAVAll.txt`; history endpoint for backfill/revision check) | AMFI | NAV for day *t* typically arrives late evening; mark `published_at_observed` |
| 23:00-23:45 | Features + forecasts (preliminary) | - | If NAV(t) missing for an ETF, flag stale and use latest NAV with penalty |
| 07:45-08:15 | Reconciliation, NAV completion, **final forecasts**, ledger write | - | Final predictions are the ledger entries |
| 08:30 | Briefs and alerts dispatched | - | After validators pass |
Backfill jobs (one-off): bhavcopy from each ETF's listing (two schemas), AMFI history in ≤90-day windows, benchmarks, FX.

### 6.4 Data contracts and validation (examples)
- Bhavcopy: `high ≥ max(open,close,low)`, `low ≤ min(...)`, volume ≥ 0, ISIN present, one row per ISIN/exchange/date.
- NAV: positive, daily change within sanity band vs benchmark return (flags NAV timing issues); no duplicates per `(isin, nav_date)` unless revision (then new `known_at`).
- Cross-source: `abs(close/NAV − 1)` > 25% triggers manual review (data error or true crisis).
- Mapping: every universe ISIN must resolve to exactly one AMFI scheme code and ≥1 exchange symbol; failures quarantine the ETF.
- Freshness: SLA per source; breaches create `data_quality_log` entries and admin alerts; predictions for impacted ETFs are flagged `degraded`.
- Schema drift: contract tests detect format changes (e.g., NSE dissemination changes; AMFI endpoint changes) [OQ-20].

### 6.5 Point-in-time (PIT) handling
- Feature builder takes `decision_time`; only rows with `known_at ≤ decision_time` are visible.
- T-1 resolution uses the trading calendar (holidays, special sessions such as Sun 1 Feb 2026).
- Unit tests include "future-poisoning" (inject a future value, assert features unchanged) and a full rebuild equality test (features rebuilt from snapshot equal stored features).

### 6.6 Security master construction (the highest-risk data step)
1. Seed from AMFI scheme master + NSE/BSE ETF lists; join on ISIN.
2. Parse SID/KIM for benchmark, creation unit, market makers, iNAV frequency; store extracted fields with source URL and human verification flag.
3. Track symbol changes from exchange notices (e.g., `SILVRETF`→`SILVERAG`, 15 Sep 2025 [R]).
4. A wrong mapping silently corrupts everything: quarantine on mismatch; **manual verification sign-off per ETF** in Phase 1.

### 6.7 Forward-collected datasets (start immediately, even before models exist)
Pre-open snapshots (D8), 5-minute iNAV/price snapshots, and exchange/AMC notices. These cannot be recovered retroactively and make T2/T3 intraday work possible later. Check terms of use [OQ-09].

---

## 7. Feature Engineering

All features computed per ETF-day at decision time. Feature sets are versioned; each feature has a unit test and a documented lookback.

| Group | Features (examples) | Rationale |
|---|---|---|
| **F1 Premium dynamics** | `prem` lags 0-10; rolling mean/median/std (5, 20, 60d); MAD60; EWMA; z-score vs own 60d; slope of last 5d; max/min over 10d; sign persistence; days since |prem|>τ; AR(1) residual | Mean-reversion and persistence structure |
| **F2 Liquidity / microstructure proxies** | Turnover vs 20d mean (ratio, z); volume surge flag; trades count z; High-Low range % ; close-to-VWAP proxies if available; Amihud-style `abs(return)/turnover`; zero-volume days (30d); price staleness | Thin-liquidity and demand-surge signals (all proxies) |
| **F3 Underlying/benchmark** | Benchmark 1/3/5-day return; realised vol (5/20d); gap size; drawdown from 10d high; benchmark return minus ETF NAV return (NAV/benchmark tracking residual → NAV staleness flag) | Crash/gap and clock-mismatch detection |
| **F4 Import-parity/basis (commodity)** | Domestic spot vs (global price × USD/INR) ratio and change; z of the ratio; domestic premium over import-parity proxy | The signal the AMCs themselves cited in Oct 2025 (premium over import parity); requires duty/tax inputs [OQ-12] |
| **F5 Cross-sectional peers** | Peer-group median premium; own premium minus peer median; dispersion; fraction of group with |prem|>τ; leader-follower lags (e.g., silver peers) | Contagion within a category |
| **F6 Calendar/seasonality** | Days to Dhanteras/Diwali/Akshaya Tritiya/wedding season; Union Budget and policy dates; month-end; holiday adjacency; special-session flag | Narrative-driven demand windows |
| **F7 Event/state (from notices)** | FoF suspension active (days since); NFO/launch age; MM change; symbol/benchmark change; regulatory-notice flags; **overseas headroom state** for U2 [OQ-08] | Primary-market constraint states |
| **F8 Regulatory-regime & band state** | `regime_id`; current band width category; distance of prior close (and prior-day High/Low) to band edge as % of base; trailing count of cooling-off-trigger days (proxy); in R2: pre-open indicative price vs prior close | Band-stress prediction; regime interactions |
| **F9 (T3) Attention/sentiment** | Google Trends indices (gold/silver/ETF queries), news headline sentiment, aggregated daily | Optional; accepted only if ablation shows gain |
| **Static** | `archetype_group`, issuer, creation unit, age (days listed), AUM bucket (monthly), TER | Heterogeneity across ETFs |

**Handling known pitfalls:** per-group scaling (robust), winsorisation of extreme values, no imputation across NAV gaps without a flag, explicit missingness indicators, and exclusion of the first 60 days post-listing from training for each ETF (still predicted and flagged as low-history).

---

## 8. Models

### 8.1 Baselines (mandatory comparison points)
| ID | Task | Baseline |
|---|---|---|
| B0 | A | Persistence: `prem(t+1) = prem(t)` with empirical-residual quantiles |
| B1 | A/B | **Rolling-volatility threshold:** flag if `abs(prem(t) − median60) > k·MAD60`; quantiles from rolling empirical distribution |
| B2 | A/B | Peer-median model: group-level rolling quantiles |
| B3 | C | **Gap-rule baseline:** flag if prior-day absolute close-to-close move ≥ x% or benchmark overnight move ≥ y% (x,y fitted on training only) |
| B4 | C | Band-proximity rule (R2): flag if prior-day extreme excursion within 1 percentage point of the trigger |
| B5 | D | Persistence of the 20-day premium level; FoF-halt flag as a rule |
| B6 | E | Univariate z-score/MAD on premium and turnover |
A model is only "better" if it beats the **best** applicable baseline, out-of-sample, on pre-specified metrics.

### 8.2 Core forecasting models (Tasks A-D)
- **Algorithm:** LightGBM. Task A: seven quantile models (objective `quantile`, one per α) or a monotone-rearranged set; Tasks B/C/D: binary classifiers with `is_unbalance`/class weights tuned in time-ordered CV.
- **Panel design:** one **pooled model per task** with `archetype_group` and issuer as categorical features, versus **per-archetype models**; choose by out-of-sample pinball/Brier (hierarchical comparison). Pooling is the default because events are few.
- **Constraints/regularisation:** shallow trees, min-data-in-leaf scaled to event counts, feature-fraction, L1/L2; monotone constraints on selected features (e.g., higher recent excursion cannot lower P(X)) where economically defensible.
- **Hyper-parameter search:** Optuna inside **nested time-series CV** (inner expanding windows, purge/embargo), objective = pinball loss (A) / Brier+logloss (B-D).
- **Calibration:** (A) **Conformalized Quantile Regression** with a rolling calibration window (last ≥250 observations, time-ordered); (B-D) isotonic or Platt calibration fitted on the most recent calibration block; evaluate reliability curves per group.
- **Rare-event strategy:** report Brier skill score and PR-AUC against baselines; no oversampling of the test set; use event-level (episode-level) evaluation in addition to day-level (Section 9.4).
- **Explainability:** SHAP (`TreeExplainer`) per prediction → **reason codes** (top 3-5 features mapped to plain-language templates, e.g., "turnover 3.2x its 20-day average", "peer silver ETFs' premium +180 bps").
- **Task D specifics:** features emphasise FoF/AMC notice state, premium level and change, headroom state, trading-volume shifts; the "primary market open/closed" state is rule-derived from notices where available and model-assisted otherwise.

### 8.3 Sequence-model comparison (T3, within P3 stretch)
Temporal Fusion Transformer (or LSTM/N-BEATS) on the same features with quantile heads; same splits, same metrics. Report whether it beats boosted trees. If not, say so.

### 8.4 Anomaly detection (Task E), parallel to supervised models
- **Detectors:** Isolation Forest on robust-scaled feature vectors (rolling 250-day fit per group), **robust Mahalanobis** distance (Ledoit-Wolf shrinkage), and **Bayesian online change-point detection** on `prem` and turnover.
- **Ensemble:** average rank-normalised scores → percentile; flag at ≥97.5th percentile of own history (configurable).
- **Why parallel:** a supervised model trained on "normal" history underweights novel structural breaks; the dashboard can show "forecast calm, anomaly high" as a legitimate signal.
- **Evaluation:** event recall within [−5, 0] days of episode start at a fixed budget (≤1 false flag per ETF-month on controls); precision on labelled episodes; stability (flag persistence).

### 8.5 Band engine and simulator (Task C support; R2)
Deterministic library implementing Section 3.3, independent of ML.
- **Inputs:** base price, category, intraday price path (simulated or collected).
- **State machine:** `NORMAL → TRIGGERED(cooling-off timer) → FLEXED(n)`; side-specific; last-30-minute rule (5-minute timer); equity/debt: max two flexes per direction; commodity: unbounded; exchange-relaxation hook for ±9% international moves.
- **Interfaces:** `compute_base_price(...)`, `band_edges(state)`, `step(price, timestamp)`, `simulate(path)`.
- **Test vectors (must pass):**
  | Case | Base | Events | Expected |
  |---|---|---|---|
  | Commodity up-trigger | 100 | trade at 105.90 | 15-min cooling-off starts; band remains [94,106] during it; after it upper edge = 109 (base + 3% of base); lower remains 94 (no sliding) |
  | Commodity second flex | 100 | trade at 108.90 after first flex | cooling-off; upper → 112; unlimited further flexes allowed |
  | Equity up-trigger | 100 | trade at 109.90 | cooling-off 15 min; upper → 115; lower remains 90 |
  | Equity cap | 100 | two flexes up (115, then 120) | no third flex; hard ceiling 120 |
  | Last-30-min | 100 | trigger at 15:05 | cooling-off 5 minutes |
  | Base fallback | n/a | no trades last 30 min | base = day's LTP; no trades all day → latest NAV |
  Symmetric behaviour on the downside is assumed (triggers at base×(1−0.0590/0.0990)) [A, confirm with exchange circular, OQ-01].
- **Counterfactual historical replay:** apply R2 rules to historical daily data using the proxy base (prior `ClsPric`, assumption OQ-03) and High/Low excursions to compute, for the Oct 2025 and Jan-Feb 2026 windows, which ETF-days would have **triggered cooling-off** and how often old-regime **circuit lock-ups** (±20% around a T-2 NAV base) occurred. Caveat explicitly: daily bars cannot reproduce intraday cooling-off dynamics, and participant behaviour would differ under the new rules. [REC]

---

## 9. Validation, Backtesting and Evaluation

### 9.1 Splitting protocol
- **Walk-forward, expanding window:** train through *T*, validate *T+1…T+m*, roll monthly. No shuffling.
- **Purge and embargo:** drop training samples whose label window overlaps the validation window; embargo ≥ horizon length (and 5 days for rolling features).
- **Nested tuning:** hyper-parameters selected only inside the training period.
- **Leave-one-event-out (LOEO):** for each named episode, train on data excluding a window around it, then test on the event (Section 9.3).
- **Regime-stratified reporting:** metrics reported separately for R0, R1, R2 and pooled.

### 9.2 Metrics
| Task | Primary | Secondary |
|---|---|---|
| A | **Pinball loss** per quantile, mean over quantiles; improvement vs best baseline (%) | Empirical coverage of 80/90% intervals; Kupiec (unconditional) and Christoffersen (independence) tests; PIT histogram; CRPS approximation from quantiles |
| B, C, D | **Brier score / Brier skill score** vs baseline; PR-AUC | Reliability diagram + ECE; log-loss; precision/recall at the alert threshold; **lead time** (days of warning before episode start); false alerts per ETF-month; alert fatigue (alerts per week) |
| E | Event recall at fixed alert budget | Precision on episodes; persistence |
| Operational utility | **Desk-utility score:** hits × value − false alerts × cost, with explicit, adjustable cost ratio (e.g., 1 missed High event ≈ 5 false High alerts) | Sensitivity analysis over the ratio |
**Statistical inference:** block bootstrap (blocks ≈ 10 trading days, ETF-clustered) for confidence intervals; Diebold-Mariano tests on loss differentials with HAC variance. Because events are few, report event counts next to every metric and avoid claims where intervals overlap zero improvement.

### 9.3 Named event studies (flagship artefacts)
| Event | Window | Question | Output |
|---|---|---|---|
| **E1 Silver supply-squeeze** | 22 Sep - 24 Oct 2025 | Would risk have been "Elevated or higher" for silver ETFs ≥1 session before the 5-10% premiums started on 9 Oct 2025, using only point-in-time data? | Day-by-day replay: premium, forecast fan, probabilities, anomaly flag, peer view, what a sales brief would have said |
| **E2 Crash and band lock-up** | 26 Jan - 13 Feb 2026 | Did Task C/E flag extreme-excursion risk before 1-2 Feb 2026? How many ETF-days would have triggered cooling-off under R2 rules vs how many locked at the old circuit (counterfactual)? | Replay + counterfactual band table |
| **E3 International structural premium** | Jan 2025 - Oct 2026 | Do Task D features anticipate large moves in the MAFANG/Hang Seng TECH premium (e.g., FoF-halt episodes)? | Premium path with event markers |
**Pre-registration:** thresholds, alert rules and success definitions for E1-E3 are written into the repo (`pre_registration.md`) and frozen *before* the first evaluation run. The "did it work" result is reported whatever it is.

### 9.4 Episode-level evaluation
Episode = ≥2 consecutive sessions where ≥2 ETFs in a peer group exceed τ_2 (definition frozen). For each episode: first-alert date at each level, lead time, and affected ETFs; summarise across episodes. With few episodes, present each individually rather than only averaging.

### 9.5 Forward (live) evaluation
- Every final prediction from the first production run is appended to the **hash-chained ledger** (`row_hash = SHA-256(prev_hash || canonical_json)`); a public-readable daily hash can be committed to a repo for tamper evidence.
- Outcomes are joined after target date; a **scorecard page** shows rolling calibration, Brier, alerts and hits since launch, separately for R2.
- **Regime-R2 validation is cumulative:** report the number of R2 days/events available at each reporting date; do not claim validated Task C performance in R2 until a pre-set minimum sample is reached (set in Phase 0, e.g., ≥ 60 trading days and ≥ N excursion events; ratify then).

### 9.6 Ablations and robustness
Feature-group ablation (drop F4, F5, F7, F8, F9 one at a time); pooled vs per-archetype; with/without anomaly input to risk level; calibration on/off; threshold sensitivity; NAV-clock-risk subset analysis (premium measured on days with/without NAV-benchmark residual flags).

### 9.7 Provisional hypotheses and acceptance gates (to be ratified after baselines are measured; no numbers fabricated in advance)
| ID | Hypothesis | Pass criterion (to be numerically fixed in Phase 0) |
|---|---|---|
| H1 | Core Task A model beats best baseline on pooled OOS pinball loss | Improvement with block-bootstrap 95% CI excluding 0 |
| H2 | Intervals are calibrated | 90% interval coverage within a pre-set tolerance around 90%; Christoffersen not rejected at 5% |
| H3 | Task B/C probabilities are calibrated and add skill | Positive Brier skill vs best baseline; ECE below pre-set bound |
| H4 | E1 flagged ahead of onset | ≥1 U1 silver ETF at Elevated+ ≥1 session before 9 Oct 2025 *and* false-alert budget respected on controls |
| H5 | E2 excursion risk flagged ahead of 1 Feb 2026 | As above for Task C/E |
| H6 | Controls stay quiet | ≤ pre-set High alerts per control ETF-month |
| H7 | Tree model vs sequence model | Report; no presumption |
| H8 | Attention data (T3) improves forecasts | Ablation shows significant gain, otherwise drop |
Negative results are first-class outputs.

---

## 10. GenAI Layer (makes the AI directly useful to a sales organisation)

### 10.1 Functions
| Function | Input | Output | Used by |
|---|---|---|---|
| **G1 Notice extractor** | Exchange circular/AMC notice HTML/PDF text | Structured `event` JSON (type, ETF(s), dates, key terms) → human review queue | Product, ops; feeds features F7 |
| **G2 Brief writer** | Structured JSON: ETF facts, latest premium, forecast probabilities, top reason codes, peer comparison, regime, calendar flags, recent events | `Brief` JSON: headline, risk level, what changed, why it matters for sales, 3-5 factual talking points, caveats | Sales head/RMs (U1-U3, U5, U8) |
| **G3 Event pack generator** | Event-study outputs | One-page replay summary for pitches/distributor communication | Sales/product |
| **G4 Q&A over outputs (optional)** | Question + retrieved structured outputs (no free web) | Answer with cited fields | Internal users |

### 10.2 Guardrails (enforced in code)
1. **Closed-world inputs:** the model receives only the structured JSON; no browsing, no free-text financial data.
2. **Numeric faithfulness validator:** every number in the output must match an input field within rounding; otherwise reject and regenerate (max 2 retries) or fall back to a template.
3. **Language policy:** banned phrases/patterns (buy/sell/hold, "will rise/fall", guarantees, return predictions); mandatory descriptive wording and disclaimer line; compliance wording can be replaced by Mirae's approved language.
4. **Schema-constrained outputs** (JSON schema) and length caps.
5. **Audit log:** prompt version, input hash, output, validator report stored in `brief`.
6. **Human-in-the-loop** for G1 until measured extraction accuracy is acceptable.

### 10.3 Evaluation of the GenAI layer
G1: hand-label ≥50-100 notices; report field-level precision/recall and event-type accuracy. G2: faithfulness pass rate (automatic), a rubric review of 30 briefs (clarity, usefulness, tone) by at least two reviewers (ideally sales-domain), and a regeneration/fallback rate. Cost tracking per brief.

### 10.4 Brief example (illustrative shape, not real data)
```json
{
  "isin": "INF…", "asof": "2026-11-05", "risk_level": "Elevated",
  "headline": "Silver ETFs trading rich to NAV; stress probability up vs last week",
  "what_changed": ["Premium +142 bps vs NAV (60-day median +18 bps)", "Turnover 3.1x 20-day average"],
  "why_it_matters": "Buyers today pay above fair value; premiums of this size have previously reverted within days.",
  "talking_points": ["…factual, no recommendation…"],
  "caveats": ["Daily NAV is struck at a different time than the exchange close.", "Model estimate, not advice."],
  "model_probs": {"P_tail_2": 0.34, "P_excursion": 0.12}
}
```

---

## 11. Serving: API, Backend, Frontend

### 11.1 Backend and API (FastAPI, versioned `/v1`)
| Endpoint | Purpose |
|---|---|
| `GET /v1/etfs` | Universe list with filters (tier, archetype, issuer, status) |
| `GET /v1/etfs/{isin}` | Static metadata, benchmark, creation unit, MMs, symbol history |
| `GET /v1/etfs/{isin}/series?from&to&fields=` | Price, NAV, premium, volume, benchmark, band state |
| `GET /v1/risk/board?asof=` | All ETFs: risk level, key probabilities, anomaly flag, sparkline |
| `GET /v1/forecasts/{isin}?asof=` | Quantiles, probabilities, reason codes, regime, model version |
| `GET /v1/forecasts/{isin}/history` | Past forecasts joined with outcomes |
| `GET /v1/events?isin&type&from&to` | Notices/events (reviewed) |
| `GET /v1/replay/{event_id}` | Event-study replay data (E1-E3) and counterfactual band table |
| `GET /v1/briefs/{isin}/latest`; `POST /v1/briefs/generate` (admin) | Briefs |
| `GET /v1/scorecard` | Forward-ledger calibration/Brier/alerts since launch, by regime |
| `GET /v1/models`, `GET /v1/health`, `GET /v1/data-quality` | Registry, health, DQ status |
| `POST /v1/band/simulate` | Run the band engine on a supplied path/base |
| `GET/POST /v1/alerts/subscriptions` | Alert preferences |
| `GET /v1/export/brief.pdf`, `/v1/export/board.csv` | Exports |
Auth: Firebase JWT or API key; roles `viewer`, `analyst`, `admin`; rate limiting; pagination; OpenAPI published; response times target <500 ms for board (precomputed).

**Forecast response (abridged):**
```json
{"isin":"INF769K01KG6","asof_date":"2026-11-04","target_date":"2026-11-05","regime":"R2",
 "premium_bps":{"current":88,"q05":-35,"q25":20,"q50":78,"q75":140,"q95":260},
 "probs":{"tail_E1":0.41,"tail_E2":0.17,"tail_E3":0.04,"excursion_X":0.09},
 "anomaly":{"score_pctile":98.1,"flag":true},
 "risk_level":"Elevated","reasons":[{"code":"TURNOVER_SURGE","text":"…","shap":0.21}],
 "degraded":false,"model_id":"A_lgbm_2026-10","ledger_hash":"…"}
```

### 11.2 Frontend (React + TypeScript)
**Pages**
1. **Risk Board:** heatmap/table of all ETFs grouped by tier/archetype; columns: premium (bps), risk level, P(tail), P(excursion), anomaly flag, 20-day sparkline; filters (issuer, own vs peers); "Mirae products" quick filter.
2. **ETF Detail:** (a) price vs NAV line chart with premium subplot; (b) **forecast fan chart** (quantile ribbons for next day, plus history of past forecasts vs actuals); (c) **band overlay** (R2 band edges from prior close); (d) probability gauges for tail and excursion; (e) anomaly timeline; (f) reason-code panel (SHAP summary in plain language); (g) peer comparison (same category across issuers); (h) events timeline (notices, FoF halts, regime markers).
3. **Sales Brief:** auto-generated daily brief per ETF/category with talking points, charts, export to PDF/email; edit-before-send; compliance disclaimer slot.
4. **Event Replay:** step-through playback of E1-E3 (date slider; what the system showed that day); counterfactual band table for E2.
5. **Product & Regime:** international ETF structural-premium monitor (premium level, change, FoF status, headroom state), new-regime tracker (band flexes observed, pre-open outcomes), liquidity scorecards for thin ETFs.
6. **Scorecard (Model Health):** forward-ledger calibration curves, Brier vs baseline, alerts and hits, regime-split metrics, drift indicators.
7. **Admin:** data-quality status, ingestion run history, review queue for G1 extractions, mapping verification, alert rules.
**UX rules:** no unexplained jargon (tooltips define premium, iNAV, band); every number shows its timestamp and "as-of" regime; degraded-data banners; colour-blind-safe palette; responsive layout (works on a laptop projector and phone); keyboard navigation; dark/light modes.

### 11.3 Alerting
Channels: email and Telegram (optional WhatsApp via approved provider later). Rules: level change to High/Critical, anomaly flag on a Mirae ETF, new reviewed event for a watched ETF, data degradation. De-duplication window, quiet hours, and one-tap "useful / not useful" feedback stored as `usefulness_label` (used to tune thresholds and as evidence of operational value).

---

## 12. Monitoring and MLOps

| Area | Mechanism |
|---|---|
| Pipeline health | Freshness SLAs per source; run success/latency dashboards; failure alerts; automatic `degraded` flags |
| Data drift | PSI/KS tests on feature distributions by group; regime-change detector (new rule dates + statistical break tests) |
| Model performance | Rolling Brier/pinball/coverage on realised outcomes (ledger join); decay alarms |
| Retraining | Scheduled monthly refresh (expanding window); triggered retrain on drift/decay or regime change (e.g., 1 Apr 2027); champion-challenger with shadow predictions for ≥ N days before promotion |
| Registry | MLflow: params, data snapshot id, metrics, SHAP artefacts; promotion requires passing gates |
| Reproducibility | Dataset snapshots + config hash; one-command rerun of any backtest |
| Observability | Structured logging, request tracing IDs, uptime check; optional Grafana |
| Governance | Model cards per task (intended use, data, limits, known failure modes, proxy disclaimers), versioned in repo |
| Cost | LLM spend per brief logged; caching of unchanged inputs |

---

## 13. Deployment and Operations

- **Environments:** `local` (docker-compose), `staging`, `prod`. Config via environment variables; secrets in a secret manager (never in the repo).
- **Containers:** `ingest-worker`, `model-worker`, `api`, `web`, `postgres`, `mlflow`. One small VM (or Cloud Run + scheduler) suffices; ~hundreds of ETFs × daily bars is tiny.
- **CI/CD (GitHub Actions):** lint (`ruff`), type-check (`mypy`), unit/property tests, data-contract tests on sample files, backtest smoke test on a frozen mini-snapshot, build images, deploy on tag; nightly full pipeline test on staging.
- **Backups:** nightly Postgres dump; raw zone mirrored to object storage; ledger hashes committed to a git repo daily.
- **Security:** no personal data stored; API auth; least-privilege DB roles; dependency scanning; rate-limited scrapers with identifying user-agent; respect robots/ToS (OQ-09).
- **Disaster/failure behaviour:** if a source is late, forecasts publish with `degraded` flags and last-known values; no silent substitution.
- **Cost envelope [A]:** near-zero for hosting on free tiers; LLM API cost small (briefs only for changed ETFs).
- **In-AMC deployment path (post-internship):** swap data adapters for licensed NSE/BSE feeds; deploy behind the AMC's SSO; replace the disclaimer with approved language.

---

## 14. Testing Strategy

| Layer | Tests |
|---|---|
| Ingestion | Golden-file tests for each bhavcopy schema (pre- and post-8 Jul 2024), AMFI file variants; retry/backoff; checksum idempotency |
| Security master | Mapping property tests (one ISIN ↔ one scheme code); symbol-history time-travel tests |
| Calendar | T-1 resolution across holidays, weekend special sessions (1 Feb 2026), Muhurat |
| Features | Unit tests per feature; PIT "future-poisoning" tests; rebuild equality |
| Labels | Isolated package; tests with synthetic paths; assertion that feature code cannot import it |
| Models | Reproducibility with fixed seeds; monotonic-constraint tests; calibration regression tests on frozen data |
| Band engine | Test vectors in §8.5 + property tests (flex never decreases a band; no sliding; equity cap) |
| Backtest | Purge/embargo correctness tests; leakage canary (a feature equal to the future label must be rejected by the leak detector) |
| GenAI | Faithfulness validator tests with adversarial outputs; banned-phrase tests; schema tests; extraction accuracy on labelled set |
| API | Contract tests from OpenAPI; auth and role tests; load smoke |
| Frontend | Component tests; visual regression on key charts; e2e (Playwright) for Board → Detail → Replay |

---

## 15. Repository Layout and Standards
```
elews/
  pyproject.toml  Makefile  docker-compose.yml  .github/workflows/
  docs/ (model_cards/, pre_registration.md, data_dictionary.md, runbook.md)
  src/elews/
    ingest/ security_master/ calendar/ quality/ features/ labels/ models/
    band_engine/ backtest/ ledger/ genai/ api/ monitor/ common/
  web/ (React app)
  tests/ (unit/, property/, golden/, e2e/)
  notebooks/ (exploration only; nothing imported from here)
```
Standards: typed Python, docstrings with units (bps vs %), explicit time zones (`Asia/Kolkata`), no notebooks in production paths, every dataset has a data-dictionary entry.

---

## 16. Delivery Plan (phases, dependencies, exit criteria)

| Phase | Content | Depends on | Exit criteria |
|---|---|---|---|
| **P0 Discovery and verification** | Close OQ-01…OQ-05, OQ-11, OQ-18, OQ-19; sample-file inspection (bhavcopy, AMFI); read circulars NSE/CMTR/76101, 76041, 74969; start **forward collectors** (pre-open, iNAV, notices); stakeholder interview plan; freeze thresholds/definitions; write pre-registration | none | Verification log signed; sample ingestion works for 3 ETFs; forward collectors running |
| **P1 Data platform** | Security master + mapping sign-off; backfills; contracts; calendar/regime tables; raw/curated zones; scheduler | P0 | Full universe loaded; DQ dashboard green; mapping verified per ETF; rebuild from raw reproducible |
| **P2 Features, labels, baselines** | Feature groups F1-F8; PIT tests; label module; baselines B0-B6; first EDA of premium distributions and event counts | P1 | Baseline metrics produced; event counts per task known; thresholds ratified |
| **P3 Core models and backtests** | LightGBM A-D; calibration; anomaly; walk-forward + LOEO; ablations; (stretch) TFT comparison | P2 | Backtest report with CIs; H1-H3, H6-H7 evaluated |
| **P4 Band engine and counterfactuals** | Rules library, test vectors, simulator, historical counterfactual replay for E2; Task C R2 monitoring | P2 | Engine passes vectors; E2 counterfactual table generated |
| **P5 Serving MVP** | API; React Board, Detail, Replay, Scorecard; ledger live; first end-to-end daily run | P3, P4 | Unattended daily run for 10 consecutive trading days; E1/E2 replay pages complete |
| **P6 GenAI and alerts** | G1-G3, validators, review queue; alerting; brief PDF export; usefulness feedback | P5 | Extraction/faithfulness metrics reported; briefs generated daily |
| **P7 Forward run and pitch pack** | ≥ 4-8 weeks of live ledger; scorecard; one-page summary; demo script; stakeholder feedback loop | P5 (P6 recommended) | Live scorecard with honest results; demo rehearsed |
| **P8 Extensions (T3)** | Attention/news module + ablation; intraday upgrade using forward snapshots; international module deepening; distribution-intelligence prototype | P7 | Each extension accepted only if it passes its gate |
**Pitch-ready minimum:** P0-P5 plus the E1/E2 replays and an early forward ledger (a working system, not a notebook). **Schedule risk:** the internship timeline is unknown (OQ-13); P0 forward collectors should start immediately because they cannot be backfilled.

### 16.1 Stakeholder validation plan (for the Mirae pitch)
Interview guide (ask, do not assume): How do sales teams currently learn that an ETF is at a premium? Which events triggered action in Oct 2025 and Feb 2026 and what information was missing? What would an ideal morning brief contain? How do FoF gating and market-maker decisions get made and what lead time matters? Which ETFs/categories matter most (international premiums? commodity? thin launches)? What compliance wording applies to distributor communications? What data feeds does Mirae already license? Record answers; update personas and thresholds.

---

## 17. Deliverables, Success Criteria and Expected Outcomes

### 17.1 Deliverables
1. Reproducible ingestion pipeline and curated datasets with data dictionary and DQ report (per-ETF coverage table).
2. Point-in-time feature store (F1-F8) with tests.
3. Baselines B0-B6 and core models for Tasks A-E with model cards.
4. Band engine library with passing test vectors and counterfactual replay for E2.
5. Walk-forward and event-study backtest report (pre-registered; with CIs, ablations, event counts).
6. Live system: API, React dashboard (Board, Detail, Brief, Replay, Product & Regime, Scorecard, Admin), alerts, daily briefs.
7. Forward ledger and scorecard.
8. GenAI layer with validators and evaluation report.
9. Runbook, deployment scripts, pitch pack (replay one-pagers, demo script, limitations statement).

### 17.2 Success criteria
- **Technical:** H1-H6 evaluated and reported honestly; calibration within pre-set tolerances; controls stay quiet; pipeline runs unattended for ≥10 trading days with <1 unhandled failure.
- **Operational value:** at least one real stakeholder feedback loop completed; alert usefulness ratings captured; the Morning Brief readable by a non-technical sales user without narration.
- **Integrity:** every claim in the pitch traces to an artefact produced by the pipeline; R2 claims are dated and sized by available R2 days/events.

### 17.3 What the finished application looks like and accomplishes
Each trading morning a sales head opens the Risk Board: Mirae's gold, silver, international and thematic ETFs sit next to peers, each with a one-word risk level, a premium reading, a probability of a tail dislocation and of band stress, and an anomaly flag. Clicking a silver ETF shows price vs NAV, the forecast fan, the band edges derived from yesterday's close, why the model is worried (plain-language reasons) and what peers are doing. A brief tells the team what to say to distributors, with caveats. A replay of Oct 2025 and Feb 2026 shows what the system would have said at the time, and a scorecard shows how it is doing since launch. A product manager sees the international-ETF premium monitor and the new-regime tracker. Everything is time-stamped, versioned and auditable.

---

## 18. Risks, Limitations and Mitigations
| Risk | Impact | Mitigation |
|---|---|---|
| Few historical events → low statistical power | Overfitting, weak claims | Pooled panel, simple models, LOEO, event-level reporting, forward ledger, no inflated claims |
| NAV clock mismatch contaminates premium | Spurious premiums on volatile days | `clock_risk` flag, NAV-benchmark residual feature, subset analysis, forward iNAV capture |
| Regime breaks (1 Feb 2026, 7 Sep 2026, 1 Apr 2027) | Non-stationarity | Regime table, separate reporting, retrain triggers, versioned band engine |
| Counterfactual label validity (censoring, behavioural change) | Misleading Task C backtest | Caveats; R2-only claims after data accumulates; ledger |
| Data access/format changes (bhavcopy, AMFI) | Pipeline failure | Contracts, raw retention, fallbacks, alerts |
| ISIN/symbol mapping errors | Silent corruption | Quarantine, sign-off, tests |
| Licensing/ToS constraints | Legal exposure | Review (OQ-09), demo-scope use, licensed feeds for production |
| LLM hallucination in briefs | Misinformation/compliance risk | Closed-world inputs, validators, templates fallback, human review |
| Alert fatigue | Tool ignored | Alert budget, thresholds tuned on controls, feedback loop |
| Over-claiming | Credibility loss | Pre-registration, limitations statement, model cards |
| Scope creep | Delay | Tiering and phase gates |
| Unknown stakeholder needs | Misfit | Interview plan, iterative feedback |
| Single-developer capacity | Slippage | MVP cut (P0-P5), automation, minimal infra |

---

## 19. Assumptions and Open Questions Carried Forward (to be closed in the stated phase)
| ID | Item | Phase |
|---|---|---|
| OQ-01 | Applicability of new bands to international ETFs; symmetric downside trigger | P0 |
| OQ-02 | NSE pre-open timeline/data for gold/silver ETFs; archive availability | P0 |
| OQ-03 | `ClsPric` = last-30-min VWAP? effect of closing auction | P0 |
| OQ-04 | NAV valuation time/method for commodity ETFs | P0 |
| OQ-05/06 | iNAV frequency by category; historical iNAV vendor options | P0 |
| OQ-07 | Any daily units-outstanding/AUM proxy | P0-P2 |
| OQ-08 | Overseas-limit headroom publication | P0-P2 |
| OQ-09 | Data licensing/ToS | P0 |
| OQ-10 | Special sessions/halts; NSE treatment in R1 | P0-P1 |
| OQ-11 | Domestic Price of Gold/Silver index methodology | P0 |
| OQ-12 | Duty/tax inputs for import-parity features | P2 |
| OQ-13 | Stakeholder needs; internship timeline | P0, ongoing |
| OQ-14 | Early R2 behaviour (flex frequency, auction outcomes) | P4-P7 |
| OQ-17 | Master-circular clause mapping | P0 |
| OQ-18/19/20 | Conflicting fund facts; corporate actions; AMFI endpoint stability | P0-P1 |
| A-M1 | Boosted trees will beat sequence models on this panel | P3 (empirical) |
| A-M2 | Pooled models beat per-archetype | P3 |
| A-M3 | Daily data carry early signal of building pressure | P3 (core question) |
| A-M4 | Alert budget of ≤1 High per ETF-month is operationally acceptable | P2/P7 with stakeholders |

---

## 20. Glossary
- **NAV / iNAV:** official end-of-day net asset value per unit / intraday indicative estimate.
- **Premium/discount:** ETF price relative to NAV (positive = premium); expressed in bps (1 bp = 0.01%).
- **Market maker (MM):** exchange member appointed by the AMC to quote two-way prices and create/redeem units directly with the AMC.
- **Creation unit:** the minimum block (units) in which MMs/large investors transact directly with the AMC.
- **Base price:** reference price for the day's price bands; from 7 Sep 2026 the T-1 last-30-minute VWAP.
- **Dynamic price band / cooling-off / flex:** band that starts narrow (±10% equity/debt; ±6% commodity), pauses for 15 minutes (5 in the last 30 minutes) when trades reach 9.90%/5.90% from base, then widens (+5%/+3% of base) on the side hit.
- **Pre-open call auction:** order-collection session before 09:15 that discovers one equilibrium opening price; mandatory for gold/silver ETFs from 7 Sep 2026.
- **FoF:** fund-of-funds that invests in an ETF and is bought at NAV via the AMC.
- **Overseas limit:** SEBI/RBI-linked ceilings on mutual-fund overseas investment that can close creation for international ETFs.
- **Pinball loss:** quantile-regression loss. **CQR:** conformalized quantile regression. **PIT:** point-in-time (information availability) or probability integral transform (context-dependent). **Brier score:** mean squared error of probabilistic classification. **ECE:** expected calibration error. **BOCPD:** Bayesian online change-point detection.
- **Archetypes A-E:** supply squeeze, demand surge, crash/band lock-up, structural cap-driven premium, thin-liquidity drift.
- **R0-R3:** regulatory regimes defined in §3.2.

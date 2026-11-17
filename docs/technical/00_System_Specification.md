# ETF Arbitrage-Stress Early Warning System
## Technical Document 00: System Specification (canonical definitions, architecture, data contracts, conventions)

| Field | Value |
|---|---|
| Document ID | TS-00 |
| Version | 1.0 |
| As-of | 17 November 2026 |
| Status | Active. **Canonical**: where a phase document and this document disagree on a definition, this document wins until a logged decision changes it. |
| Read with | [Research Document](../research/ETF_Stress_Research_Document.md) (why), [phase documents](phases/) (what to build, in order), [process](../process/Documentation_Logging_and_Phase_Gates.md) (how progress is recorded and verified) |

---

## 1. Purpose and precedence

This document fixes everything that more than one phase depends on: the system's architecture, the exact mathematical definitions of premium, dislocation, episode and target, the parameters and their defaults, the data model and point-in-time rules, the repository layout, the tooling and the coding conventions.

**Precedence (highest first):**

1. A logged decision in [`records/DECISIONS.md`](../../records/DECISIONS.md) that explicitly amends a section of this document.
2. The frozen pre-registration (`config/pre_registration.md`, created in P11) for anything it covers, once frozen.
3. This document.
4. The phase documents.
5. The Research Document (for facts and rationale, not for build rules).

An executing agent that finds a contradiction must not silently pick one: it records an issue in `records/ISSUES.md`, applies the higher-precedence rule, and notes it in the phase walkthrough.

---

## 2. System overview

### 2.1 Pipeline

```
 SOURCES                         STORAGE LAYERS                       ANALYTICS                          OUTPUTS
 ───────                         ──────────────                       ─────────                          ───────
 US prices (Tiingo/…)  ─┐
 US NAV+shares (issuers)┤        data/raw/      (immutable files,
 India bhavcopy (NSE)  ─┤  P04    checksummed, manifest-logged)
 India NAV (AMFI)      ─┼─ P05 ─►        │
 Metals/energy/FX/macro ┤  P06           ▼ P07
 Reference tables (hand)┘        data/curated/  (validated Parquet,
 Incident catalogue  ──── P02/P03   point-in-time: known_at)
                                         │
                                         ▼ P08
                                 Pricing layer: premium, Layer 1,
                                 total gap, no-arb band, lock class
                                         │
                       ┌─────────────────┴──────────────────┐
                       ▼ P09                                 ▼ P10
                 Labels (episodes, targets)          Features (stress signals,
                 [isolated module; may look           point-in-time only)
                  into the future]                          │
                       └──────────────┬──────────────────────┘
                                      ▼ P11
                       Evaluation harness, baselines, pre-registration
                                      ▼ P12
                       LightGBM models (full + transferable core), calibration
                                      ▼ P13
                       Root-cause tags + analogue finder
                                      ▼ P14 (US lockbox)   ▼ P15 (India transfer)
                       Out-of-sample results, event replays, business-value metrics
                                      ▼ P16
                       predictions.parquet ─► Daily ETF Stress Brief (HTML/MD) + Streamlit dashboard
                                      ▼ P17
                       Final validation, reproducibility, report, readiness
```

### 2.2 Components and their single responsibility

| Component | Python package path | Responsibility | Phase |
|---|---|---|---|
| Config | `esw.config` | Load `config/settings.yaml` + `.env`; typed settings object | P00 |
| Logging and run tracking | `esw.runlog` | Logger setup, run folders, registry, manifests | P00 |
| Reference data | `esw.reference` | Load/validate hand-built tables in `reference/` | P02, P03 |
| Ingestion | `esw.ingest.{us_prices, us_issuers, india_bhav, india_amfi, india_spot, market}` | Download → raw file + manifest → parse → staged Parquet | P04–P06 |
| Curation | `esw.curate` | Clean, reconcile, calendar-align, point-in-time stamping, quality checks | P07 |
| Pricing | `esw.pricing` | Premium, Layer 1, total gap, empirical band, lock classification, timing diagnostics | P08 |
| Labels | `esw.labels` | Dislocation days, episodes, targets, secondary labels. **Must not be imported by `esw.features`.** | P09 |
| Features | `esw.features` | Stress-signal features, point-in-time | P10 |
| Evaluation | `esw.evaluation` | Splits, metrics, bootstrap, baselines, event-level scoring | P11 |
| Models | `esw.models` | Training, tuning, calibration, prediction | P12 |
| Explain | `esw.explain` | SHAP, family aggregation, root-cause tags, analogue finder | P13 |
| Reporting | `esw.reporting` | Figures, tables, replays, business-value metrics, report assets | P14, P15, P17 |
| Brief and app | `esw.brief`, `app/streamlit_app.py` | Daily Stress Brief, dashboard | P16 |
| CLI | `esw.cli` | `python -m esw <command>` entry point for every stage | P00 onwards |

---

## 3. Repository layout

The code lives in this repository, next to the documentation. Paths are relative to the repository root.

```
Mirae/
├─ CLAUDE.md                        # operating instructions for Claude Code sessions (auto-loaded)
├─ README.md                        # human entry point
├─ pyproject.toml                   # package + tool config (created in P00)
├─ .env.example                     # names of secrets, no values (P00)
├─ .gitignore
├─ config/
│  ├─ settings.yaml                 # paths, parameters (defaults from §4.13), source settings
│  ├─ pre_registration.md           # created P11, frozen before P14
│  └─ model_configs/                # one YAML per model variant
├─ reference/                       # hand-built, versioned CSV tables (tracked in git)
│  ├─ instruments_us.csv  instruments_in.csv  symbol_history.csv
│  ├─ incidents.csv  operational_events.csv  capacity_us.csv
│  ├─ corporate_actions_manual.csv  duty_india.csv  band_regimes_india.csv
│  ├─ nav_clock.csv  series_catalogue.csv  source_registry.csv
│  └─ README.md                     # column dictionary for every table
├─ src/esw/                         # the package (see §2.2)
├─ app/streamlit_app.py
├─ tests/
│  ├─ unit/  integration/  acceptance/   # acceptance/test_pXX_acceptance.py per phase
│  └─ fixtures/                     # small golden files (tracked)
├─ data/                            # gitignored except manifests
│  ├─ raw/<source>/<yyyy>/...       # immutable downloads
│  ├─ manual_drop/<source>/         # files the user downloads by hand (MI guides)
│  ├─ staged/<source>/*.parquet     # parsed, source-shaped
│  ├─ curated/*.parquet             # validated, canonical (§6)
│  ├─ derived/{pricing,labels,features}/*.parquet
│  └─ manifests/                    # TRACKED: ingest_log.jsonl, file manifests, coverage reports
├─ runs/                            # one folder per experiment; registry.csv TRACKED; heavy files gitignored
├─ models/production/               # production model files (gitignored; hashes recorded in run folders)
├─ outputs/                         # predictions, briefs, forward log (gitignored except outputs/samples/)
├─ reports/                         # figures and final report (tracked)
├─ logs/                            # runtime logs (gitignored)
├─ docs/                            # this documentation set (docs/operations/ is added in P16–P17)
├─ records/                         # status, logs, walkthroughs, acceptance reports (tracked)
└─ archive/                         # superseded documents
```

**Naming conventions.** Files: `snake_case`. Instrument identifier: `instrument_id` = `"{market}:{primary_key}"`, where `market ∈ {US, IN}` and `primary_key` is the ISIN for India and the US ticker at inception for the US (US ISINs are used as attributes; US tickers rarely change for this universe, and changes go to `symbol_history.csv`). Example: `US:GLD`, `IN:INF769K01KG6`.

---

## 4. Canonical definitions

All quantities are per instrument `i` and trading day `t` on the instrument's **listing market calendar**. Basis points (bps) are used for gaps: 1 bp = 0.01%.

### 4.1 Calendars and decision time

- `cal(m)`: the trading calendar of market `m`. US: NYSE calendar (`exchange_calendars` code `XNYS`), cross-checked against days with price data. India: NSE trading days **derived from bhavcopy file presence**, cross-checked against NSE holiday lists; special sessions (e.g., Sunday 1 Feb 2026, Muhurat sessions) are trading days with `session_type = special`.
- `t+k`: the k-th trading day after `t` on `cal(m)`.
- **Decision time** `τ(t)`: the moment the forecast for the window `[t+1, t+H]` is made. US: **08:00 America/New_York on t+1**. India: **08:00 Asia/Kolkata on t+1**. Every input used by a feature for day `t` must have `known_at ≤ τ(t)`.

### 4.2 Prices and NAV

- `P(i,t)`: official closing price, **unadjusted** for dividends; adjusted only for splits/consolidations so that it is on the same unit basis as `NAV(i,t)` (§6.5). US: primary-listing official close. India: NSE close (assumed last-30-minute VWAP, OQ-02); BSE fallback only where NSE is missing and flagged.
- `NAV(i,t)`: official NAV per unit for date `t` as published by the issuer (US) or AMFI (India), on the same split basis.
- `O, H, L, V, TV, N`: open, high, low, volume (units), traded value (currency), number of trades (India only).
- `SO(i,t)`: shares/units outstanding (US issuers; India unavailable).

### 4.3 Premium (Layer 2)

```
prem(i,t) = 10,000 × ( P(i,t) / NAV(i,t) − 1 )        [bps; positive = premium]
```

Rows with missing `P` or `NAV`, zero/negative values, or `lock_class ∈ {confirmed_locked}` (§4.11) are kept but flagged; they are excluded from label construction as described in §4.6.

### 4.4 Layer 1 and total gap (commodity ETFs; India primarily)

```
parity(t)   = G(t) × FX(t) × (1 + duty(t))                 # import parity in local currency per unit of metal
LP(t)       = 10,000 × ( D(t) / parity(t) − 1 )            # Layer 1, bps
LP_NAV(i,t) = 0                         if NAV basis(i,t) = import_parity     (India gold/silver before 2026-04-01)
            = LP(t)                     if NAV basis(i,t) = domestic_spot      (India gold/silver from 2026-04-01)
TG(i,t)     = 10,000 × ( (1 + prem/1e4) × (1 + LP_NAV/1e4) − 1 )   # total investor gap vs global parity, bps
```

`G`: global metal price (USD per unit; source per §6.4); `FX`: USD/INR; `duty`: total effective import duty from `reference/duty_india.csv`; `D`: domestic spot. `LP` is computed only for dates where all inputs exist and the duty row is `verified = true`; otherwise it is null with a reason code. The NAV basis per instrument and date comes from `reference/nav_clock.csv`.

### 4.5 Robust baseline and scale

For each instrument, using only **eligible history** (rows with valid `prem`, not `confirmed_locked`, not inside a frozen episode window as defined in §4.6):

```
b(i,t)  = median of prem over the last BASE_WIN eligible days strictly before t     (requires ≥ BASE_MIN obs)
s(i,t)  = max( SCALE_FLOOR_BPS , 1.4826 × MAD of prem over the last SCALE_WIN eligible days strictly before t )
                                                                                    (requires ≥ SCALE_MIN obs)
dev(i,t) = prem(i,t) − b(i,t)          z(i,t) = dev(i,t) / s(i,t)
```

The baseline and scale use data strictly before `t`, so `z(i,t)` is a legitimate feature at decision time `τ(t)` (the label module computes the same quantities independently).

### 4.6 Dislocation day, episode, structural absorption

```
thr(i,t) = max( ABS_FLOOR_BPS , K_MULT × s(i,t) )
DD(i,t)  = 1  if |dev(i,t)| ≥ thr(i,t)  and the row is valid and not confirmed_locked
         = 0  otherwise
```

- **Episode:** a maximal run of `DD = 1` days in which any gap of `DD = 0` days is at most `GAP_BRIDGE` long, containing at least `PERSIST_MIN` days with `DD = 1`, all with the same sign of `dev`. A sign flip ends the run.
- **Onset** `on(e)`: first `DD = 1` day of episode `e`. **End** `end(e)`: last `DD = 1` day. **Direction**: `PREMIUM` or `DISCOUNT`. **Peak**: max `|dev|` within the episode.
- **Baseline freeze:** from an episode's onset, `b` and `s` are frozen at their values on `on(e)` (computed from pre-onset data) for up to `FREEZE_MAX` trading days. If the episode is still running after `FREEZE_MAX` days, the episode is marked `structural = true`, the freeze is released and the baseline resumes rolling over all valid rows (the persistent level is absorbed as the new normal). An absorbed episode ends when `DD` returns to 0 under the rolling baseline.
- `in_episode(i,t) = 1` for `on(e) ≤ t ≤ end(e)` for any episode `e` (known only in hindsight; used only by labels and evaluation).
- **Timing-suspect flag** (robustness, not used for training): see §4.10.

### 4.7 Primary target

```
eligible(i,t) = 1  if  s(i,t) is defined (≥ SCALE_MIN obs)
                   and t is not inside any episode (on(e) ≤ t ≤ end(e))
                   and t is not within COOLDOWN trading days after any episode end
                   and P(i,t), NAV(i,t) valid
y(i,t)        = 1  if eligible and some episode has onset in [t+1, t+H]   (H = HORIZON)
              = 0  if eligible and no onset in [t+1, t+H] and the window [t+1, t+H+PERSIST_MIN+GAP_BRIDGE] is fully observed
              = null otherwise (not used for training or evaluation)
```

Horizon variants `y_h1`, `y_h3` (H = 1, 3) are produced for sensitivity reporting only. The model is trained on `y` (H = 5).

**Label lookahead and embargo.** A label at `t` can depend on data up to `t + H + PERSIST_MIN + GAP_BRIDGE`. The embargo between training and test periods is therefore `EMBARGO = H + PERSIST_MIN + GAP_BRIDGE + 1 = 10` trading days (§9).

### 4.8 Secondary labels (evaluation only)

| Label | Definition | Market |
|---|---|---|
| `sec_trigger` | First day on which `|prem| > SEC_ABS_BPS` has held for more than `SEC_RUN − 1` consecutive trading days (i.e., the 8th consecutive day) | US and India |
| `sebi_trigger` | First day on which `prem < −SEBI_ABS_BPS` has held for `SEBI_RUN` consecutive trading days | India (also computed for the US as an analogue) |
| `noquote_trigger` | Third consecutive day with no trades (bhavcopy volume = 0 or missing while listed) | India |
| `op_event` | Effective date of an operational event (creation suspension, subscription halt for FoFs or ETFs, trading halt, capacity exhaustion) from `reference/operational_events.csv` | Both |

For each, the evaluation reports whether a WATCH/HIGH alert was issued in the `LEAD_WINDOW` trading days before the trigger and the lead time.

### 4.9 Empirical no-arbitrage band

Per instrument and day, from eligible calm history (rows with `in_episode = 0` known up to `t−1`, last `SCALE_WIN` days):

```
band_lo(i,t), band_hi(i,t) = 2.5th and 97.5th percentiles of prem
band_width(i,t)            = band_hi − band_lo
excess(i,t)                = prem − band_hi  if prem > band_hi ;  prem − band_lo  if prem < band_lo ;  0 otherwise
```

The bottom-up arbitrage cost (spread estimate + documented creation fee) is computed in P08 only as a cross-check.

### 4.10 Timing diagnostics

- `ret_px(i,t) = P(i,t)/P(i,t−1) − 1`; `ret_nav(i,t) = NAV(i,t)/NAV(i,t−1) − 1`; `div(i,t) = ret_px − ret_nav` (bps).
- **Forward-NAV gap** (label module only, uses future data): `fprem(i,t) = 10,000 × (P(i,t)/NAV(i,t+1) − 1)`.
- An episode is `timing_suspect = true` if, for at least half of its `DD` days, `|fprem − b| < thr` (the dislocation disappears when compared with the next NAV). Timing-suspect episodes stay in the primary label (pre-registered) and are reported separately; the sensitivity analysis also re-runs evaluation with them removed.

### 4.11 Lock classification (India)

`lock_class(i,t) ∈ {confirmed_locked, near_band, unconstrained, unknown}`, computed in P08 from `reference/band_regimes_india.csv`:

- Determine the band reference price and band percentages in force for that instrument, exchange and date. If the regime row is missing or unverified: `unknown`.
- `confirmed_locked`: close within 0.25% of the band limit **and** (high = low = close, or the exchange's circuit indicator if available).
- `near_band`: close within 1% of the band limit, not confirmed.
- `unconstrained`: otherwise.

US rows are `unconstrained` (no daily bands). Headline metrics exclude `confirmed_locked` rows; `near_band` and `unknown` are included and reported separately.

### 4.12 Risk levels (output mapping)

| Level | Rule |
|---|---|
| `INSUFFICIENT_DATA` | Instrument not eligible for scoring (history too short, missing data) |
| `ACTIVE` | Instrument currently has `DD = 1` for at least `PERSIST_MIN` of the last `PERSIST_MIN + GAP_BRIDGE` days (a real-time, backward-looking version of "in episode"; no future data) |
| `HIGH` | `p ≥ THR_HIGH` |
| `WATCH` | `THR_WATCH ≤ p < THR_HIGH` |
| `NORMAL` | otherwise |

`p` is the calibrated probability from the production model. `THR_WATCH` and `THR_HIGH` are chosen in P12 on development-period out-of-fold predictions to satisfy the alert budget (§4.13), recorded in the pre-registration, and never changed after the lockbox is opened.

Independently of the level, every output also shows the **absolute premium** with a descriptive band: `|prem| < 100 bps` "close to NAV", `100–300` "noticeable", `300–1,000` "large", `> 1,000` "extreme" (descriptive only; not a model output).

### 4.13 Parameters and defaults

These defaults go into `config/settings.yaml` in P00. Values marked **frozen at P11** cannot change after the pre-registration is signed (MI-11 requires sign-off).

| Parameter | Default | Meaning | Frozen at P11 |
|---|---|---|---|
| `ABS_FLOOR_BPS` | 200 | Absolute floor of the dislocation threshold | Yes |
| `K_MULT` | 3.0 | Multiple of robust scale | Yes |
| `PERSIST_MIN` | 3 | Minimum `DD` days in an episode | Yes |
| `GAP_BRIDGE` | 1 | Max consecutive non-DD days bridged inside an episode | Yes |
| `HORIZON` | 5 | Primary forecast horizon (trading days) | Yes |
| `BASE_WIN`, `BASE_MIN` | 60, 40 | Baseline window and minimum observations | Yes |
| `SCALE_WIN`, `SCALE_MIN` | 250, 120 | Scale window and minimum observations | Yes |
| `SCALE_FLOOR_BPS` | 5 | Floor on robust scale (avoids division by ~0) | Yes |
| `FREEZE_MAX` | 60 | Max baseline-freeze length before structural absorption | Yes |
| `COOLDOWN` | 5 | Days after an episode end that are ineligible | Yes |
| `EMBARGO` | 10 | Trading-day embargo between train and test | Yes |
| `SEC_ABS_BPS`, `SEC_RUN` | 200, 8 | SEC-style secondary label | Yes |
| `SEBI_ABS_BPS`, `SEBI_RUN` | 100, 7 | SEBI-style secondary label | Yes |
| `LEAD_WINDOW` | 5 | Window for counting an alert as a warning of a trigger/onset | Yes |
| `DEV_END` | 2019-12-31 | Last date of the development period (US) | Yes |
| `LOCKBOX_START` | 2020-01-01 | First date of the US lockbox | Yes |
| `DATA_CUTOFF` | set in P07 (latest complete date) | Last date in the frozen evaluation dataset | Yes |
| `ALERT_BUDGET_HIGH` | ≤ 1 HIGH alert per eligible ETF-quarter outside episodes (dev OOF) | Constraint for `THR_HIGH` | Yes |
| `ALERT_BUDGET_WATCH` | ≤ 1 WATCH-or-higher alert per eligible ETF-month outside episodes | Constraint for `THR_WATCH` | Yes |
| `THR_WATCH`, `THR_HIGH` | set in P12 | Probability thresholds | Yes (set before lockbox) |
| `SEED` | 20261117 | Global random seed | No |
| `BOOT_BLOCK` | calendar month | Block for bootstrap resampling | Yes |
| `BOOT_N` | 2,000 | Bootstrap replicates | Yes |

**Sensitivity grid (P14):** `ABS_FLOOR_BPS ∈ {100, 200, 300}`, `K_MULT ∈ {2.5, 3, 4}`, `PERSIST_MIN ∈ {2, 3, 5}`, `HORIZON ∈ {1, 3, 5}`.

### 4.14 Mechanism families and root-cause tags

| Family code | Tag shown to users | Feature families (P10) |
|---|---|---|
| `GAP` | "Gap building" | F1 gap state & persistence |
| `CRE` | `CREATION_CONSTRAINT` | F2 creation/flow, F3 capacity |
| `STL` | `STALE_NAV` | F5 NAV staleness & timing |
| `UND` | `UNDERLYING_SQUEEZE` | F6 underlying stress, F6b Layer 1 |
| `LIQ` | `LIQUIDITY_DRAIN` | F4 liquidity |
| `DEM` | `DEMAND_SURGE` | F7 demand pressure |
| `MKT` | `MARKET_WIDE_STRESS` | F8 market-wide |
| `CAL` | (context only, never the headline tag) | F9 calendar |
| `CTX` | (never a tag) | F10 static/context |

The rule for choosing the tag from SHAP values is defined in P13.

---

## 5. Universe

### 5.1 Asset groups

| Group code | Description | Market | Role |
|---|---|---|---|
| `US_COMM_PHYS` | Physically backed precious-metal trusts | US | Core |
| `US_COMM_FUT` | Futures-based commodity funds | US | Core |
| `US_BOND` | Corporate, high-yield, municipal, EM, loan ETFs | US | Contrast (stale NAV) |
| `US_INTL` | Single-country and regional international equity ETFs | US | Contrast (closures, sanctions) |
| `US_CTRL` | Large domestic equity ETFs | US | Control |
| `IN_GOLD`, `IN_SILVER` | Indian gold and silver ETFs | India | Transfer test core |
| `IN_INTL` | Indian ETFs holding overseas securities | India | Transfer test (structural cap premiums) |
| `IN_DEBT` | Indian debt ETFs excluding overnight/liquid | India | Transfer test (optional) |
| `IN_CTRL` | Large Indian equity ETFs | India | Control |

### 5.2 Candidate US universe (final list decided in P01–P02 from data availability)

| Group | Candidates (ticker, issuer) |
|---|---|
| `US_COMM_PHYS` | GLD (SPDR), IAU (iShares), SLV (iShares), SIVR, PPLT, PALL (abrdn), GLDM (SPDR, short history) |
| `US_COMM_FUT` | USO, UNG, BNO, UGA, USL, UNL, CPER, USCI (USCF); DBC, DBA, DBO (Invesco); GSG (iShares); CORN, WEAT, SOYB (Teucrium) |
| `US_BOND` | LQD, HYG, MUB, EMB, AGG, TLT (iShares); JNK (SPDR); BKLN (Invesco); BND (Vanguard) |
| `US_INTL` | EWJ, EWH, EWZ, EWW, FXI, EEM, INDA, TUR, ERUS (iShares); EGPT, RSX (VanEck); GREK (Global X); ASHR (Xtrackers) |
| `US_CTRL` | SPY, DIA (SPDR UITs), IVV, IWM (iShares), QQQ (Invesco), VOO (Vanguard) |

**Inclusion rule:** an ETF is included if (a) daily NAV and unadjusted price can be obtained for at least 500 trading days, (b) identifiers reconcile, and (c) splits reconcile (P07). Shares outstanding is desirable, not required (missing-aware). Excluded candidates are listed with reasons in `reference/instruments_us.csv`.

### 5.3 Candidate Indian universe

All listed gold ETFs and silver ETFs with ≥ 250 trading days of price and NAV; international ETFs (including Mirae `MAFANG`, S&P 500 Top 50, Hang Seng TECH; Motilal `MON100`; Nippon Hang Seng BeES; others found in the AMFI scheme master); controls (e.g., `NIFTYBEES`, `SETFNIF50`, `BANKBEES`, `JUNIORBEES`, a Sensex ETF); optional debt ETFs (Bharat Bond series, gilt ETFs). Overnight and liquid ETFs are excluded. Instruments are keyed by ISIN; Mirae products carry `issuer = Mirae Asset` and are highlighted in outputs.

---

## 6. Data architecture and contracts

### 6.1 Layers

| Layer | Location | Mutability | Format | Created by |
|---|---|---|---|---|
| Raw | `data/raw/<source>/…` | **Immutable** (never edited or overwritten; re-downloads create new files) | As downloaded | Ingestion |
| Manual drop | `data/manual_drop/<source>/…` | Written only by the user | As downloaded | User (MI guides) |
| Staged | `data/staged/<source>/*.parquet` | Rebuildable | Parquet, source-shaped, typed | Parsers |
| Curated | `data/curated/*.parquet` | Rebuildable from raw + reference | Parquet, canonical schemas below | P07 |
| Derived | `data/derived/{pricing,labels,features}/` | Rebuildable | Parquet | P08–P10 |
| Reference | `reference/*.csv` | Hand-edited, version-controlled, every row sourced | CSV (UTF-8) | P02, P03 |

**Rebuild rule:** deleting `data/staged`, `data/curated` and `data/derived` and running `python -m esw rebuild --all` must recreate them byte-for-byte equivalent (same row counts and content hashes), given the same raw and reference files (P07 and P17 acceptance).

### 6.2 Manifests and ingestion log

Every downloaded or dropped file gets one line in `data/manifests/ingest_log.jsonl`:

```json
{"ts_utc": "2026-11-20T10:31:02Z", "source": "us_issuer_ishares", "instrument_id": "US:SLV",
 "url": "https://…", "path": "data/raw/us_issuer_ishares/2026/SLV_20261120.xlsx",
 "sha256": "…", "bytes": 182733, "http_status": 200, "status": "ok|failed|skipped_cached|manual",
 "rows_parsed": 5000, "date_min": "2006-04-28", "date_max": "2026-11-19", "error": null, "run_id": "…"}
```

### 6.3 Curated table schemas

All tables carry `source` (string), `ingested_at` (UTC timestamp) and, where relevant, `known_at` (UTC timestamp; §7). Primary keys are unique (enforced by `pandera` schemas in `esw.curate.schemas`).

| Table | Primary key | Columns (beyond source/ingested_at) |
|---|---|---|
| `instrument` | `instrument_id` | `market, ticker, isin, name, issuer, group, subgroup, underlying, legal_form, nav_basis_default, listing_date, delisting_date, currency, is_mirae, rule_6c11, include, exclude_reason` |
| `symbol_history` | `instrument_id, exchange, valid_from` | `symbol, valid_to` |
| `calendar` | `market, date` | `is_trading, session_type ∈ {regular, special, half}` |
| `px_daily` | `instrument_id, date` | `open, high, low, close, volume, traded_value, n_trades, split_factor_applied, price_source, known_at` |
| `nav_daily` | `instrument_id, date` | `nav, shares_out, total_net_assets, nav_source, known_at, split_factor_applied` |
| `issuer_premium` (optional) | `instrument_id, date` | `issuer_prem_bps, issuer_mid_price` |
| `series_daily` | `series_id, date` | `value, unit, known_at` (all market/underlying/macro/FX series; catalogue in `reference/series_catalogue.csv`) |
| `corporate_action` | `instrument_id, ex_date, type` | `ratio, applies_to ∈ {price, nav, both}, verified, source_url` |
| `operational_event` | `event_id` | `instrument_id(s), type, effective_at, known_at, ended_at, ended_known_at, source_url, grade, notes` |
| `incident` | `incident_id` | `name, market, instruments, mechanisms, approx_onset, peak_date, approx_end, magnitude_text, near_miss, grade, sources` |
| `capacity` | `instrument_id, as_of` | `metric, value, unit, known_at, source_url` |
| `duty` | `metal, effective_from` | `effective_to, bcd_pct, aidc_pct, other_pct, total_pct, verified, source_url` |
| `band_regime` | `market, exchange, group, effective_from` | `effective_to, base_rule, band_init_pct, flex_step_pct, flex_max, verified, source_url` |
| `nav_clock` | `instrument_id, effective_from` | `nav_basis ∈ {us_close_16et, lbma_pm, lbma_silver_noon, futures_settle, foreign_close, evaluated_bond, in_import_parity, in_domestic_spot, in_close}, effective_to, source` |
| `quality_flag` | `table, key, check_id` | `severity ∈ {info, warn, error}, detail, detected_at` |

### 6.4 Series catalogue (initial)

| `series_id` | Description | Source | Publication lag (trading days) |
|---|---|---|---|
| `gold_usd_fut` / `silver_usd_fut` | COMEX front-month continuous | yfinance/Stooq | 0 |
| `gold_usd_navimpl` | GLD NAV ÷ ounces per share (≈ LBMA PM) | Derived | 0 |
| `wti_c1..c4`, `hh_c1..c4` | NYMEX futures curve | EIA (to Apr 2024) + fallback | 1 |
| `vix` | CBOE VIX | FRED `VIXCLS` | 0 |
| `baa10y` | Baa – 10y Treasury spread | FRED `BAA10Y` | 1 |
| `ust10y` | 10y Treasury yield | FRED `DGS10` | 1 |
| `usd_broad` | Broad dollar index | FRED `DTWEXBGS` | 1 |
| `usdinr`, `usdrub`, `usdegp`, … | FX | FRED `DEXINUS` etc.; RBI/FBIL reference rate | 1 |
| `india_vix` | India VIX | NSE | 0 |
| `in_gold_spot`, `in_silver_spot` | Domestic spot | MCX/IBJA (P05) | 0 |

### 6.5 Split and unit consistency

`P` and `NAV` must be on the same unit basis for every row. P07 detects split dates from (a) `corporate_action` rows, (b) price ratio jumps ≈ integer or 1/integer with no matching NAV jump, (c) NAV jumps with no matching price jump. Any detected but unexplained jump becomes a `quality_flag` with severity `error` and blocks the instrument until reconciled (logged in the walkthrough).

---

## 7. Point-in-time rules

| Data | `known_at` rule |
|---|---|
| US close/OHLCV for date t | t 16:15 America/New_York |
| US NAV, shares outstanding for date t | t 20:00 America/New_York (conservative; issuers publish in the evening). If an issuer is known to publish next morning, `t+1 07:00` |
| India bhavcopy for date t | t 18:00 Asia/Kolkata |
| AMFI NAV for date t | t 23:30 Asia/Kolkata |
| AMFI monthly AUM | Actual publication date (if unknown: the 10th calendar day of the following month, 18:00 IST) |
| FRED and other series | date t + publication lag (series catalogue), 18:00 local of the source |
| Scheduled calendars (holidays, foreign closures announced in advance) | Treated as known at all times **only** for scheduled holidays in the official calendar; unscheduled closures use their event `known_at` |
| Operational events, capacity rows, corporate actions | Their `known_at` (announcement/publication time), never `effective_at` |
| Reference metadata (inception dates, groups) | Known at all times |

**Leakage controls (all mandatory):**

1. Feature code receives only data with `known_at ≤ τ(t)` through one accessor (`esw.features.pit.as_of(table, decision_time)`); direct reads of curated tables from feature code are a test failure.
2. `esw.features` must not import `esw.labels` (import-guard test).
3. **Future-injection test:** perturb every input row with `known_at > τ(t)` for a sample of `(i,t)`; features for those `(i,t)` must not change.
4. **Leaky-canary test:** a feature equal to the label must be caught by the evaluation harness's leakage detector (an implausibly high single-feature PR-AUC triggers an error).
5. Hyper-parameters and thresholds are chosen using development-period data only; the lockbox is opened once (MI-11).

---

## 8. Modelling architecture (summary; details in P11–P13)

| Item | Specification |
|---|---|
| Unit of prediction | `(instrument_id, t)` eligible rows |
| Target | `y` (onset within 5 days) |
| Baselines | B0 climatology by group; B1 calibrated `|z|` rule; B2 persistence lookup; B3 L2-logistic on ~10 core features |
| Core model | LightGBM binary classifier; pooled across instruments; monotone constraints where economically justified (P12) |
| Variants | `full_us` (all features) and `core_transfer` (features available in both markets, §9.6 of the Research Document) |
| Calibration | Isotonic or Platt (sigmoid) fitted on a time-ordered calibration block inside each training fold; choice by development-period log loss |
| Class imbalance | No resampling; `scale_pos_weight` tuned or 1; calibration corrects probabilities |
| Tuning | Random search, ≤ 40 configurations, nested time-series CV inside the development period |
| Explanations | TreeSHAP on the uncalibrated model's log-odds; aggregated by family (§4.14) |
| Analogue finder | k-nearest neighbours over standardised family-SHAP signatures of pre-onset windows of catalogued incidents known before `t` |

---

## 9. Evaluation protocol (summary; details and numeric gates in P11)

| Item | Specification |
|---|---|
| Development period (US) | Data start → `DEV_END` (2019-12-31). Walk-forward annual test folds 2010–2019; each trains on all eligible rows ending `EMBARGO` days before the fold start |
| Lockbox (US) | `LOCKBOX_START` (2020-01-01) → `DATA_CUTOFF`. Annual refits with frozen hyper-parameters; opened once after pre-registration sign-off |
| India | Never used for training `core_transfer`. Zero-shot evaluation on all eligible Indian rows; separate "India-recalibrated" variant using rolling-origin calibration on earlier Indian years only |
| Primary metrics | PR-AUC; Brier skill score vs best baseline; event-level recall at `THR_HIGH` and `THR_WATCH`; median lead time; false alerts per ETF-month |
| Secondary | Log loss; reliability diagram and expected calibration error; ROC-AUC (reported, not primary); results by group, mechanism and year; secondary-label lead times; business-value metrics (Research Document §7.3) |
| Uncertainty | Block bootstrap by calendar month (`BOOT_N` replicates); report 95% CIs and onset counts next to every metric; also report results excluding March 2020 |
| Rows excluded from headline metrics | `confirmed_locked`; `y = null` |

---

## 10. Outputs

### 10.1 `outputs/predictions/predictions_<asof>.parquet` (and the full history `predictions_all.parquet`)

| Column | Type | Meaning |
|---|---|---|
| `instrument_id`, `ticker`, `isin`, `name`, `issuer`, `group`, `is_mirae` | str/bool | Identity |
| `asof_date` | date | `t` |
| `decision_time` | timestamp | `τ(t)` |
| `window_start`, `window_end` | date | `t+1`, `t+H` |
| `prem_bps`, `dev_bps`, `z`, `band_lo_bps`, `band_hi_bps` | float | Current state |
| `lp_bps`, `tg_bps` | float | Layer 1 and total gap (null where not applicable) |
| `p_onset` | float | Calibrated probability (null if not eligible) |
| `risk_level` | str | §4.12 |
| `abs_level_text` | str | Descriptive absolute-premium band |
| `root_cause_tag`, `root_cause_share`, `secondary_tag` | str/float/str | P13 |
| `top_reasons` | JSON str | Up to 3 templated reason strings with values |
| `analogue_incident_id`, `analogue_name`, `analogue_distance` | str/str/float | P13 |
| `sec_counter`, `sebi_counter`, `noquote_counter`, `band_distance_pct` | int/int/int/float | Deterministic monitors |
| `lock_class`, `flags` | str/JSON | Data-quality and regime flags |
| `model_id`, `run_id`, `data_cutoff` | str | Provenance |

### 10.2 Daily ETF Stress Brief

`outputs/briefs/brief_<market>_<asof>.html` and `.md`, rendered from `src/esw/brief/templates/`. Content and rules in P16.

### 10.3 Dashboard

`streamlit run app/streamlit_app.py`: Watchlist, ETF detail, Incident replay, Model evidence (P16).

---

## 11. Tooling and environment

| Concern | Choice | Notes |
|---|---|---|
| OS | Windows 11 (user's machine); code must be OS-neutral | Use `pathlib`; no shell-specific scripts in the pipeline |
| Python | **3.11** (installed at `C:\Users\Nakul\AppData\Local\Programs\Python\Python311`) | Decision D-002: use the installed version rather than require a new install. 3.12 also acceptable if already present. |
| Environment | `uv` if available (`pip install uv`), else `python -m venv .venv` + `pip` | Lockfile: `uv.lock` or `requirements-lock.txt` |
| Core libraries | pandas ≥ 2.2, numpy, pyarrow, duckdb, scipy, scikit-learn, lightgbm, shap, pandera, pydantic ≥ 2, pyyaml, python-dotenv, requests, tenacity, openpyxl, exchange_calendars, bidask, matplotlib, plotly, jinja2, streamlit, typer | Pin exact versions in the lockfile in P00 |
| Optional | yfinance (fallback prices), statsmodels | |
| Dev tools | pytest, pytest-cov, ruff (lint + format) | |
| CLI | `python -m esw <command>` (Typer) | No Makefile (Windows) |

**Secrets:** API keys live only in `.env` (gitignored). `.env.example` lists the names: `TIINGO_API_KEY`, `FRED_API_KEY` (optional), `ESW_USER_AGENT` (a generic client string, e.g., `esw-research-bot/0.1`; do not put personal email addresses in it).

**Polite data access:** identify with `ESW_USER_AGENT`; at most 1 request per second per host (configurable); exponential back-off with jitter on 429/5xx (max 5 retries); cache raw files and never re-download an existing complete file unless `--refresh`.

---

## 12. Coding, testing and run conventions

1. **Determinism.** All randomness seeded from `SEED`; LightGBM `deterministic=true`, `num_threads` fixed in config.
2. **Configuration.** No magic numbers in code: parameters come from `config/settings.yaml` (validated by a Pydantic model). Every run writes the resolved config to its run folder.
3. **Type hints and docstrings** on public functions; ruff clean (`ruff check`, `ruff format --check`).
4. **Tests.** `tests/unit` for functions; `tests/integration` for stage outputs on fixtures; `tests/acceptance/test_pXX_acceptance.py` encodes each phase's objective acceptance criteria and runs on the real data where feasible. `pytest -q` must pass before any phase is marked complete.
5. **Runs.** Every model training/evaluation invocation creates `runs/<YYYYMMDD-HHMMSS>_<slug>/` with `config.yaml`, `git_commit.txt`, `data_fingerprint.json` (hashes of input Parquet files), `metrics.json`, `predictions.parquet` (gitignored), `plots/`, `README.md` (auto-generated summary + agent notes), and appends one row to `runs/registry.csv` (`run_id, phase, purpose, model_id, data_cutoff, key metrics, status, notes`).
6. **Logging.** `logging` with format `%(asctime)s %(levelname)s %(name)s run=%(run_id)s | %(message)s`, to console and `logs/<date>_<command>.log`.
7. **Errors.** Fail loudly on schema violations; never silently impute. Missing values are explicit nulls plus `*_missing` indicator features.
8. **Notebooks** are allowed only for exploration in `notebooks/` and never as the source of a reported number. Every reported number comes from a script and a run folder.

---

## 13. Phase map and dependencies

| Phase | Title | Depends on | Typical effort [A] |
|---|---|---|---|
| P00 | Environment, repository and governance setup | — | 0.5–1 day |
| P01 | Source verification and access probes | P00 | 2–3 days |
| P02 | Reference data: universe, identifiers, calendars, NAV clocks | P01 | 2–3 days |
| P03 | Incident and operational-event catalogue | P02 | 3–4 days |
| P04 | US ETF data acquisition | P02 | 3–4 days |
| P05 | India ETF data acquisition | P02 | 3–4 days |
| P06 | Underlying, market-wide and FX data acquisition | P02 | 2–3 days |
| P07 | Curation, alignment, point-in-time store and data quality | P03–P06 | 3–5 days |
| P08 | Pricing layer | P07 | 2–3 days |
| P09 | Labels: dislocation episodes and targets | P08 | 2–3 days |
| P10 | Feature engineering: stress signals | P08 (not P09) | 4–6 days |
| P11 | Evaluation harness, baselines and pre-registration | P09, P10 | 3–4 days |
| P12 | Model development (development period only) | P11 | 4–5 days |
| P13 | Explainability: root-cause tags and analogue finder | P12, P03 | 3–4 days |
| P14 | US lockbox evaluation, sensitivity and event replays | P13 + MI-11 | 3–4 days |
| P15 | India transfer test | P14 | 3–4 days |
| P16 | Daily ETF Stress Brief and dashboard | P13 (P14/P15 for evidence views) | 3–5 days |
| P17 | Final validation, verification, report and readiness | P14–P16 | 3–5 days |

P03, P04, P05 and P06 may run in parallel once P02 is accepted. P10 may start once P08 is accepted (it must not depend on labels).

**Gate rule.** A phase may start only when every phase it depends on has status `VERIFIED` in `records/STATUS.md`, its acceptance report exists in `records/acceptance/`, and its walkthrough exists in `records/walkthroughs/`. The procedure is in the [process document](../process/Documentation_Logging_and_Phase_Gates.md).

---

## 14. Global Definition of Done (applies to every phase)

A phase is `VERIFIED` only when **all** of these hold:

1. Every deliverable in the phase document exists at the stated path.
2. `pytest -q` passes (all unit, integration and the phase's acceptance tests); `ruff check` is clean.
3. Every acceptance criterion in the phase document is evaluated and recorded as PASS, or as WAIVED with a logged decision and the user's approval where the phase document says approval is needed.
4. The phase's acceptance report (`records/acceptance/PXX_acceptance.md`) and walkthrough (`records/walkthroughs/PXX_walkthrough.md`) are written from the templates.
5. `records/STATUS.md`, `records/PROGRESS_LOG.md`, and, as applicable, `records/DECISIONS.md`, `records/ISSUES.md`, `records/OPEN_QUESTIONS.md` and `records/MANUAL_ACTIONS.md` are updated.
6. Any manual intervention the phase required is recorded as `DONE` and verified.
7. Work is committed under the commit policy recorded in P00 (decision D-003).

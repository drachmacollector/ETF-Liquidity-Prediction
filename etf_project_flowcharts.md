# ETF Premium Early-Warning — Architecture Flowcharts

Two diagrams, two audiences:

1. **Master Flowchart (Full Technical Detail)** — every component, every data check, every modelling and validation step. Use this as your own personal reference map of the entire system — if you ever forget how a piece fits, find it here.
2. **Simplified Pitch Flowchart (Financial-First)** — built for Umesh. Light on engineering jargon, explicit about the financial mechanics (NAV vs iNAV, the signals considered, the two prediction outputs). Meant to be understood at a glance.

Both diagrams use [Mermaid](https://mermaid.js.org/) syntax — they'll render automatically in GitHub, Claude, Obsidian, most modern Markdown viewers, or at [mermaid.live](https://mermaid.live) if you want to paste one in and inspect/export it as an image for a slide.

---

## 1. Master Flowchart — Full System Detail

*Every data source, every cleaning/validation step, every feature group, every model, every validation mechanism, every output. This is the "zoom all the way in" view.*

```mermaid
flowchart TD

%% ========== DATA SOURCES ==========
subgraph SRC["RAW DATA SOURCES (daily, free, public)"]
    NSE["NSE UDiFF CM Bhavcopy<br/>D1: OHLC, volume, turnover, trades<br/>2 schemas pre/post 8-Jul-2024"]
    BSE["BSE EOD Bhavcopy<br/>D1 fallback"]
    AMFI1["AMFI NAVAll.txt<br/>D2: latest NAV, all schemes"]
    AMFI2["AMFI NAV-History Download<br/>D2: max 90 days per request"]
    D4["Gold/Silver Global Benchmark Proxy<br/>D4: MCX / IBJA / LBMA-derived"]
    D5["USD/INR FX Reference<br/>D5: RBI/FBIL"]
    D7["Hand-built Scheme Master<br/>D7: ISIN, AMFI code, symbol history,<br/>issuer, metal, inception, creation unit"]
    D10["Trading Calendar<br/>D10: holidays + special sessions<br/>e.g. Sun 1-Feb-2026 Budget session"]
    EVT["Hand-made Events Table<br/>FoF halts/resumes, symbol changes,<br/>regime changes — 10-15 rows"]
end

%% ========== INGESTION ==========
subgraph ING["INGESTION LAYER"]
    DL["Download Scripts<br/>polite UA, delays, retry w/ backoff,<br/>prefer archive host over live site"]
    RAWSTORE[("Raw File Store<br/>immutable, checksummed, dated<br/>never edited in place")]
end

%% ========== CLEANING / VALIDATION ==========
subgraph CLN["CLEANING & VALIDATION"]
    SCHEMA["Schema Normalizer<br/>reconciles 2 bhavcopy layouts<br/>into one internal schema"]
    ISIN_KEY["Identity Resolution<br/>key on ISIN, NOT ticker<br/>e.g. SILVRETF -> SILVERAG (15-Sep-2025)"]
    CHK1["Price Sanity Checks<br/>high>=max(o,c,l), low<=min(...), vol>=0,<br/>1 row per ISIN/date"]
    CHK2["NAV Sanity Checks<br/>positive; day-over-day vs proxy return<br/>large gap -> flag NAV-timing issue"]
    CHK3["Cross-Source Check<br/>|close/NAV - 1| > 25% -> manual review"]
    CHK4["Mapping Check<br/>every universe ISIN has exactly<br/>1 AMFI code + >=1 exchange symbol"]
    CHK5["Coverage Report<br/>per-ETF first/last date, missing days"]
    SURV["Survivorship Handling<br/>include merged/renamed/delisted ETFs<br/>that existed during eval period"]
    CURATED[("Curated Parquet Tables<br/>queried via DuckDB")]
end

%% ========== DEFINITIONS LAYER ==========
subgraph DEF["CORE DEFINITIONS (computed per ETF-day)"]
    PREMDEF["prem(i,t) = 10000 x (Close - NAV) / NAV<br/>in basis points, vs OFFICIAL NAV<br/>(not iNAV — see Lesson flag)"]
    M60DEF["m60(i,t) = 60-day trailing median premium<br/>'this ETF's own normal'"]
    MADDEF["MAD60(i,t) = 60-day median absolute deviation"]
    REGIMEDEF["Regime Flag<br/>R0: until 30-Jan-2026<br/>R1: 1-Feb to 4-Sep-2026 (exchange-specific sub-history)<br/>R2: from 7-Sep-2026"]
    LOCKDEF["Circuit-Lock Flag<br/>uses ACTUAL historical applicable band<br/>(not a flat assumed +-20%) OR falls back to<br/>Confirmed / Potentially-Constrained / Unknown"]
end

%% ========== POINT-IN-TIME DISCIPLINE ==========
subgraph PIT["POINT-IN-TIME ENGINEERING (critical, cross-cutting)"]
    PITRULE["Rule: day-t feature row uses ONLY<br/>data dated <= t; NAV(t) usable for<br/>predicting t+1, not same-day t"]
    KNOWNAT["Event timestamps: effective_at vs known_at<br/>backtest features use known_at only<br/>(prevents notice-lag leakage)"]
    LEAKTEST["Automated Leak Test<br/>inject future value into one input,<br/>assert features don't change"]
    CANARY["Leaky-Canary Feature Test<br/>a feature literally equal to the future<br/>label must be auto-flagged by the harness"]
end

%% ========== FEATURE ENGINEERING ==========
subgraph FEAT["FEATURE BUILDER (~35-45 features/ETF/day)"]
    F1["F1 Premium Dynamics<br/>prem lags 0-5; rolling mean/median/std<br/>5/20/60d; MAD60; z-score; 5d slope;<br/>days since |prem|>tau"]
    F2["F2 Liquidity Proxies<br/>turnover/20d-avg ratio+zscore;<br/>trades-count z-score; (H-L)/C;<br/>zero/low-vol days; stale-price flag"]
    F3["F3 Underlying & Volatility<br/>proxy return 1/3/5d; realized vol 5/20d;<br/>largest overnight gap 5d; drawdown 10d high;<br/>NAV-vs-proxy residual (clock-mismatch signal)"]
    F4["F4 Peer Cross-Section<br/>peer-group median premium;<br/>own - peer median; peer dispersion;<br/>share of peers beyond tau"]
    F5["F5 Context<br/>metal; issuer; days since listing; regime flag;<br/>Dhanteras/Diwali/Akshaya Tritiya proximity;<br/>Union Budget window; active FoF-halt flag"]
    HANDLE["Robust scaling by group; winsorize;<br/>explicit missing-value flags (no silent imputation);<br/>first 60 days post-listing excluded from training<br/>(but still predicted, flagged low_history"]
end

%% ========== LABELS (ISOLATED MODULE) ==========
subgraph LAB["LABELS MODULE (import-isolated from features)"]
    TASKA_LBL["Task A Label<br/>prem(i,t+1) — the actual next-day premium"]
    TAUFREEZE["tau frozen pre-test<br/>per group: gold/silver ~200bps,<br/>controls ~50bps; train-period event rate 2-5%"]
    TASKB_LBL["Task B Label E(i,t+1) =<br/>1 if |prem(t+1) - m60(t)| >= max(tau, 3*MAD60(t))<br/>i.e. deviation from the ETF's OWN recent normal"]
    ABSWARN["Separate Absolute-Premium Warning<br/>(independent of tail-label) so a chronically<br/>expensive ETF can't 'normalize' into invisibility"]
end

%% ========== BASELINES ==========
subgraph BASE["BASELINES (must be beaten, out-of-sample)"]
    B0["B0 Persistence<br/>prem(t+1) = prem(t);<br/>interval from own recent forecast errors"]
    B1["B1 Rolling-Volatility Rule<br/>flag if |prem(t)-m60|>k*MAD60;<br/>PROBABILITY = historical conditional<br/>event frequency given current risk state"]
    B2["B2 Peer-Median Model<br/>peer-group rolling quantiles;<br/>PROBABILITY = peer-group historical<br/>tail-event frequency"]
end

%% ========== CORE MODELS ==========
subgraph MDL["CORE MODELS"]
    LGBMA["LightGBM Quantile Regression<br/>Task A: 5 models, one per quantile<br/>(5/25/50/75/95%), pooled across ETFs<br/>w/ metal+issuer+regime as features"]
    LGBMB["LightGBM Binary Classifier<br/>Task B: class-weighted,<br/>time-ordered validation split"]
    CQR["Conformalized Quantile Regression<br/>rolling time-ordered calibration window<br/>(>=250 ETF-days); widens/narrows intervals<br/>to hit target coverage; coverage checked<br/>SEPARATELY by period & ETF group<br/>(panel data isn't i.i.d.)"]
    ISO["Isotonic Regression<br/>calibrates Task B raw scores into<br/>trustworthy probabilities"]
    OPTUNA["Optuna Hyperparameter Search<br/>inside time-series CV, training data only"]
    SHAP["SHAP Value Attribution<br/>per-prediction feature contributions<br/>-> mapped to reason-code templates<br/>e.g. 'turnover 3.2x its 20-day average'"]
    ABLATE["Ablation Study<br/>drop F1-F5 each in turn,<br/>measure skill loss"]
end

%% ========== BACKTEST / VALIDATION ==========
subgraph BT["BACKTEST & VALIDATION"]
    WF["Walk-Forward, Expanding Window<br/>train through T, test next block,<br/>refit monthly, no shuffling"]
    PURGE["Purge / Embargo<br/>drop rows whose label window overlaps<br/>test block; 5-trading-day embargo"]
    SPLIT["Regime-Split Reporting<br/>R0 / R1 (exchange-specific) / R2<br/>reported separately; R2 flagged as short"]
    METRICS_A["Task A Metrics<br/>Pinball loss (+ % vs best baseline);<br/>90%/50% interval coverage; Kupiec test"]
    METRICS_B["Task B Metrics<br/>Brier skill score vs best PROBABILITY<br/>baseline; PR-AUC; reliability diagram;<br/>precision/recall at Watch/High;<br/>lead time; false alerts/ETF-month"]
    BOOT["Block Bootstrap<br/>~10-day blocks, resample by ETF+time,<br/>95% CIs; event count always printed alongside"]
    PREREG["Pre-Registration<br/>config/pre_registration.md — event defs,<br/>tau, thresholds, success criteria<br/>FROZEN before test runs"]
end

%% ========== EVENT STUDIES ==========
subgraph EVS["EVENT STUDIES (headline demonstration)"]
    E1["E1: Silver Premium Squeeze<br/>22-Sep to 24-Oct-2025<br/>Target: official-NAV deviation<br/>(iNAV reports kept as CONTEXT only,<br/>not the ground-truth label)"]
    E2["E2: Crash Stress Test<br/>26-Jan to 13-Feb-2026<br/>lock-days flagged, not silently excluded"]
    FWDLOG["Forward Test Log (optional stretch)<br/>forward_log.csv appended daily,<br/>git-committed for independent timestamp proof"]
end

%% ========== OUTPUTS ==========
subgraph OUT["OUTPUTS"]
    PREDCSV["predictions.csv<br/>isin, asof_date, target_date, regime,<br/>prem_now_bps, q05..q95, p_tail,<br/>risk_level, top_reasons, lock_flag,<br/>low_history_flag, model_id"]
    RISKMAP["Risk Level Mapping<br/>Normal / Watch (P>=10%) / High (P>=30%)<br/>— initial seed, FINAL thresholds tuned<br/>on train/val to an alert budget, then frozen"]
end

%% ========== DEMO / DASHBOARD ==========
subgraph DASH["STREAMLIT DEMO"]
    V1["View 1: Risk Table<br/>per-ETF premium, 5-95% interval,<br/>P(tail), risk level, sparkline, top reason"]
    V2["View 2: ETF Detail<br/>price-vs-NAV chart; forecast fan;<br/>probability gauge; reason-code panel;<br/>peer comparison; event markers"]
    V3["View 3: Event Replay<br/>date slider over E1/E2;<br/>'what the system would have said that day'"]
end

%% ========== TESTING ==========
subgraph TEST["TESTING HARNESS"]
    T1["Golden-file tests — both bhavcopy schemas,<br/>AMFI variants; idempotency"]
    T2["Universe tests — 1 ISIN:1 AMFI code;<br/>symbol-history lookups"]
    T3["Calendar tests — holiday/special-session logic"]
    T4["Feature unit tests + leak test + rebuild-equality"]
    T5["Label tests — synthetic-path; import-guard"]
    T6["Model tests — fixed-seed reproducibility;<br/>calibration check on frozen sample"]
    T7["Backtest tests — purge/embargo correctness;<br/>leaky-canary must be flagged"]
    T8["App smoke test — 3 views load from sample CSV"]
end

%% ===== FLOW CONNECTIONS =====
NSE --> DL
BSE --> DL
AMFI1 --> DL
AMFI2 --> DL
D4 --> DL
D5 --> DL
D7 --> DL
D10 --> DL
EVT --> DL
DL --> RAWSTORE
RAWSTORE --> SCHEMA
SCHEMA --> ISIN_KEY
ISIN_KEY --> CHK1 --> CHK2 --> CHK3 --> CHK4 --> CHK5
CHK5 --> SURV --> CURATED

CURATED --> PREMDEF --> M60DEF --> MADDEF
CURATED --> REGIMEDEF
CURATED --> LOCKDEF

PREMDEF --> PITRULE
EVT --> KNOWNAT --> PITRULE
PITRULE --> LEAKTEST
PITRULE --> CANARY

PITRULE --> F1
PITRULE --> F2
PITRULE --> F3
PITRULE --> F4
PITRULE --> F5
F1 --> HANDLE
F2 --> HANDLE
F3 --> HANDLE
F4 --> HANDLE
F5 --> HANDLE

M60DEF --> TASKA_LBL
MADDEF --> TASKB_LBL
TAUFREEZE --> TASKB_LBL
TASKA_LBL --> ABSWARN
TASKB_LBL --> ABSWARN

HANDLE --> B0
HANDLE --> B1
HANDLE --> B2
TASKA_LBL --> B0
TASKB_LBL --> B1
TASKB_LBL --> B2

HANDLE --> LGBMA
HANDLE --> LGBMB
TASKA_LBL --> LGBMA
TASKB_LBL --> LGBMB
OPTUNA --> LGBMA
OPTUNA --> LGBMB
LGBMA --> CQR
LGBMB --> ISO
LGBMA --> SHAP
LGBMB --> SHAP
HANDLE --> ABLATE

CQR --> WF
ISO --> WF
B0 --> WF
B1 --> WF
B2 --> WF
WF --> PURGE --> SPLIT
SPLIT --> METRICS_A
SPLIT --> METRICS_B
METRICS_A --> BOOT
METRICS_B --> BOOT
PREREG -.frozen before.-> E1
PREREG -.frozen before.-> E2
BOOT --> E1
BOOT --> E2
LOCKDEF --> E2
E1 --> FWDLOG
E2 --> FWDLOG

CQR --> PREDCSV
ISO --> PREDCSV
SHAP --> PREDCSV
LOCKDEF --> PREDCSV
RISKMAP --> PREDCSV

PREDCSV --> V1
PREDCSV --> V2
PREDCSV --> V3
E1 --> V3
E2 --> V3

T1 -.validates.-> ING
T2 -.validates.-> CLN
T3 -.validates.-> DEF
T4 -.validates.-> FEAT
T5 -.validates.-> LAB
T6 -.validates.-> MDL
T7 -.validates.-> BT
T8 -.validates.-> DASH
```

---

## 2. Financial flowchart

```mermaid
flowchart TD

subgraph DATA["Daily Public Data We Use"]
    direction LR
    D_PRICE["Exchange Closing Price<br/>(NSE/BSE, every trading day) Bhavcopy"]
    D_NAV["Official AMFI NAV published once/day"]
    D_METAL["Global Gold/Silver Price<br/>+ USD/INR Rate"]
    D_ID["ETF Identity & Calendar<br/>(ISIN, symbol history, trading days)"]
end

subgraph CLOCK["The NAV vs iNAV Distinction"]
    direction LR
    NAV_OFF["Official NAV<br/>once a day,<br/>full historical archive"]
    INAV_LIVE["iNAV (intraday estimate)<br/>live only, NO public<br/>historical archive"]
    TARGET["Model is trained & tested against<br/>Close-vs-OFFICIAL-NAV deviation<br/>(iNAV used only as context)"]
end

subgraph SIGNALS["Financial Signals the Model Weighs"]
    S1["Premium/Discount vs. this<br/>ETF's own recent normal"]
    S2["Trading volume & liquidity stress<br/>(is demand surging ?)"]
    S3["Underlying metal volatility &<br/>global-vs-India timing gap"]
    S4["Peer ETF behaviour<br/>(is it just this fund, or<br/>the whole gold/silver category?)"]
    S5["Seasonal & regulatory context<br/>(festivals, FoF halts, SEBI regime)"]
end

subgraph AI["The AI Forecaster"]
    LEARN["Learns which COMBINATIONS of<br/>signals preceded past dislocations<br/>(Oct-2025 squeeze, Feb-2026 crash)"]
    OUT_A["Output A — Premium Range<br/>'tomorrow's premium likely lands<br/>between X% and Y%'"]
    OUT_B["Output B — Tail-Risk Probability<br/>'P% chance of an unusual jump away<br/>from this ETF's own normal'"]
end

subgraph DESK["What the Sales Desk Sees"]
    RISK["Daily Risk List<br/>Normal / Watch / High<br/>— per ETF, Mirae products highlighted"]
    WHY["Plain-Language Reasons<br/>e.g. 'volume 3x normal,<br/>peer silver ETFs also elevated'"]
    PROOF["Event Replay<br/>'what would this have said<br/>on 9-Oct-2025 and in Feb-2026?'"]
end

D_PRICE --> S1
D_NAV --> S1
D_NAV --> NAV_OFF --> TARGET
INAV_LIVE -.not the training target.-> TARGET
D_METAL --> S3
D_ID --> S1

S1 --> LEARN
S2 --> LEARN
S3 --> LEARN
S4 --> LEARN
S5 --> LEARN
TARGET --> LEARN

LEARN --> OUT_A
LEARN --> OUT_B

OUT_A --> RISK
OUT_B --> RISK
LEARN --> WHY
OUT_A --> PROOF
OUT_B --> PROOF
```

---


## More simpler

```mermaid
%%{init: {'flowchart': {'curve': 'basis'}}}%%
flowchart TD

subgraph DATA["Daily Public Data We Use"]
    direction LR
    D_PRICE["Exchange Closing Price<br/>(NSE/BSE, every trading day) Bhavcopy"]
    D_NAV["Official AMFI NAV published once/day"]
    D_METAL["Global Gold/Silver Price<br/>+ USD/INR Rate"]
    D_ID["ETF Identity & Calendar<br/>(ISIN, symbol history, trading days)"]
end

subgraph CLOCK["The NAV vs iNAV Distinction"]
    direction LR
    NAV_OFF["Official NAV<br/>once a day,<br/>full historical archive"]
    INAV_LIVE["iNAV (intraday estimate)<br/>live only, NO public<br/>historical archive"]
    TARGET["Model is trained & tested against<br/>Close-vs-OFFICIAL-NAV deviation<br/>(iNAV used only as context)"]
end

subgraph FORMULAS["The Core Math — How Every Number Is Actually Calculated"]
    direction TB
    FORM1["Premium / Discount (bps)<br/>prem(i,t) = 10,000 × (Price(i,t) − NAV(i,t)) / NAV(i,t)<br/>positive = premium, negative = discount"]
    FORM2["Own-Normal Baseline<br/>m60(i,t) = 60-day trailing MEDIAN of prem(i,t)<br/>MAD60(i,t) = 60-day trailing median absolute deviation"]
    FORM3["Tail-Event Label (what Output B learns from)<br/>E(i,t+1) = 1 if │prem(i,t+1) − m60(i,t)│ ≥ max(τ, 3×MAD60(i,t))<br/>τ frozen pre-test: ≈200bps gold/silver, ≈50bps controls"]
    FORM4["Output A — Quantile Forecast<br/>5 LightGBM models → Q5, Q25, Q50, Q75, Q95 of prem(i,t+1)<br/>90% interval = [Q5, Q95], median = Q50"]
    FORM5["Output B — Calibrated Probability<br/>raw LightGBM score → Isotonic Regression → P(E=1)<br/>Risk level: Watch if P≥10%, High if P≥30%"]
end

subgraph SIGNALS["Financial Signals the Model Weighs"]
    direction LR
    S1["Premium/Discount vs. this<br/>ETF's own recent normal"]
    S2["Trading volume & liquidity stress<br/>(is demand surging ?)"]
    S3["Underlying metal volatility &<br/>global-vs-India timing gap"]
    S4["Peer ETF behaviour<br/>(is it just this fund, or<br/>the whole gold/silver category?)"]
    S5["Seasonal & regulatory context<br/>(festivals, FoF halts, SEBI regime)"]
end

subgraph AI["The AI Forecaster — LightGBM (Gradient-Boosted Decision Trees)"]
    direction TB
    MODEL["Model used: LightGBM<br/>hundreds of small decision trees working<br/>together, built one after another"]
    ELI10["ELI10 — how it actually learns:<br/>Tree 1 makes a rough, crude guess.<br/>Tree 2 looks ONLY at what Tree 1 got wrong<br/>and nudges the answer to fix that mistake.<br/>Tree 3 fixes whatever is still wrong after 1+2.<br/>...repeat this correction loop hundreds of times.<br/>Final prediction = sum of all the small corrections,<br/>like sharpening a blurry photo one pass at a time."]
    LEARN["Learns which COMBINATIONS of<br/>signals preceded past dislocations<br/>(Oct-2025 squeeze, Feb-2026 crash)"]
    OUT_A["Output A — Premium Range<br/>5 quantile models (Q5/Q25/Q50/Q75/Q95)<br/>→ a calibrated range for tomorrow's premium"]
    OUT_B["Output B — Tail-Risk Probability<br/>binary classifier + Isotonic calibration<br/>→ a trustworthy P% chance of an unusual jump"]
end

subgraph DESK["Illustrative Forecast Output — Mirae Silver ETF"]
    direction LR
    CARDA["OUTPUT A · PREMIUM RANGE<br/><b>+1.2% to +4.8%</b><br/>90% prediction interval<br/>Median forecast: +2.7%"]
    CARDB["OUTPUT B · TAIL-RISK PROBABILITY<br/><b>68%</b><br/>HIGH RISK<br/>Probability of an unusually large deviation<br/>from this ETF's own recent normal"]
    NOTE["Illustrative values only —<br/>not real market data or live predictions"]
end

D_PRICE --> S1
D_NAV --> S1
D_NAV --> NAV_OFF --> TARGET
INAV_LIVE -.not the training target.-> TARGET
D_METAL --> S3
D_ID --> S1

D_PRICE --> FORM1
D_NAV --> FORM1
FORM1 --> FORM2 --> FORM3
FORM1 --> FORM4
FORM3 --> FORM5

S1 --> LEARN
S2 --> LEARN
S3 --> LEARN
S4 --> LEARN
S5 --> LEARN
TARGET --> LEARN
FORM3 --> LEARN
FORM4 --> LEARN

MODEL --> ELI10 --> LEARN
LEARN --> OUT_A
LEARN --> OUT_B
FORM4 --> OUT_A
FORM5 --> OUT_B

OUT_A --> CARDA
OUT_B --> CARDB
CARDA --> NOTE
CARDB --> NOTE

classDef data fill:#E8F1FA,color:#17365D,stroke:#5684B5,stroke-width:1px
classDef clock fill:#F3E8FF,color:#432B68,stroke:#9333EA,stroke-width:1px
classDef formula fill:#FFF7E0,color:#7A5B00,stroke:#D9A441,stroke-width:1.5px
classDef signal fill:#EAF3EA,color:#234D30,stroke:#65966B,stroke-width:1px
classDef ai fill:#E9EEFB,color:#1E3A8A,stroke:#4C6FDE,stroke-width:1.5px
classDef desk fill:#EDE7F8,color:#432B68,stroke:#8A70B5,stroke-width:1px
classDef cardA fill:#D1FAE5,color:#064E3B,stroke:#059669,stroke-width:2px
classDef cardB fill:#FEE2E2,color:#7F1D1D,stroke:#DC2626,stroke-width:2px

class D_PRICE,D_NAV,D_METAL,D_ID data
class NAV_OFF,INAV_LIVE,TARGET clock
class FORM1,FORM2,FORM3,FORM4,FORM5 formula
class S1,S2,S3,S4,S5 signal
class MODEL,ELI10,LEARN,OUT_A,OUT_B ai
class CARDA cardA
class CARDB cardB
class NOTE desk
```


### another one

```mermaid
flowchart TB

    %% =====================================================
    %% ETF PREMIUM EARLY-WARNING SYSTEM
    %% FINANCIAL-FIRST ARCHITECTURE
    %% =====================================================

    TITLE(["ETF PREMIUM EARLY-WARNING SYSTEM<br/>Gold & Silver ETFs · India"])

    %% ---------------- DATA SOURCES ----------------

    subgraph DATA["01 · MARKET DATA — WHAT HAPPENS TODAY?"]
        direction LR

        MARKET(["Exchange Data<br/><b>NSE / BSE</b><br/>Closing price · Volume<br/>Turnover · Trades"])

        NAV(["Official NAV<br/><b>AMFI</b><br/>Daily published valuation<br/>Historical data available"])

        METAL(["Underlying Markets<br/><b>Gold / Silver + USD/INR</b><br/>Global price movements<br/>Volatility · Overnight gaps"])

        CONTEXT(["ETF & Market Context<br/>Scheme identity · Peers<br/>Trading calendar · Events<br/>Regulatory regime"])

        INAV(["Live iNAV<br/><b>Mirae Asset Website</b><br/>Intraday indicative valuation<br/>No usable historical archive"])
    end

    %% ---------------- VALUATION DISTINCTION ----------------

    subgraph VALUATION["02 · UNDERSTANDING THE ETF'S VALUE"]
        direction LR

        PRICE(["Exchange Market Price<br/>What buyers and sellers<br/>actually pay"])

        OFFICIAL(["Official NAV<br/>Authoritative daily<br/>scheme valuation"])

        INDICATIVE(["iNAV<br/>Live estimate of<br/>intraday value"])

        PREMIUM(["DAILY PREMIUM / DISCOUNT<br/><b>(Market Close − Official NAV) ÷ NAV</b><br/>Measured in basis points"])

        CLOCK(["Valuation Timing Check<br/>Global metal markets and<br/>Indian ETF markets run on<br/>different trading clocks"])
    end

    %% ---------------- FEATURE ENGINEERING ----------------

    subgraph SIGNALS["03 · FINANCIAL SIGNALS — WHAT MAY INDICATE STRESS?"]
        direction LR

        S1(["Premium Behaviour<br/>Recent trend · Volatility<br/>Deviation from own normal"])

        S2(["Trading & Liquidity<br/>Turnover · Trade count<br/>Price range · Stale prices"])

        S3(["Underlying Metal<br/>Gold / silver volatility<br/>Overnight gaps · Price shocks"])

        S4(["Peer ETF Behaviour<br/>Are other gold / silver ETFs<br/>showing similar deviations?"])

        S5(["Market Context<br/>Festivals · FoF restrictions<br/>Regulatory regime · Holidays"])
    end

    %% ---------------- AI ENGINE ----------------

    subgraph AI["04 · MACHINE-LEARNING FORECASTER"]
        direction TB

        LEARN{{"Learn patterns from historical ETF behaviour<br/>and today's financial conditions"}}

        subgraph PREDICTIONS["TWO COMPLEMENTARY FORECASTS"]
            direction LR

            TASK_A(["<b>OUTPUT A · PREMIUM RANGE</b><br/>Forecast tomorrow's closing<br/>premium / discount to NAV<br/><br/>Example: −1% to +3%"])

            TASK_B(["<b>OUTPUT B · TAIL-RISK PROBABILITY</b><br/>Chance of an unusually large<br/>deviation from the ETF's<br/>own recent normal<br/><br/>Example: 65%"])
        end

        EXPLAIN(["Explainable Predictions<br/>Identify the strongest contributing<br/>signals and generate plain-language<br/>reason codes"])
    end

    %% ---------------- VALIDATION ----------------

    subgraph VALIDATION["05 · HISTORICAL TESTING — DOES IT ACTUALLY WORK?"]
        direction LR

        OCT(["<b>OCTOBER 2025</b><br/>Silver Premium Squeeze<br/><br/>Test for unusual<br/>official-NAV deviations<br/>iNAV reports = context only"])

        FEB(["<b>JAN–FEBRUARY 2026</b><br/>Precious-Metal Crash<br/><br/>Extreme-market stress test<br/>Identify price-band constraints<br/>No claim of predicting circuits"])

        BASELINE(["Benchmark Comparison<br/>Simple historical methods<br/>vs. machine learning<br/><br/>Walk-forward backtesting"])
    end

    %% ---------------- BUSINESS OUTPUT ----------------

    subgraph BUSINESS["06 · WHAT THE ETF SALES TEAM RECEIVES"]
        direction LR

        DASH(["<b>DAILY ETF RISK MONITOR</b><br/>Gold & Silver ETF risk table<br/>Normal · Watch · High"])

        DETAIL(["ETF-Level Analysis<br/>Forecast range · Tail probability<br/>Historical premium chart<br/>Peer comparison"])

        REASONS(["Evidence-Based Reasons<br/>Why the model raised a warning<br/>What signals are deteriorating"])

        REPLAY(["Historical Event Replay<br/>What would the system<br/>have said at the time?"])
    end

    END(["<b>BUSINESS PURPOSE</b><br/>Earlier visibility into unusual ETF pricing conditions<br/>to support better-informed distributor and advisor conversations"])

    %% ---------------- CONNECTIONS ----------------

    MARKET --> PRICE
    NAV --> OFFICIAL
    INAV -. "Live contextual reference" .-> INDICATIVE
    METAL --> CLOCK

    PRICE --> PREMIUM
    OFFICIAL --> PREMIUM
    INDICATIVE -. "Not the historical model target" .-> CLOCK
    CLOCK --> PREMIUM

    PREMIUM --> S1
    MARKET --> S2
    METAL --> S3
    CONTEXT --> S5
    CONTEXT --> S4
    PREMIUM --> S4

    S1 --> LEARN
    S2 --> LEARN
    S3 --> LEARN
    S4 --> LEARN
    S5 --> LEARN

    LEARN --> TASK_A
    LEARN --> TASK_B
    LEARN --> EXPLAIN

    TASK_A --> DASH
    TASK_B --> DASH
    TASK_A --> DETAIL
    TASK_B --> DETAIL
    EXPLAIN --> REASONS

    PREMIUM --> OCT
    PREMIUM --> FEB
    TASK_A --> BASELINE
    TASK_B --> BASELINE

    OCT --> REPLAY
    FEB --> REPLAY
    BASELINE -. "Evidence of model performance" .-> DETAIL

    DASH --> END
    DETAIL --> END
    REASONS --> END
    REPLAY --> END

    %% ---------------- STYLING ----------------

    classDef title fill:#172554,stroke:#60A5FA,color:#FFFFFF,stroke-width:2px,font-size:19px,font-weight:bold;
    classDef data fill:#E0F2FE,stroke:#0284C7,color:#0C4A6E,stroke-width:1.5px;
    classDef valuation fill:#F3E8FF,stroke:#9333EA,color:#581C87,stroke-width:1.5px;
    classDef signal fill:#FEF3C7,stroke:#D97706,color:#78350F,stroke-width:1.5px;
    classDef ai fill:#DBEAFE,stroke:#2563EB,color:#1E3A8A,stroke-width:2px;
    classDef prediction fill:#D1FAE5,stroke:#059669,color:#064E3B,stroke-width:2px;
    classDef validation fill:#FCE7F3,stroke:#DB2777,color:#831843,stroke-width:1.5px;
    classDef business fill:#EDE9FE,stroke:#7C3AED,color:#4C1D95,stroke-width:1.5px;
    classDef outcome fill:#172554,stroke:#60A5FA,color:#FFFFFF,stroke-width:2px,font-weight:bold;

    class TITLE title;
    class MARKET,NAV,METAL,CONTEXT,INAV data;
    class PRICE,OFFICIAL,INDICATIVE,PREMIUM,CLOCK valuation;
    class S1,S2,S3,S4,S5 signal;
    class LEARN,EXPLAIN ai;
    class TASK_A,TASK_B prediction;
    class OCT,FEB,BASELINE validation;
    class DASH,DETAIL,REASONS,REPLAY business;
    class END outcome;

    style DATA fill:#F0F9FF,stroke:#7DD3FC,stroke-width:2px
    style VALUATION fill:#FAF5FF,stroke:#C084FC,stroke-width:2px
    style SIGNALS fill:#FFFBEB,stroke:#FBBF24,stroke-width:2px
    style AI fill:#EFF6FF,stroke:#60A5FA,stroke-width:2px
    style PREDICTIONS fill:#ECFDF5,stroke:#34D399,stroke-width:1.5px
    style VALIDATION fill:#FDF2F8,stroke:#F9A8D4,stroke-width:2px
    style BUSINESS fill:#F5F3FF,stroke:#A78BFA,stroke-width:2px

    linkStyle default stroke:#64748B,stroke-width:1.5px
```

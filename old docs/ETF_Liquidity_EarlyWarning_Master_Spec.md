# Master Specification: iNAV Deviation & Liquidity-Stress Early-Warning System for Indian ETFs

**Document purpose:** This is the single source of truth for the project. It is written to be handed to another AI system (or another engineer) with zero prior context, so that it can independently decompose the work into detailed phase-level specifications without needing to rediscover *why* the project exists, *what* data it runs on, or *what* "done" looks like. Nothing here should need to be inferred or re-derived from outside conversation.

**Status:** Pre-build / planning document. No code has been written yet. All data-availability claims below are based on desk research (public documentation, vendor pages, open-source scrapers, financial press) as of August 2026, not on verified hands-on access — see Section 9 for what still needs to be confirmed empirically before the build starts.

---

## 1. Executive Summary

**What we are building:** A system that ingests daily (and, in a later phase, intraday) pricing and net-asset-value data for a defined universe of Indian-listed ETFs, learns the normal statistical relationship between an ETF's exchange-traded market price and its underlying net asset value, and outputs a forward-looking, probabilistic forecast of abnormal premium/discount events — before they happen, using only information that would genuinely have been available at forecast time.

**Why it matters:** Indian ETFs — commodity ETFs especially — periodically trade at large premiums or discounts to their true asset value when the arbitrage mechanism that is supposed to keep price and NAV in line (Authorized Participants creating/redeeming units) can't keep pace with demand or physical-asset supply constraints. This is not a theoretical risk: in October–November 2025, several major Indian silver ETFs (Nippon India, HDFC, Tata, UTI) traded at 5–10%+ premiums to their indicative NAV during a physical-supply squeeze, some AMCs halted new subscriptions, and India's regulator (SEBI) is actively considering mandatory price bands for commodity ETFs as a direct policy response. Retail investors who bought during that premium lost money the moment it reverted — and had no data-driven way to know they should have waited.

**What "success" looks like:** A working, backtested model that (a) would have flagged elevated risk of a premium/discount event before the October 2025 silver episode using only pre-event data, (b) beats a simple statistical baseline on out-of-sample walk-forward evaluation, and (c) is packaged as a usable dashboard/alert system, not just a notebook with a metric in it.

---

## 2. The Real-World Problem (detailed)

### 2.1 Mechanics of the problem
An ETF's exchange-traded price is supposed to stay close to its Net Asset Value (NAV) because Authorized Participants (APs) can create new ETF units (by delivering the underlying basket to the AMC in exchange for units, which they then sell on the exchange when the ETF trades above NAV) or redeem units (the reverse, when the ETF trades below NAV). This creation/redemption arbitrage is the mechanism that keeps price and NAV converged. It breaks down when:
- The underlying asset is hard to source quickly (physical gold/silver during a supply squeeze — exactly what happened in Oct–Nov 2025).
- The ETF is thinly traded, so market-maker/AP economics don't justify tight quoting.
- Demand surges faster than APs can create units (a sudden retail buying wave, often driven by price momentum or a news/sentiment event).

### 2.2 Evidence this is a live, current, named problem (not hypothetical)
- **October–November 2025:** Nippon India's silver ETF — the largest in its category — closed at a 5.5% premium to its iNAV on a single day; ETFs from HDFC, Tata, and UTI MF saw premiums of 10%+. Several AMCs (e.g., Kotak) halted lump-sum and switch-in subscriptions into their silver ETF/FoF products in response.
- Nippon India's own head of commodities publicly attributed the premium to a "genuine demand–supply deficit" compounded by "festival season buying and restocking" — i.e., a demand-side, sentiment-driven surge, not a pure supply shock, which is directly relevant to why an alternative-data leading indicator (Section 10) is a sensible future extension.
- **SEBI is actively considering mandatory price bands for gold/silver ETFs** as a regulatory response to exactly this failure mode — reported in March 2026 press coverage in which Mirae Asset's own Head of ETF Product (Siddharth Srivastava) discussed the proposal directly, alongside commentary that gold/silver ETF inflows represented 54% of all ETF flows in a recent month, 2.5x active large-cap fund inflows.
- Mirae Asset filed offer documents to launch a silver ETF in India (alongside Aditya Birla Sun Life and Nippon India) in December 2021, so this product category is one Mirae itself has direct commercial exposure to.
- At the broader Mirae Asset Financial Group level, Mirae Asset Securities (USA) has publicly described acting as a Designated Liquidity Provider / Authorized Participant for ETFs, so liquidity provision and premium/discount management is a theme the wider Mirae ETF franchise already engages with commercially — this is useful context, not a claim that Mirae India runs this exact desk.

### 2.3 Who would use this and why
- **Product/risk teams at an ETF issuer:** to know when a fund is trading away from fair value and whether AP/liquidity intervention is warranted.
- **Distribution/advisory desks:** to avoid recommending a product mid-premium-spike, and to have a factual, data-backed talking point with clients/advisors.
- **Retail investors and advisors generally:** the underlying insight (don't buy an ETF at a large premium; it will likely revert) is directly actionable and easy to explain, which matters for the "commercial value" criterion — this is not an insight that only a quant desk could use.

---

## 3. Research Foundation and Gap (summary — full detail in the prior research document)

This project was selected after a structured comparison against several other AI/ETF project ideas (fund-flow lead-generation via graph neural networks, dynamic replication optimization, tracking-error causal decomposition, market-making reinforcement learning, generic price-direction prediction, HMM regime detection). It was chosen because it has the best combination of (a) genuine technical/research depth, (b) realistic data feasibility with India-accessible sources, and (c) a live, dated, named real-world event to validate against — which the alternatives either lacked or only partially satisfied. That comparative reasoning is documented in full in the companion document `Mirae_Asset_ETF_AI_Project_Research.md` and is not repeated here; this document assumes that decision as settled and focuses entirely on specifying the chosen project.

**What exists in the literature:**
- Substantial market-microstructure and econometric literature on ETF arbitrage efficiency, tracking error, and premium/discount behavior — but concentrated on **US and Chinese markets**, and largely **descriptive/econometric rather than predictive/ML-based**. Example: Dobson (2020), "ETFs tracking errors on global markets with consideration of regional diversity," MPRA 103695 — finds tracking errors differ significantly by region and market development, but does not build a forecasting model.
- ML-based **prediction** of arbitrage-related signals exists but is applied elsewhere: Zhang et al. (PMC9601484) use LASSO/XGBoost/BPNN/LSTM to forecast spot-futures arbitrage opportunities for the CSI 300 (China) — methodologically the closest precedent to what we're proposing, but a different market and a different instrument pair (index futures vs. ETF, not ETF price vs. ETF NAV).
- **India-specific coverage is almost entirely financial press, after the fact** (e.g., explaining why the October 2025 premium happened, not predicting it in advance). No published, backtested, India-specific predictive model for ETF premium/discount was found in this research.

**The gap this project fills:** a live, forward-looking, backtested early-warning model for Indian ETF price/NAV divergence — combining time-series/ML forecasting techniques that are well-established elsewhere with a market (India) and instrument class (physical commodity + thinly-traded thematic ETFs) that has not been studied this way before.

---

## 4. Scope Definition

### 4.1 In scope (the flagship system)
- A defined, fixed universe of Indian-listed ETFs (see Section 6.5) with daily price and NAV history.
- A **daily-frequency** premium/discount forecasting model (this is the achievable MVP grain — see Section 6.2 for why).
- An anomaly-detection layer to flag structural-break-type events that don't fit the learned "normal" pattern.
- A backtest that explicitly targets the October–November 2025 silver ETF premium episode as a named validation event.
- A user-facing output (dashboard and/or alert mechanism — see Section 8) that surfaces the forecast and the anomaly flag in an interpretable way.

### 4.2 Explicitly out of scope for the flagship (do not silently expand into these)
- **Trading/execution strategy.** This system predicts and flags; it does not place trades, size positions, or recommend a trading strategy. Turning a premium/discount forecast into a profitable arbitrage strategy is a materially harder, separate problem (it requires borrow costs, transaction costs, and creation/redemption unit-size constraints that retail-accessible data cannot fully capture) and is explicitly not a goal here.
- **Intraday, real-time iNAV modeling** — this is Tier 2 / stretch, not the MVP target. See Section 6.2 and Section 9 for why.
- **Creation/redemption-unit-level AP modeling.** This data is not publicly available in India (see Section 5.6). Any AP-behavior signal in the model is a proxy (trading volume, spread), not actual AP order-flow data.
- **The distribution/lead-generation project (Project 1) and the dynamic-replication/RL projects considered earlier.** Those are separate, independent project concepts and are not part of this system's scope, even as extensions.
- **Project 3 (alternative-data nowcasting)** is a planned future integration, not part of the core build. It is specified only at a high level in Section 10 so the downstream phase-planning AI knows where it will eventually plug in, but no phase should be created for it until the core system (Sections 5–9) is working end to end.

---

## 5. Data Specification

This is the most important section for downstream implementation planning. Every dataset below must be treated as a distinct ingestion source with its own access method, refresh cadence, and known limitations — do not collapse these into a vague "market data" bucket.

### 5.1 Data source overview table

| # | Dataset | Source | Frequency | Historical coverage | Access method | Cost |
|---|---|---|---|---|---|---|
| D1 | ETF exchange trading data (OHLC, volume, trades) | NSE (primary), BSE (secondary, for dual-listed/BSE-only ETFs) | Daily (bhavcopy) | NSE archives back to the 1990s for equities; ETF-specific listings only from each ETF's own listing date | NSE's public historical-reports portal (`nseindia.com`) bhavcopy files; BSE equivalent for BSE listings | Free |
| D2 | Official ETF/scheme NAV | AMFI (Association of Mutual Funds in India) | Daily (one NAV per scheme per trading day) | From April 2006 for the AMFI historical archive (ETFs will only have data from their own launch date) | AMFI's public `NAVAll.txt` daily file and historical NAV-history download endpoint (`amfiindia.com`) | Free |
| D3 | Indicative intraday NAV (iNAV) | Individual AMC/exchange real-time feeds | Continuous during market hours, but **disclosure frequency varies by ETF type** (see 5.3) | **Real-time only — no confirmed free historical archive** | AMC websites (e.g., Nippon India ETF site, Zerodha Fund House "iNAV Summary" page) and NSE/BSE real-time data feeds | Free to view live; historical archive likely requires a paid vendor or our own forward-collection (flagged as open dependency, Section 9) |
| D4 | Domestic gold/silver reference spot price | MCX (futures-based reference) and/or IBJA (India Bullion and Jewellers Association) daily spot fixing, and/or LBMA fixing (SEBI's silver ETF circular specifies LBMA benchmarking) | Daily | MCX and IBJA both maintain multi-year daily archives | MCX website / data vendor; IBJA daily rate publication; **the exact benchmark differs per ETF and must be confirmed from each ETF's Scheme Information Document (SID)** — do not assume one universal gold/silver price series applies to every fund | Free for daily reference rates; higher-frequency futures tick data may be paid |
| D5 | Monthly aggregate ETF/scheme flow data | AMFI monthly industry data releases | Monthly | Multi-year archive available via AMFI and financial press | AMFI website monthly release; corroborating figures from financial press (Business Standard, etc.) | Free |
| D6 | Macro/context calendar | Festivals (Diwali/Dhanteras — historically linked to gold/silver buying), SEBI circular dates, known AMC subscription-halt announcements | Irregular/event-based | Constructed manually from press coverage and public AMC announcements, not a licensed dataset | Manual curation, cross-checked against financial press (Business Standard, Economic Times, Mint) | Free (labor-intensive, not automatable) |
| D7 | Scheme metadata | AMFI scheme master data | Static, updated as schemes launch/change | Current + historical scheme master via AMFI | AMFI scheme master file (also mirrored by third-party aggregators) | Free |

### 5.2 D1 — NSE/BSE exchange trading data: exact fields needed

NSE's daily bhavcopy for the Capital Market (Equity) segment — ETFs are listed under the same "Equity" instrument type as regular shares in NSE's classification — contains, at minimum, per symbol per day:
`SYMBOL, SERIES, OPEN, HIGH, LOW, CLOSE, LAST, PREVCLOSE, TOTTRDQTY (total traded quantity), TOTTRDVAL (total traded value), TIMESTAMP, TOTALTRADES`.

For this project we specifically need, per ETF per trading day: **CLOSE** (used to compute the daily premium/discount against NAV), **TOTTRDQTY / TOTTRDVAL** (used as liquidity/volume features), **TOTALTRADES** (used as a secondary liquidity proxy), and **HIGH/LOW** (used to construct an intraday range feature as a rough volatility proxy, since true intraday tick data is not in scope for the MVP). BSE publishes an equivalent daily bhavcopy for BSE-listed ETFs. Existing open-source tooling (the R package `nser` and multiple PyPI packages) already implements bhavcopy retrieval and parsing, confirming this is a solved data-engineering problem rather than a research risk.

### 5.3 D2/D3 — NAV vs. iNAV: a distinction that must not be collapsed

This is the single most important data nuance in the entire specification, and it directly determines what the MVP can and cannot claim to predict.

- **Official end-of-day NAV (D2):** published once per trading day by the AMC via AMFI, computed from the closing prices/values of the fund's actual holdings. This is authoritative, free, and has deep historical coverage (back to each ETF's launch date, within AMFI's broader April-2006-onward archive).
- **Indicative intraday NAV / iNAV (D3):** a continuously-updated *estimate* of fair value published by the AMC/exchange throughout the trading day, used by traders to judge whether the current market price is at a premium or discount *right now*. Disclosure frequency is **not uniform across ETF types** — confirmed from AMC disclosures: domestic equity ETFs disclose iNAV continuously (roughly 15–30 second delay); **commodity ETFs (gold/silver) disclose iNAV only hourly between 10:00 a.m. and 3:00 p.m.**; debt ETFs disclose iNAV only 3 times a day; international ETFs disclose with a 15-second delay but only reflecting currency movement from the prior close. **No confirmed free source of historical iNAV time series was found during this research** — AMC pages (e.g., Zerodha Fund House's "iNAV Summary") appear to show live/current values only, not a downloadable historical archive.

**Consequence for scope:** the MVP target variable is defined at **end-of-day granularity**, using the officially published daily NAV, not the intraday iNAV:

> **MVP premium/discount definition:** `premium_t = (Close_price_t − Official_NAV_t) / Official_NAV_t`, computed once per trading day per ETF, using D1's `CLOSE` and D2's official NAV for the same trading date.

This is fully backtestable today using only free, historical, well-archived data. True intraday iNAV-deviation modeling (which would let the system say "premium is spiking *right now*, mid-session" rather than "premium was elevated *at yesterday's close*") is explicitly deferred — it requires either sourcing paid historical tick-level iNAV data from a market-data vendor, or standing up our own real-time capture pipeline from project start onward (meaning it could only ever be backtested on data collected after the pipeline exists, not retroactively on 2025's silver squeeze). This is flagged as an open dependency in Section 9, not silently assumed away.

### 5.4 D4 — Commodity reference price: per-fund verification required

Different gold/silver ETFs in India benchmark to different reference prices depending on their Scheme Information Document: some track an MCX-based domestic price series (e.g., SBI Gold ETF is described as tracking "MCX Gold (INR/10g)"), while SEBI's silver ETF operational circular specifies benchmarking against the **LBMA Silver daily spot fixing price**, and IBJA daily rates are also commonly referenced in the Indian bullion market. **Do not assume a single universal gold/silver price series applies across all ETFs in the universe** — each fund's actual benchmark must be read from its SID/factsheet during the data-engineering phase and mapped explicitly, fund by fund.

### 5.5 D5/D7 — AMFI flow and scheme metadata: exact fields

AMFI's daily `NAVAll.txt` file contains, per row: **Scheme Type, Fund Family (AMC name), Scheme Code, ISIN (Dividend Payout/Growth), ISIN (Dividend Reinvestment), Scheme Name, Net Asset Value, Date**. This same file/archive is the source for D2 above. AMFI's separate scheme-master data additionally carries category, sub-category, launch date, and plan/option flags, which are used to correctly identify which scheme codes correspond to which listed ETF ticker (a non-trivial mapping step — ETF tickers on NSE/BSE must be matched to AMFI scheme codes and ISINs, since the two systems use different identifiers natively). Multiple existing open-source scrapers (`mftool` Python package, several GitHub projects, and at least one free third-party API) already parse this file and handle historical retrieval, again confirming this is a data-engineering task, not a research risk.

### 5.6 What is explicitly NOT available (confirmed absence, not oversight)

- **Creation/redemption unit-level data** — India has no public equivalent of a 13F-style holder/AP disclosure. Any feature meant to proxy AP activity (e.g., sudden volume spikes, spread widening) is an indirect proxy, not ground-truth AP order flow, and must be labeled as such in all documentation and model cards produced downstream.
- **Free historical intraday iNAV** — see 5.3. Treated as an open dependency, not assumed solved.
- **Distributor/holder-level ownership data** — irrelevant to this project (relevant to the separate, out-of-scope Project 1) but noted here so it is not mistakenly assumed to exist for this system either.

### 5.7 ETF universe for the MVP (proposed, not final)

Priority order for inclusion, to be finalized once data availability is empirically confirmed per fund:
1. **All listed Indian gold ETFs** across major AMCs (e.g., Nippon India, SBI, HDFC, Kotak, and Mirae Asset's own gold ETF where confirmed live) — highest priority, since this category has the clearest premium/discount history and the most direct tie to the validating event.
2. **All listed Indian silver ETFs** (Nippon India, HDFC, Tata, UTI, Kotak, ICICI Prudential, and Mirae Asset's silver ETF where confirmed live) — the exact category involved in the October–November 2025 event; this is the primary validation set.
3. **A control group of 5–8 large, liquid, non-commodity ETFs** (e.g., broad Nifty 50/Nifty Bank ETFs) that are *not* expected to show large premium/discount events — included specifically so the model and the evaluation can demonstrate it isn't just learning "commodity ETFs are always volatile" but is genuinely picking up on the conditions that precede a divergence.
4. **A handful of thinly-traded thematic/sector ETFs** (e.g., from the Nifty India Internet / New Age Consumption / sector-fund category) as a secondary test of whether the model generalizes beyond commodities to genuinely illiquid equity ETFs, which is a distinct failure mode (thin trading, not physical-supply constraints) from the commodity case.

---

## 6. Target Variable and Prediction Task — Formal Definition

### 6.1 Primary target (MVP)
For each ETF *i* and trading day *t*:

`premium_i,t = (Close_i,t − NAV_i,t) / NAV_i,t`

The model's job is to forecast, using only information available up to and including day *t*, a **probability distribution** over `premium_i,t+1` (next trading day) — not a single point estimate. This is a deliberate design choice (justified in Section 7.3): a probabilistic forecast lets the system say "there's a 70% chance of a >3% premium tomorrow," which is what a risk desk or advisor actually needs, rather than a single number that hides the uncertainty.

### 6.2 Why daily, not intraday, for the MVP
Restated from Section 5.3 for clarity in this section: intraday iNAV history is not confirmed to be freely available, and even where AMCs disclose iNAV live, the disclosure frequency itself varies by ETF type (continuous for equity ETFs, only hourly for commodity ETFs). Building the MVP at daily/EOD grain avoids depending on an unconfirmed data source and still fully supports the headline validation goal (would the model have raised an alarm ahead of the October 2025 episode, using data available before it).

### 6.3 Secondary output: anomaly / structural-break flag
Independent of the probabilistic forecast, an unsupervised anomaly-detection layer flags days where the *realized* feature state (not just the premium itself) looks statistically unlike anything the model has seen in its training history. This exists because the biggest real events (like October 2025) are structural breaks — a supply shock is, by definition, something outside the recent training distribution — and a purely supervised forecasting model can be slow to react to genuinely novel conditions. The anomaly flag is a second, independent signal, not a replacement for the primary forecast.

### 6.4 What the system does *not* claim to predict
It does not predict the *magnitude and duration* of a premium event with high precision (that would require creation/redemption-unit data we don't have), and it does not predict *which specific day within a multi-week supply squeeze* will see the peak premium — it predicts *elevated risk* over the near-term horizon, which is the achievable and honestly-scoped claim given the available data.

---

## 7. System Architecture

### 7.1 High-level pipeline

```
[Data Ingestion Layer]
   D1 (NSE/BSE bhavcopy)  ─┐
   D2 (AMFI NAV)           ─┤
   D4 (Gold/Silver spot)   ─┼──▶ [Data Warehouse / Storage]
   D5 (AMFI flows)         ─┤          │
   D6 (Event calendar)     ─┘          ▼
                              [Feature Engineering Layer]
                                       │
                                       ▼
                    ┌──────────────────┴──────────────────┐
                    ▼                                      ▼
        [Baseline Model]                       [Core Forecasting Model]
   (rolling volatility threshold)         (quantile GBM / LSTM / TFT)
                    │                                      │
                    └──────────────────┬───────────────────┘
                                       ▼
                          [Anomaly Detection Layer]
                        (isolation forest / autoencoder)
                                       │
                                       ▼
                          [Evaluation & Backtest Engine]
                     (walk-forward, Oct-2025 stress test)
                                       │
                                       ▼
                      [Serving Layer: Dashboard + Alerts]
                                       ▲
                                       │
                    (future extension, Section 10)
                    [Alt-Data Nowcasting Module]
```

### 7.2 Module responsibilities

| Module | Responsibility | Why it's a separate module |
|---|---|---|
| Data Ingestion Layer | Scheduled retrieval and parsing of D1/D2/D4/D5, plus manual curation of D6; normalizes all sources to a common ETF-identifier and date key | Each source has a different native identifier system (NSE ticker vs. AMFI scheme code vs. ISIN) and different refresh cadence; isolating this logic means a broken scraper for one source doesn't take down the whole pipeline |
| Feature Engineering Layer | Computes the premium/discount target, rolling statistics, liquidity features, and joins the commodity/calendar context per ETF | Kept separate from modeling so the same feature set can feed both the baseline and the core model, and so features can be unit-tested independently of any model |
| Baseline Model | Simple rolling-volatility threshold rule (e.g., flag if today's premium exceeds N standard deviations of its own trailing 60-day premium history) | This is the explicit "what are we beating" reference — every result must be reported against this baseline, not in isolation, per the brief's emphasis on rigorous, comparative evaluation |
| Core Forecasting Model | Quantile-loss gradient boosting (LightGBM/XGBoost) as the primary candidate, with a sequence model (LSTM or Temporal Fusion Transformer) as a comparison architecture | Two model families are specified, not one, because with a modest labeled-event count (large premium events are rare by definition) a simpler tree-based quantile model may out-generalize a deeper sequence model — this is an empirical question to be settled during the build, not assumed in advance |
| Anomaly Detection Layer | Isolation forest or autoencoder reconstruction-error scoring on the full multivariate feature vector | Independent of the supervised forecast so it can catch conditions unlike anything in training history, which a supervised model trained only on historical premium levels cannot do by construction |
| Evaluation & Backtest Engine | Walk-forward backtesting, leakage/survivorship safeguards, the named October-2025 stress test | Deliberately structured as its own module (not just "a script that runs at the end") because validation rigor is a first-class deliverable of this project, not an afterthought |
| Serving Layer | Dashboard showing current forecast, anomaly flags, and historical model performance per ETF | This is what makes the project a "system" rather than a notebook — see Section 8 |

### 7.3 Key design-choice rationale

- **Quantile/probabilistic output, not point prediction:** a plain regression that outputs "expected premium = 0.8%" is far less useful to a risk desk than a distributional forecast that can say "there's a material chance this exceeds 3%." Quantile loss functions (pinball loss) directly optimize for this and are well-supported in both LightGBM/XGBoost and modern sequence architectures.
- **Two model families compared, not one chosen upfront:** given that large premium events are rare (a class-imbalance problem in disguise), a tree-based model on carefully engineered features may actually generalize better than a deep sequence model that needs more labeled examples of the rare event to learn from. The system should report both and let the evidence decide — this is itself a defensible, citable methodological choice for the eventual writeup.
- **Anomaly detection as a parallel, not sequential, layer:** if the anomaly detector fed into the forecaster (or vice versa) as a single pipeline, a genuinely novel event would be filtered through a model trained on the "normal" past and likely underweighted. Keeping them parallel and independently surfaced means the dashboard can show "the forecast model isn't worried, but the anomaly detector is flagging something unusual" — which is itself a meaningful and honest signal to show a user.
- **Baseline model is mandatory, not optional:** because the brief's evaluation criteria explicitly require demonstrating the system is "demonstrably better" than existing/naive approaches, the rolling-volatility threshold baseline must be implemented first and reported alongside every subsequent result.

---

## 8. Outputs and User-Facing Deliverable

### 8.1 What a user sees
- **Per-ETF forecast card:** current premium/discount level, the model's forecasted distribution for the next trading day (e.g., a simple probability bar: "12% chance of >2% premium, 3% chance of >5% premium"), and a plain-language risk label (Normal / Elevated / High).
- **Anomaly flag indicator:** a separate, clearly distinguished indicator showing whether current conditions are statistically unusual relative to the ETF's own history, independent of the forecast above.
- **Historical performance view:** for each ETF, a chart of realized premium/discount over time with the model's historical forecasts overlaid, so a user can visually audit "did this system actually work" rather than trusting a single aggregate accuracy number.
- **The October 2025 case study, presented explicitly:** a dedicated view showing what the model's forecast and anomaly flag would have shown in the days leading up to and during the silver ETF premium spike, using strictly point-in-time historical data. This is the single most important artifact for the eventual pitch/demo and should be treated as a first-class deliverable, not an incidental backtest chart.

### 8.2 Delivery mechanism
A lightweight dashboard (the specific technology choice — e.g., a Python-based dashboard framework vs. a simple static report — is left to the implementation phase, since it doesn't affect the modeling work and shouldn't be over-specified here) plus, optionally, a simple alerting mechanism (e.g., an email or message triggered when an ETF crosses into "Elevated" or "High" risk). The alerting piece is a nice-to-have polish item, not core to demonstrating the system works.

---

## 9. Assumptions, Dependencies, and Open Risks — Explicit List

This section exists so that nothing important is silently assumed. Each item below should be treated as a question to resolve empirically during the data-engineering phase, not as a settled fact.

| # | Assumption / Dependency | Status | Impact if it doesn't hold |
|---|---|---|---|
| A1 | NSE/BSE bhavcopy archives are accessible and parseable for the full historical window needed per ETF (from each ETF's listing date) | Likely true (multiple existing open-source tools confirm feasibility) but not yet hands-on verified for this specific project | Would require sourcing bhavcopy from a paid vendor for any gaps |
| A2 | AMFI NAV history is accessible and correctly matchable to each ETF's NSE/BSE ticker via ISIN/scheme-code mapping | Likely true, but the ISIN/ticker/scheme-code mapping step is non-trivial and must be built and validated carefully — a wrong mapping silently corrupts every downstream feature | If mapping is wrong for any fund, that fund's data must be excluded until fixed, not left in with bad joins |
| A3 | Historical intraday iNAV data is NOT freely available | Reasonably confirmed by this research (no free historical archive found; AMC pages show live values only) | Confirms the Section 6.2 decision to scope the MVP at daily grain; if this turns out to be wrong (a free archive is found during implementation), intraday scope could be revisited as a scope *increase*, not a blocker |
| A4 | The correct commodity benchmark price series per gold/silver ETF (MCX vs. LBMA vs. IBJA) must be read from each fund's SID individually | Confirmed as necessary by this research (funds are not uniform) | Using the wrong benchmark for a given fund would introduce a systematic feature error for that fund specifically |
| A5 | No public creation/redemption or AP order-flow data exists for Indian ETFs | Reasonably confirmed (no such disclosure regime was found, unlike the US) | Any AP-activity proxy in the model must be clearly labeled as a proxy (volume/spread-based), not treated as ground truth, in all model documentation |
| A6 | The number of genuinely large premium/discount events in the historical data (the "positive class" for practical purposes) will be small | Should be assumed true until measured — premium blowouts are, by nature, rare | May require the modeling phase to use techniques suited to rare-event/imbalanced forecasting (e.g., focal-loss variants, careful threshold selection) rather than standard regression evaluation alone; this should be revisited once the actual event count is known from the data |
| A7 | Mirae Asset's own gold/silver ETFs are live, listed, and have sufficient trading history to include in the universe | Not fully confirmed — Mirae filed to launch a silver ETF in Dec 2021, but current live status/AUM/listing history was not independently verified in this research | If not confirmed, Mirae's own funds may need to be excluded from the primary dataset and only referenced narratively in the pitch, without weakening the project (the October 2025 event involved other issuers' funds regardless) |

**Instruction to the downstream phase-planning AI:** Treat Section 9 as a mandatory checklist for the first (data-engineering) phase. No modeling phase should begin until A1–A5 are empirically confirmed or their fallback plans are activated.

---

## 10. Future Extension: Alternative-Data Nowcasting Module (Project 3) — Specified at High Level Only

**Do not expand this into a full build phase until the core system (Sections 5–9) is working end to end.** It is included here only so its eventual integration point is understood in advance.

**Intended role:** AMFI's official flow data is monthly and lagged; by the time an AMC sees retail gold/silver demand spiking in the official numbers, a premium event may already be underway or over. The nowcasting module is meant to give the core system an earlier warning by tracking retail attention/demand in near-real time.

**Planned inputs (not yet built):** Google Trends search-interest indices for gold/silver/ETF-buying-related queries, and financial-news headline sentiment scoring for Indian financial press. This has direct academic precedent — Chen, Chen, Lai & Yang (2023, *Review of Pacific Basin Financial Markets and Policies*) found Google Trends search-volume indices positively associated with fund inflows — and is a natural fit given that Nippon India's own commodities head attributed the October 2025 premium partly to "festival season buying," i.e., a demand-narrative-driven event, which is exactly what search/news attention data is suited to pick up ahead of official flow data.

**Integration point:** the nowcasting module's output would be added as an additional input feature to the Core Forecasting Model (Section 7, "Feature Engineering Layer" → "Core Forecasting Model"), not as a separate standalone system. When it is eventually built, the correct evaluation is an **ablation test**: does adding this feature measurably improve the walk-forward forecast accuracy versus the core system without it? A clean "yes, by this much" or "no, it didn't help" result is more valuable and more honest than simply asserting alternative data was used.

**Explicitly not yet resolved (do not assume answers when this phase eventually starts):** which specific search queries/keywords best proxy retail gold/silver ETF demand in an Indian context, what sentiment-scoring method to use on Indian financial press, and what mixed-frequency modeling technique (e.g., MIDAS-style regression, a dynamic factor model) best fuses a daily/weekly alt-data signal with the model's forecasting cadence. These are genuine open research questions for whenever this phase is picked up.

---

## 11. Deliverables and Definition of Done

### 11.1 Core system deliverables (what "complete" means for the flagship, excluding Section 10)
1. **A documented, reproducible data-ingestion pipeline** covering D1, D2, D4, D5 for the finalized ETF universe (Section 5.7), including the ISIN/ticker/scheme-code mapping logic (Assumption A2) and a data-quality report showing what date ranges are actually available per fund.
2. **A feature-engineering module** implementing the target-variable definition (Section 6.1) and the full feature set (liquidity, volatility-proxy, commodity-benchmark, calendar/seasonality features), unit-tested independently of any model.
3. **A working baseline model** (rolling-volatility threshold) with reported performance, as the mandatory comparison point for everything else.
4. **A working core forecasting model** (at minimum, the quantile gradient-boosting version; the sequence-model comparison is a stretch-within-the-core-scope, not mandatory for a first working version) producing the probabilistic next-day premium/discount forecast described in Section 6.1.
5. **A working anomaly-detection layer** producing the independent structural-break flag described in Section 6.3.
6. **A walk-forward backtest report**, including explicit leakage/look-ahead-bias and survivorship-bias safeguards (train strictly on data available before each forecast date; include delisted/matured schemes in the historical universe where feasible rather than only funds that are still trading today), with pinball loss and event-classification precision/recall reported against the mandatory baseline.
7. **The named October–November 2025 silver ETF stress-test case study**, run strictly on point-in-time data, presented as its own artifact (Section 8.1) — this is the single deliverable the eventual pitch will lean on most heavily, so it must be built to be explainable and visually presentable, not just a metric in a table.
8. **A dashboard/serving layer** (Section 8) that a non-technical viewer (e.g., in a pitch/demo setting) can look at and understand without narration.
9. **A written model card / documentation artifact** stating plainly what the system does and does not claim to predict (Section 6.4), which data sources it relies on, and which features are proxies rather than ground truth (per Assumption A5) — this is what separates a defensible research project from an overclaimed one.

### 11.2 Success criteria (what makes the project a success, not just "finished")
- The core model beats the rolling-volatility baseline on out-of-sample walk-forward evaluation on at least the primary metric (pinball loss and/or event precision/recall — exact thresholds to be set once baseline performance is known, not fabricated in advance).
- The October 2025 stress-test case study shows the model and/or the anomaly detector giving a materially elevated signal in the period before or during the event, using only data available at the time. (If this is *not* the result — i.e., the model would have missed it — that is itself an important, reportable finding, not a failure to hide; the brief explicitly values honest evaluation over forced success.)
- The system runs end-to-end (ingestion → features → forecast → dashboard) without manual intervention at each step, demonstrating this is a system, not a one-off analysis.
- Every claim made about the system's capability in any pitch/writeup is directly traceable to a specific evaluation result produced by this pipeline — no unverified or aspirational claims.

### 11.3 What the final end-to-end system is meant to achieve
A demonstrable, defensible, India-specific answer to the question "could this have warned us about the kind of event that just happened in the silver ETF market" — built on real, cited research precedent, real and specifically-identified public data sources, and evaluated with the same rigor (walk-forward validation, named baseline, explicit bias safeguards) that the brief's own evaluation criteria call for. The alternative-data module (Section 10) remains available as a well-specified, ready-to-scope future phase once the core system has proven itself.

---

## 12. Glossary (for downstream AI/engineer reference)

- **NAV (Net Asset Value):** the official, once-daily, per-unit value of an ETF's underlying holdings, published via AMFI.
- **iNAV (Indicative NAV):** a continuously-updated estimate of an ETF's fair value published during trading hours, used to judge real-time premium/discount; disclosure frequency varies by ETF type (Section 5.3).
- **Premium/Discount:** the percentage difference between an ETF's traded market price and its NAV/iNAV; positive = premium (trading above fair value), negative = discount.
- **Authorized Participant (AP):** an institution empowered to create or redeem ETF units directly with the AMC, which is the mechanism that normally keeps price and NAV aligned.
- **Creation/Redemption:** the process by which APs create new ETF units (delivering the underlying basket, receiving units to sell) or redeem units (the reverse), used to arbitrage away price/NAV gaps.
- **Bhavcopy:** NSE/BSE's standard daily end-of-day market data file format.
- **AMFI:** Association of Mutual Funds in India — the industry body that also operates the public NAV-reporting infrastructure for all Indian mutual fund schemes, including ETFs.
- **Walk-forward backtest:** an evaluation method where the model is trained only on data up to time T and tested strictly on data after T, repeated in a rolling fashion, to avoid look-ahead bias.
- **Pinball loss (quantile loss):** the loss function used to train and evaluate probabilistic/quantile forecasts, penalizing under- and over-prediction asymmetrically depending on the target quantile.

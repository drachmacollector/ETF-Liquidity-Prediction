# Master Specification: ETF Price-Band & Liquidity-Stress Early-Warning System for Indian ETFs

**Document purpose:** This is the single source of truth for the project. It is written to be handed to another AI system (or another engineer) with zero prior context, so that it can independently decompose the work into detailed phase-level specifications without needing to rediscover *why* the project exists, *what* data it runs on, or *what* "done" looks like.

**Status:** Pre-build / planning document. No code has been written yet.

**Revision note (this version):** This document supersedes an earlier draft. It was revised after fresh research surfaced a material regulatory change — **SEBI has finalized a full overhaul of ETF price-band mechanics, effective September 1, 2026** (six days from the date of this revision) — which changes what the system's primary target should be, not just a footnote. It was also revised to reflect current Mirae Asset product developments (India's first hybrid ETF, a new defence-sector ETF, confirmed live status of Mirae's own gold/silver ETFs). Every section below reflects the current state of the market as of **August 2026**, not the pre-reform framework. Where the earlier draft's reasoning still holds, it is kept; where facts changed the target, data, or scope, that is called out explicitly rather than silently patched.

---

## 1. Executive Summary

**What we are building:** A system that ingests daily (and, in a later phase, intraday/auction-level) pricing and net-asset-value data for a defined universe of Indian-listed ETFs, learns the statistical relationship between an ETF's exchange-traded market price and its underlying net asset value, and outputs two coupled, forward-looking, probabilistic signals:
1. **Premium/discount forecast** — the probability distribution of tomorrow's price deviation from NAV (the original core target).
2. **Band-breach / trading-halt risk forecast** — the probability that an ETF's price will approach or breach its **regulatory dynamic price band** the next trading day, triggering a cooling-off/halt cycle under SEBI's new framework (a new, regulation-driven target added in this revision — see Section 3).

**Why it matters, and why the timing is unusually good for this project:** Indian ETFs — commodity ETFs especially — have repeatedly traded at large premiums or discounts to fair value when the creation/redemption arbitrage mechanism can't keep pace with demand or physical-supply constraints (the October–November 2025 silver ETF episode remains the clearest evidence: several major silver ETFs traded 5–10%+ above iNAV, and some AMCs halted subscriptions). **SEBI's response to exactly this class of problem is now final, not proposed:** a circular issued June 15, 2026 replaces the old flat ±20% band (based on a stale two-day-old NAV) with **dynamic, asset-class-specific bands anchored to the previous day's closing price**, effective **September 1, 2026**. This means the project is being scoped at almost the exact moment the market structure it's studying is changing — which is a genuine opportunity (we can validate against a real historical crisis under the *old* rules, then be among the first to validate a model against the *new* rules as live data accumulates from September 2026 onward) and a genuine complication (pre-reform and post-reform data are not statistically the same regime, and the system must treat that honestly — see Section 9).

**What "success" looks like:** A working, backtested model that (a) would have flagged elevated risk ahead of the October 2025 silver episode using only pre-event, point-in-time data under the old regime, (b) beats a simple statistical baseline on out-of-sample walk-forward evaluation, (c) has a clearly specified, ready-to-run methodology for forecasting band-breach/halt risk under the new regime as soon as sufficient post-September-2026 data exists, and (d) is packaged as a usable dashboard, not just a notebook with a metric in it.

---

## 2. The Real-World Problem (detailed, current as of August 2026)

### 2.1 Mechanics of the problem
An ETF's exchange-traded price is supposed to stay close to its Net Asset Value (NAV) because Authorized Participants (APs) can create or redeem units, arbitraging away any gap. This breaks down when the underlying asset is hard to source quickly (physical gold/silver during a supply squeeze), the ETF is thinly traded, or demand surges faster than APs can create units.

### 2.2 Evidence this is a live problem — and that regulators have now acted on it

- **October–November 2025:** Nippon India's silver ETF closed at a 5.5% premium to iNAV on a single day; ETFs from HDFC, Tata, and UTI MF saw premiums of 10%+; several AMCs halted lump-sum and switch-in subscriptions into silver ETF/FoF products. Nippon India's own head of commodities publicly attributed this to a genuine demand–supply deficit compounded by festival-season buying.
- **June 15, 2026 — SEBI circular (effective September 1, 2026):** SEBI, acting on recommendations from its Secondary Market Advisory Committee and stakeholder consultation, finalized a complete overhaul of ETF price-band mechanics. This is no longer a "proposal under consideration" (as it was described in earlier reporting and in the prior version of this document) — **it is a finalized rule with a firm effective date.** The key changes, in full, because the downstream engineering and modeling depend on the exact mechanics:

| Aspect | Old rule (until Aug 31, 2026) | New rule (from Sept 1, 2026) |
|---|---|---|
| Base price for setting the day's trading band | Previous NAV from **two trading days prior (T-2)** | **Previous day's closing price (T-1)**, computed as the **last 30-minute Volume-Weighted Average Price (VWAP)**; if no trades in that window, the Last Traded Price; if no trades at all that day, the latest available NAV |
| Price band — Equity & Debt ETFs (excl. Overnight/Liquid) | Flat ±20% | **Dynamic, starting at ±10%**, which can flex up to ±20% after a cooling-off period |
| Price band — Overnight & Liquid ETFs | Flat ±20% | **Fixed ±5%**, with a revised close-out mechanism (close-out price = the higher of the highest price recorded up to the auction/close-out date, or 5% above the latest available closing price) |
| Price band — Commodity ETFs (Gold/Silver) | Flat ±20% | **Dynamic, starting at ±6%**, relaxed in stages after cooling-off periods; exchanges may relax further in exceptional circumstances involving extreme international commodity price movements, with market notice |
| Price discovery for Gold/Silver ETFs | Continuous trading only | **A mandatory pre-open call auction session** is added specifically for Commodity ETFs, to discover an equilibrium price before regular trading begins |
| Longer-term direction | — | SEBI has directed exchanges and AMCs to work toward using **T-1 closing NAV** (not just T-1 closing price) as the base price from **April 1, 2027**, once operational readiness allows |

- Separately, and specifically relevant to Mirae: Mirae Asset's own Head of ETF Product, Siddharth Srivastava, was on record in March 2026 (i.e., *before* this circular was finalized) discussing gold/silver ETF inflow dynamics and the then-proposed price-band changes — direct evidence Mirae's own product team was already tracking this exact issue.
- Mirae Asset Securities (USA), at the wider group level, has separately discussed acting as an Authorized Participant / Designated Liquidity Provider for ETFs — useful context that liquidity provision is a theme the broader Mirae ETF franchise engages with commercially.

### 2.3 What this means for the problem statement (important reframing from the earlier draft)
The earlier version of this document framed the problem purely as "forecast how far price will diverge from NAV." That is still valid and still the right MVP target (Section 6.1), but it is no longer the *only* important target. From September 1, 2026, an ETF that would have drifted to a 10% premium under the old rules will instead **hit a regulatory band and trigger a halt/cooling-off cycle** well before reaching that level (±6% for commodity ETFs, ±10%→±20% for equity/debt). The more operationally relevant question for a product/risk desk going forward is not just "how far will this drift" but **"will this ETF hit its band tomorrow, and if so, how many cooling-off stages will it likely take to find equilibrium."** Both targets are specified formally in Section 6.

---

## 3. Research Foundation and Gap (updated)

This project was selected after a structured comparison against several alternative AI/ETF project ideas (documented separately, not repeated here). The core research gap identified — a scarcity of India-specific, predictive (not just descriptive) modeling of ETF price/NAV divergence, versus richer literature on US/Chinese markets — still holds. **What's new in this revision is that the regulatory environment itself has moved from "a gap regulators might eventually address" to "a gap regulators have just addressed with a specific mechanism," which changes the research contribution on offer:** the project can now credibly ask, and attempt to answer, a question no existing published work has had the chance to study yet — *does a dynamic, VWAP-anchored price band with staged cooling-off actually contain a demand-driven premium event better than the old flat-band regime would have, and can the onset of such an event be forecast far enough ahead to be useful to a risk desk or advisor?* This is a genuinely novel, timely question, not a reproduction of existing work, and it is only askable because of the timing of this project relative to the regulatory change.

---

## 4. Scope Definition (updated)

### 4.1 In scope
- A defined universe of Indian-listed ETFs (Section 5.7, now updated with confirmed live tickers) with daily price and NAV history.
- **Two coupled forecasting targets** (Section 6): the original daily premium/discount forecast, and the new band-breach/cooling-off risk forecast introduced by the September 2026 reform.
- An anomaly-detection layer for structural-break-type events.
- Two backtests: (a) the October–November 2025 silver ETF episode, run strictly under the *old*-regime rules that were actually in force at the time; (b) a forward-looking validation plan for the *new*-regime band-breach target, to be run as live data accumulates from September 1, 2026 onward (explicitly **not** back-fittable, since the new mechanism did not exist before that date — see Section 9).
- A user-facing dashboard/alert output (Section 8).

### 4.2 Explicitly out of scope
- Trading/execution strategy — this system predicts and flags; it does not trade.
- True intraday, second-by-second iNAV modeling — still Tier 2/stretch; still constrained by the same lack-of-free-historical-archive issue identified in the earlier draft (Section 5.3).
- Creation/redemption-unit-level AP modeling — still not publicly available in India.
- **Overnight and Liquid ETFs** — these now sit under a materially different, simpler regime (fixed ±5% band, a different close-out mechanism) that isn't the kind of large, demand-driven divergence event this project is built to address. They are excluded from the primary ETF universe, not because the reform doesn't apply to them, but because their band mechanics and typical use case (cash-management, not directional/commodity exposure) make them a poor fit for this system's purpose.
- Project 1 (distribution/lead-generation) and Project 3 (alt-data nowcasting) remain separate/future, as before — Project 3's integration point is unchanged (Section 10).

---

## 5. Data Specification (updated: one new source, several refined)

### 5.1 Data source overview table (updated)

| # | Dataset | Source | Frequency | Historical coverage | Access method | Cost |
|---|---|---|---|---|---|---|
| D1 | ETF exchange trading data (OHLC, volume, trades) | NSE (primary), BSE (secondary) | Daily (bhavcopy) | From each ETF's own listing date | NSE/BSE public historical-reports portals | Free |
| D2 | Official ETF/scheme NAV | AMFI | Daily | From April 2006 (per-ETF from launch) | AMFI `NAVAll.txt` daily file + historical archive | Free |
| D3 | Indicative intraday NAV (iNAV) | AMC/exchange real-time feeds | Continuous, but frequency varies by ETF type | **Real-time only — no confirmed free historical archive** (unchanged from earlier draft) | AMC websites, NSE/BSE live feeds | Free live; historical likely paid/self-collected |
| D4 | Domestic gold/silver reference spot price | MCX / IBJA / LBMA-linked benchmark (varies by fund — see 5.4) | Daily | Multi-year | MCX/IBJA data; per-fund benchmark confirmed from SID | Free (daily reference) |
| D5 | Monthly aggregate ETF/scheme flow data | AMFI | Monthly | Multi-year | AMFI monthly release | Free |
| D6 | Macro/context calendar | Festival dates, SEBI circular dates, AMC subscription-halt announcements | Irregular | Manually curated | Financial press cross-checking | Free (manual) |
| D7 | Scheme metadata | AMFI scheme master | Static, updated as schemes change | Current + historical | AMFI scheme master file | Free |
| **D8 (new)** | **Gold/Silver ETF pre-open call auction data** — the equilibrium price and matched/unmatched quantity discovered in the new mandatory pre-open auction session for commodity ETFs | NSE/BSE (mechanism mandated by the June 2026 SEBI circular, live from Sept 1, 2026) | Daily, pre-market | **None before September 1, 2026 — this data source does not exist yet** | Expected via the same NSE/BSE market-data channels as D1, once the exchanges implement the mandated session; exact report format not yet published as of this document's writing | Presumed free, consistent with other bhavcopy-style data, but **unconfirmed** |

### 5.2–5.6 (unchanged from the earlier draft)
The detailed field-level specification for D1 (NSE/BSE bhavcopy fields), the NAV-vs-iNAV distinction (D2 vs D3) and its consequence for target-variable grain, the per-fund commodity-benchmark verification requirement (D4), and the AMFI `NAVAll.txt` field list (D2/D5/D7) all carry over unchanged from the prior version of this document and are not repeated here to avoid redundancy — the downstream engineering team should treat those sections as still authoritative. The one addition is D8 above, which is new specifically because of the September 2026 reform.

### 5.7 ETF universe for the MVP (updated with confirmed live tickers and new Mirae products)

1. **Gold ETFs**, across major AMCs including **Mirae Asset Gold ETF (ticker: GOLDETF)** — confirmed live, inception February 24, 2023, tracks the "Domestic price of Gold Index – INR – Benchmark TR Gross," ~₹3,117 Cr AUM as of April 2026 — alongside equivalents from Nippon India, SBI, HDFC, Kotak.
2. **Silver ETFs**, including **Mirae Asset Silver ETF (ticker: SILVRETF)** — confirmed live, inception June 14, 2023, tracks the "Domestic Price of Silver Index – INR – Benchmark TR Gross," 0.39% expense ratio — alongside Nippon India, HDFC, Tata, UTI, Kotak, ICICI Prudential. **This resolves an open item from the prior draft (previously flagged as "not independently verified"): both Mirae commodity ETFs are confirmed live with ~3 years of trading history each, sufficient for inclusion in the historical backtest.**
3. **A control group of 5–8 large, liquid, non-commodity ETFs** (broad Nifty 50/Nifty Bank ETFs), unchanged in purpose from the prior draft.
4. **A handful of thinly-traded thematic/sector ETFs**, now including a concrete, current Mirae example: the **Mirae Asset BSE India Defence ETF** (NFO opened February 2, 2026), which by the time this project's data-engineering phase begins will have roughly six-plus months of trading history — enough for illustrative inclusion, though likely still too little for robust standalone modeling; treat it as a secondary/qualitative case, not a primary training instrument, until more history accumulates.
5. **New: Mirae Asset's hybrid ETF, added as a forward-monitoring candidate, not a backtest instrument.** Mirae launched **India's first hybrid ETF** — the Mirae Asset Nifty200 Momentum 30 Plus 8–13 Yr G-Sec 50:50 ETF — with its NFO open July 10–22, 2026. This is a genuinely novel instrument class for this project to be aware of: it combines an equity sleeve (Nifty200 Momentum 30) and a government-bond sleeve (Nifty 8–13 Year G-Sec Index) inside a single ETF wrapper, which means its NAV computation and liquidity dynamics blend two asset classes with very different liquidity profiles. **This is explicitly out of the MVP backtest universe** — by the time this document was written the fund had at most a few weeks of trading history, far too little to model — but it should be added to the live data-ingestion pipeline (D1/D2) from day one of the build, so that by the time the system is operational it will have accumulated enough history to be a genuinely novel test case: **no existing research, in India or elsewhere, appears to study premium/discount behavior in a hybrid equity/G-Sec ETF, making this a strong candidate for a differentiated finding later in the project's life, without expanding the MVP's immediate scope.**

---

## 6. Target Variable and Prediction Task — Formal Definition (revised: two targets, not one)

### 6.1 Primary target A (unchanged core): daily premium/discount forecast
`premium_i,t = (Close_i,t − NAV_i,t) / NAV_i,t`, forecast as a probability distribution one trading day ahead, using daily-grain data (D1 close vs. D2 official NAV), for the reasons given in the prior draft (Section 5.3's NAV-vs-iNAV distinction still applies and is unchanged).

### 6.2 Primary target B (new, added in this revision): band-breach / cooling-off risk forecast
For each ETF *i*, on each trading day *t* from September 1, 2026 onward, define the applicable regulatory band `[Base_i,t × (1 − w), Base_i,t × (1 + w)]` where `Base_i,t` is the T-1 VWAP-derived base price defined in Section 2.2's table and `w` is the currently-applicable band width for that ETF's category (starting at 10% for equity/debt, 6% for commodity, subject to the staged relaxation rules). The model's second job is to forecast, one trading day ahead: **the probability that the ETF's traded price will approach or breach its current band, triggering a cooling-off/halt event.** This is a genuinely different prediction task from 6.1 — it is not simply "large premium," it is "large premium *relative to a regulator-defined, dynamically-updating threshold*," and it only becomes a meaningful, testable target once the new regime is live.

### 6.3 Why both targets are kept, not just the new one
Target A (raw premium/discount) remains valuable on its own: it applies to every ETF in the universe regardless of category, it's what the October 2025 case study can actually validate against (since the band mechanism didn't exist then), and it's a more informative continuous signal for a risk desk than a binary breach flag alone. Target B is the more operationally urgent one from September 2026 onward, but it is best understood as sitting on top of Target A's forecast (a large forecasted premium is the leading indicator; whether it crosses the current regulatory band is what determines whether it actually triggers a halt).

### 6.4 Secondary output: anomaly/structural-break flag
Unchanged in purpose from the prior draft — an unsupervised layer (isolation forest/autoencoder) flagging conditions unlike anything in the ETF's own training history, kept independent of both supervised targets above.

### 6.5 What the system does not claim to predict (unchanged, restated)
It does not predict exact magnitude/duration with high precision (no AP order-flow data), and — new caveat specific to this revision — **it cannot yet be validated on Target B using real historical outcomes**, because the mechanism it's forecasting (band breaches under the new dynamic system) has no track record before September 1, 2026. This is stated plainly, not glossed over — see Section 9.

---

## 7. System Architecture (mostly unchanged; two additions)

The overall pipeline structure (Data Ingestion → Feature Engineering → Baseline/Core Models → Anomaly Detection → Evaluation → Serving) carries over unchanged from the prior draft. Two additions specific to this revision:

1. **A new feature group: "regulatory state" features**, computed per ETF per day from Sept 1, 2026 onward — current applicable band width, distance of current price from the band edge (as a percentage), count of cooling-off stages already triggered in the current episode, and (once D8 exists) the pre-open auction price versus the previous close. These feed directly into Target B's model.
2. **A new architectural note: pre- and post-reform data must be treated as two statistical regimes, not one continuous series.** Any model trained on pooled pre/post-September-2026 data should include an explicit regime indicator feature (or, more conservatively, the two periods should be modeled/evaluated separately with the pre-reform period used only for Target A and the Oct-2025 case study, and the post-reform period reserved for Target B once enough of it exists). This is a direct consequence of the Section 9 regime-change risk and should not be treated as an implementation detail to be discovered later — it's a first-class design constraint.

The baseline model, the mandatory-comparison-point principle, the two-model-family comparison for the core forecaster, and the parallel (not sequential) anomaly-detection design all carry over unchanged, with their rationale from the prior draft still fully applicable to Target A; the same design principles (probabilistic output, mandatory baseline, honest reporting) apply to Target B once it becomes buildable.

---

## 8. Outputs and User-Facing Deliverable (updated)

The per-ETF forecast card (Section 8.1 in the prior draft) now shows **two risk indicators side by side** rather than one: the premium/discount forecast (Target A) and, for ETFs where the new regime is live and applicable, a **band-breach risk indicator** (Target B) — e.g., "currently 4.1% above base price; band limit is 6%; forecast probability of breaching tomorrow: X%." The October 2025 case study (Section 8.1) remains the flagship backtest artifact, now explicitly labeled as an **old-regime validation** so a viewer doesn't mistake it for evidence about how the new band system performs — that evidence doesn't exist yet and won't be manufactured.

---

## 9. Assumptions, Dependencies, and Open Risks — Explicit List (updated)

| # | Assumption / Dependency | Status | Impact if it doesn't hold |
|---|---|---|---|
| A1 | NSE/BSE bhavcopy archives accessible/parseable per ETF from listing date | Likely true, not yet hands-on verified | Would need a paid vendor for gaps |
| A2 | AMFI NAV history correctly matchable to NSE/BSE tickers via ISIN/scheme-code | Likely true; mapping step is non-trivial | Wrong mapping silently corrupts downstream features; must be validated, not assumed |
| A3 | Historical intraday iNAV is NOT freely available | Reasonably confirmed | Confirms daily-grain MVP scope for Target A |
| A4 | Correct commodity benchmark (MCX/IBJA/LBMA-linked) must be confirmed per fund from its SID | Confirmed as necessary; for Mirae's own funds specifically, the benchmark is named "Domestic price of Gold/Silver Index – INR – Benchmark TR Gross" per public fund-data pages, but the precise underlying methodology of that index should still be verified against Mirae's SID before use | Wrong benchmark introduces a systematic feature error for that fund |
| A5 | No public creation/redemption or AP order-flow data exists in India | Reasonably confirmed | AP-activity features must be labeled as proxies, not ground truth |
| A6 | Large premium/discount events are rare in the historical data | Assume true until measured | May require rare-event-aware modeling techniques |
| A7 | **(Resolved in this revision)** Mirae's own gold/silver ETFs are live and have sufficient history | **Confirmed** — GOLDETF (since Feb 2023) and SILVRETF (since Jun 2023) are both live, listed, with named benchmarks and current AUM figures | N/A — no longer an open risk |
| **A8 (new)** | **The exact reporting format and public availability of D8 (pre-open call auction data for commodity ETFs) is unconfirmed** — the mechanism is mandated by regulation but exchanges have not yet published (as of this document) the specific data-feed format that will carry it from September 1, 2026 | Open, must be confirmed once the mechanism goes live | If the auction data isn't published in a machine-readable, historically-archived form, Target B's model will need to rely on D1/D2/D3 proxies only, without the auction-price feature — this degrades but does not invalidate Target B |
| **A9 (new)** | **Pre-reform (before Sept 1, 2026) and post-reform (from Sept 1, 2026) data are different statistical regimes.** The October 2025 case study validates the model's ability to detect building demand-side pressure, but says nothing about how well the *new* band/cooling-off mechanism itself will perform, because that mechanism did not exist during that event | Confirmed as a structural fact, not a risk to be resolved — it is a permanent feature of the project's timeline | Target B cannot be backtested against real historical outcomes at project start; its validation plan (Section 4.1) is necessarily forward-looking and should be explicitly scoped as such in any pitch or writeup, not implied to already have results |
| **A10 (new)** | Mirae Asset's new hybrid ETF and defence ETF have too little trading history at project start to be part of the initial modeling dataset | Confirmed by launch dates (July 2026 and February 2026 respectively, relative to an August 2026 project start) | These are correctly scoped as forward-monitoring candidates only (Section 5.7); do not attempt to force early modeling results from insufficient history |

**Instruction to the downstream phase-planning AI:** A8 and A9 are the two most consequential new items in this revision. A9 in particular should shape how any phase plan sequences work: Target A (with the Oct-2025 backtest) can be fully built and validated now; Target B can be built now but can only be *validated against real outcomes* incrementally, as post-September-2026 data accumulates — plan the phases accordingly rather than promising a complete Target B validation on day one.

---

## 10. Future Extension: Alternative-Data Nowcasting Module (Project 3) — unchanged in role, restated briefly

No change to this module's specification from the prior draft: it remains a planned future integration (Google Trends + financial-news sentiment, fused via a nowcasting model, feeding into the Core Forecasting Model as an additional feature, evaluated via ablation), not part of the current build. Its motivating precedent (Chen, Chen, Lai & Yang 2023 on Google Trends and fund inflows) and its rationale (AMFI's flow data is monthly and lagged; retail gold/silver demand is narrative-driven) are unchanged. Do not expand this section into a build phase until Sections 5–9's core system is working end to end.

---

## 11. Deliverables and Definition of Done (updated to reflect two targets)

### 11.1 Core system deliverables
1. Documented, reproducible data-ingestion pipeline for D1, D2, D4, D5, D7 (unchanged), **plus a placeholder ingestion path for D8 that can be activated once its format is confirmed (A8)**.
2. Feature-engineering module implementing both Target A and the new "regulatory state" feature group for Target B (Section 7).
3. Working baseline model(s): the original rolling-volatility threshold for Target A, **plus a simple rule-based baseline for Target B** (e.g., "flag if yesterday's premium was within 1 percentage point of the current band edge") — both mandatory comparison points.
4. Working core forecasting model for Target A (quantile GBM, with sequence-model comparison as before).
5. A **specified, ready-to-run** modeling approach for Target B, built and testable in simulation/backtest-of-mechanism-logic now, with real-outcome validation explicitly deferred and scheduled to begin incrementally from September 1, 2026 (per A9 — do not claim a validated Target B model before real data exists).
6. Working anomaly-detection layer (unchanged).
7. Walk-forward backtest report for Target A with the mandatory leakage/survivorship safeguards (unchanged from prior draft).
8. **The October–November 2025 silver ETF case study, explicitly labeled as an old-regime validation of the underlying demand-pressure signal**, not as evidence about the new band mechanism.
9. Dashboard/serving layer showing both targets (Section 8).
10. A written model card documenting, plainly: what Target A and Target B each do and do not claim to predict, which data sources are confirmed versus still-open dependencies (A1–A10), and — specifically — that Target B's real-world validation is a forward, not backward, exercise as of this document's writing.

### 11.2 Success criteria (updated)
- Target A model beats its baseline on out-of-sample walk-forward evaluation (unchanged criterion).
- The October 2025 case study shows the model/anomaly detector giving an elevated signal ahead of or during the event, using only point-in-time data — and if it doesn't, that is reported as a finding, not hidden (unchanged principle).
- Target B's *mechanism logic* (band computation, cooling-off staging) is verifiably correct against the SEBI circular's specification (Section 2.2's table), independent of whether enough live data yet exists to fully validate its predictive accuracy — this is a testable, achievable success criterion even before September 2026 data accumulates.
- Every claim in any pitch/writeup is traceable to a specific evaluation result actually produced by this pipeline, and claims about Target B are explicitly dated/scoped to reflect how much post-reform data was actually available at the time the claim is made.

### 11.3 What the final end-to-end system is meant to achieve
The same core ambition as the prior draft — a demonstrable, defensible, India-specific early-warning capability for ETF price/NAV divergence — **now sharpened by being built at the exact moment India's regulatory framework for this problem changed.** The system's value proposition is no longer just "would this have warned us about October 2025" (still true and still the headline backtest) but also "is this ready to tell us, in near-real time from September 2026 onward, whether the new dynamic-band regime is actually working" — a question nobody has been able to ask yet, because the regime is six days old at the time of this document.

---

## 12. Glossary (updated with new regulatory terms)

- **NAV, iNAV, Premium/Discount, Authorized Participant, Creation/Redemption, Bhavcopy, AMFI, Walk-forward backtest, Pinball loss:** unchanged definitions from the prior draft.
- **Base price:** under the new SEBI framework, the reference price from which a given day's trading band is calculated — from September 1, 2026, this is the previous day's closing price (last-30-minute VWAP, or LTP, or latest NAV as fallbacks), replacing the old T-2 NAV method.
- **Dynamic price band:** a trading limit around the base price that can widen in stages (rather than being fixed) as an ETF's price moves — ±10%→±20% for equity/debt ETFs, ±6% with staged relaxation for commodity ETFs, under the new framework.
- **Cooling-off period:** the pause mechanism that occurs when an ETF's price approaches its current band, before the band is allowed to widen further — the specific duration/mechanics of these periods should be confirmed from SEBI's full circular text once available for implementation-level detail.
- **Pre-open call auction:** a new, mandatory pre-market order-matching session specifically for Gold/Silver ETFs (from September 1, 2026) intended to discover an equilibrium price before continuous trading begins — the source of the new D8 data.
- **VWAP (Volume-Weighted Average Price):** the average traded price over a given window, weighted by traded volume — used here specifically as "last 30-minute VWAP" for computing the next day's base price.

# ETF Arbitrage-Stress Early Warning System
## Research Document: Foundations, Problem, Evidence, Data, Feasibility and Rationale

| Field | Value |
|---|---|
| Document ID | RD-01 |
| Version | 1.1 (P01 corrections: Indian NAV basis before Apr 2026; data-source results) |
| Research as-of date | 17 November 2026 (IST) |
| Status | **Active: single source of truth for the "why" and "what"**. The "how" lives in [`docs/technical/`](../technical/). |
| Source proposals | [`docs/source/ETF Arbitrage-Stress Early Warning System.pdf`](../source/) (the proposal) and [`docs/source/ETF_Stress_Early_Warning_Brief.pdf`](../source/) (the one-page brief prepared for the Mirae Asset ETF team) |
| Supersedes | Everything in [`archive/`](../../archive/) |
| Change control | Edits after the first build phase begins must be logged in [`records/DECISIONS.md`](../../records/DECISIONS.md) and bump the minor version. |

### Evidence grading

Every factual claim that matters to the build carries a tag. Tags tell the reader how much to trust the claim and whether to re-check it before quoting it to anyone outside the project.

| Tag | Meaning | Required action before external use |
|---|---|---|
| **[V]** | Verified in this research pass against a primary or official source (regulator text, SEC/EDGAR filing, issuer filing, exchange circular) or against two or more independent credible reports quoting the primary source | None |
| **[R]** | Reported by credible financial press, aggregators or industry bodies; not confirmed from a primary source in this pass | Cite the outlet; re-check if a number is used |
| **[K]** | Established domain knowledge (well-known market structure, fund launch dates, textbook mechanics), not re-verified in this pass | Re-check dates and figures in P01/P03 |
| **[C]** | Carried forward from earlier project research (academic citations, figures), not re-verified | Re-verify before quoting |
| **[A]** | Assumption or inference by the author | Treat as a hypothesis; resolution path is listed in §13 |
| **[REC]** | Recommendation or design decision | Binding on the build unless changed through the decision log |

Open questions use IDs `OQ-xx` (register in §13 and live tracker in [`records/OPEN_QUESTIONS.md`](../../records/OPEN_QUESTIONS.md)). Assumptions use `AS-xx` (§14).

---

## Table of contents

1. Executive summary
2. ETF foundations: how the price is meant to stay close to NAV
3. How the arbitrage pipe breaks: a mechanism taxonomy
4. Measuring the gap correctly: NAV construction, clocks and the two-layer cost gap
5. The incident record: what happened, what was visible beforehand
6. Regulatory frameworks (US and India) and what they imply for the build
7. Mirae Asset context, users and business value
8. Literature and existing solutions; the gap this project fills
9. The data landscape
10. Feasibility assessment
11. Rationale for the chosen approach
12. Critical reassessment of the proposal and the brief
13. Open questions register
14. Assumptions register
15. Glossary
16. Source register

---

## 1. Executive summary

### 1.1 The problem in one paragraph

An exchange-traded fund (ETF) is designed to trade close to the value of what it holds (its net asset value, NAV). The mechanism that keeps it close is **arbitrage through creation and redemption**: specialised firms (Authorised Participants in the US, Market Makers in India) create new units when the ETF trades rich and redeem units when it trades cheap. That mechanism usually works so well that gaps stay inside a narrow band set by transaction costs. **Large, persistent gaps arise when the mechanism is blocked**: the fund cannot issue new units (registration limits, regulatory caps, sanctions), the basket cannot be sourced (a physical squeeze), the NAV is stale or uncertain (closed foreign markets, untraded bonds), or the local underlying market itself breaks away from the global one. These events forced subscription suspensions, investor advisories and reputational damage in the US (UNG 2009, USO 2020, bond ETFs in March 2020, Russia ETFs in 2022) and in India (silver ETFs in October 2025, international ETFs under the overseas-investment cap from 2022 onwards). Issuers today mostly see them after the fact.

### 1.2 The question the project answers

> **For each ETF, each trading day: what is the probability that a material, persistent dislocation between its market price and its NAV begins within the next 1 to 5 trading days; which part of the arbitrage pipe is under strain; and which past incident does the current pattern most resemble?**

### 1.3 The solution in brief [REC]

1. A **breakdown-onset forecaster**: a gradient-boosted tree classifier (LightGBM) trained on a pooled panel of US ETFs from 2004 onwards, producing a **calibrated probability** that a dislocation episode (defined objectively in §11.3 and in the System Specification) starts within the next 5 trading days.
2. A **root-cause explainer**: SHAP contributions grouped into mechanism families (creation constraint, stale NAV, underlying squeeze, liquidity drain, demand surge, market-wide stress), producing a root-cause tag per alert that is validated against hand-labelled incidents.
3. An **analogue finder**: a nearest-neighbour search over the pre-onset signatures of catalogued past incidents ("pattern resembles silver, Oct 2025"), restricted to incidents that were known at the time.
4. **Deterministic monitors** that need no machine learning but carry direct business value: current premium level, the SEC 2%/7-day disclosure counter, the SEBI direct-redemption counter (discount >1% for 7 days), and distance to the Indian price band.
5. A **daily ETF Stress Brief** and a small dashboard, generated from templates so every number traces to data.

The system is **built and validated on US ETFs**, where two decades of daily NAV, price and shares-outstanding data cover many stress episodes, and **then tested on Indian ETFs**, which the model never trains on. That transfer test is the scientific centre of the project.

### 1.4 What changed since the v1 project, and why

| v1 (archived) | Revised direction | Reason |
|---|---|---|
| Predict tomorrow's premium (quantile intervals) for Indian gold/silver ETFs | Predict the **onset of a breakdown** within 1–5 days, for any ETF | Daily premium noise is mostly timing artefacts and mean reversion. The business events are breakdowns, which are rarer, larger and longer-lasting. |
| India only, ~4 years of silver data, 1–2 events | **US first** (2004–2026, dozens of episodes), India as an out-of-sample transfer test | Too few Indian events to train and validate honestly. |
| Features: premium history, volume, metal volatility, peers | Features organised around **why arbitrage fails**: creation activity, capacity headroom, NAV staleness, liquidity, local-vs-global gaps | Precursors of breakdowns are mechanism-specific. |
| One number per ETF | Probability + **root-cause tag** + **closest past incident** + deterministic regulatory counters | The people who act (product, sales, compliance) need the "why" and a precedent. |

### 1.5 The most important corrections to the proposal

The proposal and the brief are directionally sound, but this research found several statements that would mislead the build if taken literally. §12 lists them in full. The five that matter most:

1. **SEC Rule 6c-11 does not cover the core commodity ETFs.** GLD, SLV, USO and UNG are grantor trusts or commodity pools, not 1940-Act investment companies, so the rule's 2%/7-day website disclosure does not apply to them. [K, OQ-01] The rule is still a good *template* for the label definition, but it is **not a ready-made label dataset**: the disclosures are website postings kept for one year, not an archive.
2. **"Premium exceeds 2% *or* 3× normal range" will fire constantly on calm ETFs.** For SPY, 3× normal range is a few basis points. The label must use the **larger** of an absolute floor and a relative threshold (§11.3).
3. **There is no free historical iNAV, bid/ask or order-book depth for India, and no free historical daily bid/ask for the US.** Spread must be estimated from daily open/high/low/close prices (EDGE estimator, §9.4); order-book depth and news attention are out of scope. [V/K]
4. **India has no public daily creation/redemption or units-outstanding data**, so the US "creation activity" signal cannot be used in the transfer model. The model that is transferred to India must use only features available in both markets (§9.6, §11.6).
5. **Since 1 April 2026 Indian gold and silver ETF NAVs use exchange-polled domestic spot prices** (SEBI circular of 26 Feb 2026) [V]. Before that, NAVs were based on the LBMA AM price converted to rupees plus duties [R]. So in October 2025 the domestic silver squeeze appeared as an *ETF premium to NAV*; the same squeeze today would sit *inside* NAV. Any Indian label that spans 1 April 2026 is measuring two different things unless both layers of the gap are tracked separately (§4.3).

### 1.6 What success looks like

Success is **useful lead time at a tolerable false-alarm rate, measured against simple baselines, on data the model never saw**. Concretely (numeric gates are frozen in the pre-registration in phase P11):

- On the US lockbox period (1 Jan 2020 – latest), the model beats the best baseline on precision–recall AUC and Brier skill, with bootstrap confidence intervals that exclude zero improvement.
- At the pre-registered alert budget, it warns ahead of a meaningful share of episode onsets, with median lead time ≥ 1 trading day.
- On Indian ETFs, the transferred model shows skill above Indian baselines, or the project explains plainly why it does not.
- Root-cause tags agree with hand-labelled mechanisms well above chance.

A negative result on any of these is a legitimate, reportable outcome. The project is a research prototype, **not investment advice and not a trading system**.

---

## 2. ETF foundations: how the price is meant to stay close to NAV

### 2.1 Two markets for one product

| | Primary market | Secondary market |
|---|---|---|
| Who | Authorised Participants (US) / Market Makers and large investors (India) | Everyone (retail, advisors, institutions) |
| What | Create or redeem units **directly with the fund**, in large blocks (creation units), in exchange for the underlying basket and/or cash | Buy and sell existing units **on the exchange** |
| Price | NAV (plus fees) | Whatever the market sets |
| Effect on units outstanding | Changes it | No change |

**The arbitrage loop.** If the ETF trades above NAV by more than the cost of creating units, an AP buys the basket, delivers it to the fund, receives new units and sells them on the exchange. That selling pushes the price down towards NAV, and units outstanding rise. If the ETF trades below NAV, the AP buys units cheaply, redeems them for the basket and sells the basket; units outstanding fall. [K]

### 2.2 The no-arbitrage band

Arbitrage is not free. The gap between price and NAV can wander inside a band whose width is set by:

- the ETF's bid–ask spread and market impact;
- the cost of trading the underlying basket (spreads in the underlying, which can be large for corporate bonds or physical metal);
- creation/redemption fees (fixed per order, or variable);
- financing and settlement mismatch (holding inventory for one or more days);
- **timing risk** when the underlying market is closed while the ETF trades.

Petajisto (2017) found that US ETF premiums typically fluctuate within a band of roughly 100–200 bps for funds with illiquid or international holdings and much less for liquid domestic equity funds. [C] The project therefore never treats a small premium as a problem. It cares about gaps that **exceed the ETF's own normal band and persist**, which is what a blocked pipe produces.

**Design consequence [REC]:** rather than building the arbitrage-cost band bottom-up (creation fees and physical sourcing costs are mostly not public), the system estimates each ETF's **empirical no-arbitrage band** from its own calm-period premium distribution (robust centre and scale). A bottom-up cost estimate is computed only where the inputs exist, as a cross-check (P08).

### 2.3 Three prices, three clocks

| Price | Who produces it | When | Notes |
|---|---|---|---|
| Market price | Exchange trading | Continuous trading hours | US: official closing price (closing auction) at 16:00 ET. India: NSE closing price is the volume-weighted average of the last 30 minutes of trading [K, OQ-02]. |
| NAV | Fund administrator, once per business day | Struck at a fund-specific valuation time | US equity/bond funds: usually 16:00 ET. GLD: LBMA Gold Price PM (15:00 London). SLV: LBMA Silver Price (12:00 London). Futures funds (USO/UNG): futures settlement prices (~14:30 ET). India gold/silver ETFs since 1 Apr 2026: exchange-polled domestic spot. [K/V] |
| iNAV / IIV | Calculation agent, intraday | Every 15 seconds (US); per scheme (India) | Indicative only. **No free history** in India [R]. Not used as a model input. |

When the NAV clock differs from the market-price clock, part of the measured premium is simply **information that arrived between the two clocks**. Example: GLD's NAV uses the London afternoon price; if gold rallies 2% in New York trading after 15:00 London, GLD closes about 2% "above NAV" without any arbitrage failure. That apparent premium reverses the next day, when the new NAV catches up. This is the single most common source of false dislocations in daily data, and §4 and §11.3 explain how the build neutralises it.

### 2.4 Why gaps are normally small, and why that matters for modelling

For most ETF-days the gap is tiny and mean-reverting. Dislocation episodes are **rare events** (the expected positive rate for a 5-day onset target is in the low single-digit percent of ETF-days or below [A, AS-03]). This shapes the whole evaluation design: accuracy is meaningless, precision–recall and calibration are what matter, and confidence intervals must be wide and honest.

### 2.5 US and Indian structures compared

| Aspect | United States | India |
|---|---|---|
| Legal form | Most ETFs: open-end funds or UITs under the Investment Company Act 1940. Commodity ETPs (GLD, SLV, USO, UNG): grantor trusts or commodity pools registered under the Securities Act 1933 only. [K] | Open-ended mutual fund schemes listed on NSE/BSE, under the SEBI (Mutual Funds) Regulations 2026 (effective 1 Apr 2026). [V via v1 research] |
| Primary-market agents | Authorised Participants | Market Makers (at least two per ETF) and investors dealing above ₹25 crore directly with the AMC [V via SIDs] |
| Public creation data | Daily shares outstanding published by issuers; creations can be inferred from changes [K] | **No daily public units outstanding** [A, strongly supported]; monthly scheme AUM from AMFI |
| Premium disclosure | Rule 6c-11 ETFs: daily premium/discount, history, median spread, 2%/7-day statement [V] | iNAV disclosure; no standard historical premium disclosure |
| Investor protection trigger | Disclosure only | **Direct redemption with the AMC** allowed if the ETF closes >1% below NAV for 7 consecutive trading days, has no quotes for 3 days, or the bid size is below half a creation unit averaged over 7 days [V via AMC disclosures quoting the SEBI master circular] |
| Price limits | Intraday Limit Up–Limit Down pauses; no daily band | Daily price bands; new dynamic framework from 7 Sep 2026 (±6% initial for gold/silver ETFs, flexing in 3% steps, uncapped) [V via v1 research] |

---

## 3. How the arbitrage pipe breaks: a mechanism taxonomy

Every large incident in §5 traces back to a small number of mechanisms. The system's root-cause tags are built on this taxonomy, so it is defined precisely here.

| Code | Mechanism | What breaks | Typical direction | Typical persistence | Observable precursors in daily public data | Root-cause tag used by the system |
|---|---|---|---|---|---|---|
| **M1** | **Creation blocked by capacity** (registered-share exhaustion, regulatory investment caps, position limits, sanctions) | AP cannot create new units, so a premium cannot be arbitraged away | Premium | Days to years | Rapid unit growth (US shares outstanding); registered-share headroom falling (SEC filings); fund holdings approaching position limits; industry cap utilisation (India, not public daily); a suspension notice | `CREATION_CONSTRAINT` |
| **M2** | **Basket cannot be sourced** (physical squeeze) | Creation is legally open but physically impractical | Premium | Days to weeks | Local-vs-global premium widening; lease rates; surging volume and turnover; peer ETFs in the same metal also rich | `UNDERLYING_SQUEEZE` |
| **M3** | **NAV stale or uncertain** (underlying market closed; underlying assets not trading; valuation at a different clock) | NAV no longer reflects tradable value; the ETF becomes the price-discovery venue | Either; discounts in sell-offs | Days to weeks | Underlying-market closures (scheduled or unscheduled); credit-spread spikes; ETF return diverging from NAV return; volatility spikes | `STALE_NAV` |
| **M4** | **Local underlying dislocated from global** (Layer 1) | The underlying itself trades at a local premium (import constraints, duty changes, local shortage) | Premium (India) | Days to months | Domestic spot vs import parity widening; duty or import-policy changes; festival demand | `UNDERLYING_SQUEEZE` (with Layer-1 detail) |
| **M5** | **Liquidity drain** (market makers withdraw or widen) | Arbitrage capital is unavailable or too costly | Either | Hours to days | Estimated spread widening; falling depth proxies; low volume; high intraday range | `LIQUIDITY_DRAIN` |
| **M6** | **Demand surge** (one-sided retail chase) | Demand arrives faster than primary-market capacity can respond | Premium | Days | Volume and turnover surges; unit creation at record pace; media attention | `DEMAND_SURGE` |
| **M7** | **Trading frictions** (price bands, circuit locks, halts) | The price cannot move to fair value | Either | Hours to days | Volatility regime relative to band width; prior-day moves near band edges | `MARKET_STRUCTURE` (monitor only) |
| **M8** | **Market-wide stress** (systemic risk-off) | Amplifies M3 and M5 across many ETFs at once | Discount | Days | VIX, credit spreads, FX moves | `MARKET_WIDE_STRESS` |

Three points from this taxonomy drive the design.

1. **Not every measured gap is a broken pipe.** Clock mismatch (a special case of M3 that happens every day for GLD, SLV and international ETFs) produces apparent gaps that reverse the next day. The label must require **persistence** and the evaluation must separately report how many alerts were timing artefacts (§11.3).
2. **Mechanisms differ in what can be seen beforehand.** M1 and M2 build over days (unit growth, local premium), so they are plausibly forecastable. M3 triggered by a sudden market closure (Egypt 2011, Russia 2022) can be forecast only once the closure begins, so the gain there is in forecasting *persistence and escalation*, not the first day. The evaluation reports results by mechanism for this reason.
3. **Some mechanisms are invisible in public daily data before the event.** India's overseas-investment cap utilisation is not published daily (OQ-12). The system can only use the public suspension notices (with the date they became known) and the behaviour of the price.

---

## 4. Measuring the gap correctly: NAV construction, clocks and the two-layer cost gap

### 4.1 How NAV is constructed, by ETF type

| ETF type | Examples | NAV price source and clock | Consequence for daily premium |
|---|---|---|---|
| Physical gold (US) | GLD, IAU | LBMA Gold Price PM, 15:00 London (≈10:00–11:00 ET) [K] | ~5–6 hours of gold trading between NAV strike and ETF close; large apparent premia on volatile days |
| Physical silver (US) | SLV, SIVR | LBMA Silver Price, 12:00 London [K] | Same, larger because silver is more volatile |
| Futures-based commodity (US) | USO, UNG, BNO, DBC | Futures settlement prices (~14:30 ET for NYMEX energy) [K] | 90-minute gap; small timing noise |
| Investment-grade / high-yield bonds | LQD, HYG, JNK | Vendor-evaluated bid prices at ~16:00 ET; many bonds do not trade daily [K/V] | In stress, NAV lags the market; the ETF shows a discount that is really a stale NAV (March 2020) |
| International equity | EWJ, EWH, FXI, EGPT, GREK, RSX | Local closing prices (possibly fair-valued) [K] | Timing gap of many hours; closures make NAV completely stale |
| Domestic equity (controls) | SPY, IVV, QQQ | 16:00 ET closing prices [K] | Gaps of a few basis points |
| Indian gold/silver ETFs (until 31 Mar 2026) | GOLDBEES, SILVERBEES, Mirae `GOLDETF`, `SILVERAG` | LBMA AM fixing, converted to rupees, plus transport, customs duty, taxes and levies, and a *notional premium or discount* (per scheme documents: the premium usually charged for delivery of metal to where it is stored) [V: SEBI circular 26 Feb 2026 para 1; Mirae Silver ETF SID] | The domestic **squeeze** premium sat largely *outside* NAV (only a small notional delivery premium was inside), so it showed up as an ETF premium (Oct 2025) |
| Indian gold/silver ETFs (from 1 Apr 2026) | same | **Polled spot prices from recognised exchanges used to settle physically delivered derivatives (currently MCX; BSE also mentioned)**, under an AMFI uniform policy [V: SEBI circular HO/(68)2026-IMD-POD-2/I/5780/2026, 26 Feb 2026, per multiple reports] | Domestic premium now sits *inside* NAV; the ETF premium measures only exchange-level arbitrage friction |
| Indian international ETFs | Mirae `MAFANG`, `MASPTOP50`, Hang Seng TECH ETF; Motilal `MON100` | Overseas closing prices of the previous day [K] | Structural premium under the overseas cap plus a timing gap |

### 4.2 Three ways the build neutralises clock mismatch [REC]

1. **Persistence in the label.** A real breakdown persists for days; a timing artefact reverses when the next NAV is struck. Requiring at least 3 consecutive dislocation days (with at most one gap day) removes most artefacts.
2. **A forward-NAV robustness check in the label module.** Labels may use future information (features may not). For each candidate dislocation day the label module also computes the gap against the *next* NAV adjusted by the underlying move; episodes that vanish under this adjustment are flagged `timing_suspect` and reported separately. This is a robustness check, not the primary label (P09).
3. **Timing features.** The model is told how much the underlying moved between the NAV strike and the ETF close (where a proxy exists), whether the underlying market was closed, and how much the ETF's return has diverged from its NAV return recently.

### 4.3 The two-layer cost gap (India and commodity ETFs) [REC]

The investor buying an Indian silver ETF pays a total gap over the global price that has two layers with different causes, owners and fixes.

```
Global price (LBMA / COMEX, USD)
   × USD/INR × (1 + import duties)
          = Import parity (fair local price)
                 │  Layer 1: local-market premium  (physical supply, duties, import policy)
                 ▼
Domestic spot (MCX polled spot; IBJA)            ← basis of NAV since 1 Apr 2026
                 │  Layer 2: ETF premium to NAV  (arbitrage friction: creation, liquidity, bands)
                 ▼
ETF market price (what the investor pays)
```

Definitions used throughout the project (full formulas in the System Specification §4):

- **Layer 1, local-market premium**: `LP_t = D_t / (G_t × FX_t × (1 + duty_t)) − 1`, where `D` is the domestic spot price, `G` the global price in USD, `FX` USD/INR, and `duty` the effective import duty rate in force on day t.
- **Layer 2, ETF premium**: `prem_t = P_t / NAV_t − 1`.
- **Total investor gap vs global parity**: `TG_t = (1 + prem_t)(1 + LP^NAV_t) − 1`, where `LP^NAV_t` is the Layer-1 premium embedded in NAV. Before 1 Apr 2026 `LP^NAV` was a small, slow-moving notional delivery premium (NAV ≈ import parity + notional premium; estimated empirically in P08); after that date `LP^NAV ≈ LP_t`.

**Why this matters.** In October 2025 the domestic silver premium rose from about 0.5% in early September to 5.7% on 9 October (intraday peaks near 12%) according to Kotak Mutual Fund [R]. Because NAV was then based on import parity plus only a small notional delivery premium, silver ETFs showed 5–10% premiums to NAV. If the same squeeze happened today, NAV would rise with domestic spot, and the ETF premium to NAV could stay small while investors still overpay versus the global price. A model trained on "ETF premium to NAV" alone would see a structural break on 1 April 2026. The project therefore:

- tracks Layer 1, Layer 2 and the total gap separately for Indian commodity ETFs;
- defines the Indian label on Layer 2 (the arbitrage-friction gap, comparable with US ETFs), and reports Layer-1 episodes as a separate, deterministic monitor;
- treats 1 April 2026 as a documented measurement break in all Indian evaluations (P15).

**Duty is time-varying and must come from a dated table.** India's gold and silver import duty was cut to 6% (5% basic customs duty + 1% AIDC) in July 2024 [K]. Reports conflict on whether the February 2026 Budget changed it, and one report mentions a further revision in May 2026 [R, conflicting]. The duty table is therefore a hand-verified reference table with effective dates and sources (OQ-15, MI-09).

### 4.4 The US analogue of Layer 1

US commodity ETFs have a similar two-layer structure in a few episodes. In March 2020, COVID-19 logistics disruptions pushed COMEX gold futures far above London spot (the "EFP" spread blew out) [K]. GLD's NAV uses the London price while GLD trades in New York, so a Layer-1-type gap appeared in GLD's premium. The analogue matters for the transfer test because it gives the US training set at least some examples of local-vs-global dislocation.

---

## 5. The incident record

This section is the factual basis for the incident catalogue (built in phase P03). Each case lists what happened, the mechanism, the magnitude, **what was observable beforehand in daily public data** (the hypotheses the features encode), and the evidence grade. Figures are approximate unless graded [V].

### 5.1 United States

#### U1. United States Natural Gas Fund (UNG), July–September 2009: registered-share exhaustion

- **What happened.** On 6 July 2009 UNG disclosed that only 32.1 million registered units remained; by 7 July all were issued and UNG suspended new creation baskets until a new registration became effective. Redemptions continued. [V: UNG Form 8-K filings, July 2009]
- **Magnitude.** The premium rose within days of the suspension and peaked at about 19% on 28 August 2009. [R: etf.com]
- **Resolution.** The SEC registration of additional units came in August; UNG's own 8-K of 12 August said creations would not resume immediately; creations resumed on 28 September 2009, with conditions. [V: UNG 8-K] Concerns about CFTC position limits on natural gas futures were part of the background. [K]
- **Mechanism.** M1 (capacity: registered shares), with M6 (strong demand for a beaten-down commodity).
- **Precursors.** Rapid growth in units outstanding in the preceding months; the fund's own disclosure of remaining registered units; the pending S-3 registration. The premium itself was small *before* the suspension.
- **Lesson for the build.** The best predictor is **capacity headroom**, which is public in SEC filings but not in price data. Capacity events need a hand-built table (P03) with `known_at` dates.

#### U2. VelocityShares Daily 2x VIX Short-Term ETN (TVIX), February–March 2012: issuance suspended (ETN analogue)

- **What happened.** Credit Suisse suspended new issuance of TVIX notes in February 2012; the notes traded at a premium of up to roughly 89% to indicative value before collapsing when issuance resumed in March. [K]
- **Mechanism.** M1. **Why it is in the catalogue but not the training set:** TVIX is an exchange-traded *note* (an unsecured debt instrument), not a fund, and its indicative values are not available as clean NAV history. It is kept as an **analogue reference** only.

#### U3. Market Vectors Egypt Index ETF (EGPT), January–March 2011: underlying market closed

- **What happened.** The Egyptian Exchange closed from late January to late March 2011 during the revolution. EGPT kept trading in New York, becoming the only price-discovery venue for Egyptian equities, while its NAV relied on stale or fair-valued prices. [K]
- **Mechanism.** M3 (NAV stale because the underlying market was closed).
- **Precursors.** Political turmoil (not in our features); the closure itself is the trigger. Forecastable component: once the closure begins, the dislocation persists and grows.
- **Data caveat.** VanEck's historical NAV for EGPT must be confirmed (P01).

#### U4. June 2013 "taper tantrum": municipal and emerging-market bond ETFs

- **What happened.** Following Federal Reserve tapering signals, bond ETFs (municipal, high-yield, emerging-market debt) traded at unusual discounts to NAV for several days in late June 2013. [K]
- **Mechanism.** M3 (stale or evaluated bond prices) with M5 and M8.
- **Precursors.** Rapid rises in Treasury yields and credit spreads; outflows (falling shares outstanding).

#### U5. Global X MSCI Greece ETF (GREK), June–August 2015: underlying market closed

- **What happened.** The Athens Exchange closed from 29 June to 3 August 2015 under capital controls. GREK continued trading in the US against a stale NAV. [K]
- **Mechanism.** M3. **Precursors.** Bailout-negotiation stress, bank-deposit outflows (not in features); market-wide and FX stress partly visible.

#### U6. China A-share ETFs, July 2015: trading suspensions in the underlying

- **What happened.** During the 2015 Chinese equity crash, roughly half of A-share stocks suspended trading. US-listed A-share ETFs (e.g., ASHR) had NAVs built partly from suspended stocks' last prices, while the ETFs traded freely. [K]
- **Mechanism.** M3. **Lesson.** NAV staleness can be partial (a fraction of holdings), which daily data can only proxy.

#### U7. March 2020 COVID-19 bond-market stress

- **What happened.** Corporate bond ETFs traded at large discounts to NAV. LQD closed at about a 5% discount on the peak days (MSCI reports 5.08% on 19 March; MarketsMedia reports about 5% on 11–12 March). [R, consistent across sources] S&P Global reported that more than half of LQD's bonds by par value did not trade on a given day in March. [R] BIS Bulletin No. 6 (Aramonte and Avalos, 14 April 2020) used ETF discounts as a cue to corporate-bond distress, arguing ETF prices incorporated information faster than NAVs. [V as to the bulletin's existence and subject]
- **Mechanism.** M3 (stale evaluated bond prices) + M5 + M8. Many analysts argue the *ETF* price was the more accurate one; the "dislocation" reflected NAV staleness.
- **Lesson.** Discounts in bond ETFs during stress are partly measurement. The root-cause tag must be able to say `STALE_NAV`, and the business message differs ("the NAV is stale" vs "the ETF is cheap").
- **US Layer-1 analogue.** The same month, the COMEX–London gold spread widened sharply (§4.4). [K]

#### U8. United States Oil Fund (USO), April 2020: registered-share exhaustion during negative oil prices

- **What happened.** During the April 2020 oil collapse (front-month WTI settled below zero on 20 April), USO saw heavy inflows, exhausted its registered shares and suspended sales of creation baskets. [V: USO Form 10-K for FY2020]
- **Magnitude.** On 21 April 2020 the market price of USO was **36% above** its end-of-day NAV; by 22 April the premium had narrowed to 8.66%, and from 23 April it continued to decline, to 1.45% on 1 May 2020. [V: USO Form 10-Q (June 2020) and Form S-3/A]
- **Duration.** USO's later filings describe the premium as short-lived. [V: USO 10-K FY2024]
- **Other relevant facts.** USO changed its portfolio composition (moving away from the front month) and carried out a **1-for-8 reverse split** at the end of April 2020. [K] The split falls inside the event window and is a data trap (P07).
- **Mechanism.** M1 + M6, with futures-market stress (extreme contango, position-limit and accountability-level pressure). [K]
- **Precursors.** Record unit creations in March–April; extreme contango in WTI futures (front vs second month); USO's share of front-month open interest; the S-3 registration filing.

#### U9. iShares Silver Trust (SLV), February 2021: the "silver squeeze"

- **What happened.** Retail social-media buying drove record SLV inflows in late January and early February 2021. iShares amended SLV's prospectus in early February to warn that authorised participants might not be able to acquire enough silver, which could restrict creations and lead to wide premiums or discounts. [R: ETFstream and others; the filing date is reported as 3 or 8 February]
- **Magnitude.** Creations continued and no lasting large premium developed. [R]
- **Mechanism.** M2 risk + M6, which **did not become a dislocation**.
- **Lesson.** A valuable **near-miss**: the same precursor pattern (demand surge, physical-supply warnings) without an episode. The evaluation needs such cases to estimate false-alarm costs honestly. The catalogue records near-misses explicitly.

#### U10. Russia ETFs, February–March 2022: sanctions, market closure, creations suspended

- **What happened.** After the invasion of Ukraine (24 February 2022), the Moscow Exchange closed and sanctions restricted dealings. VanEck suspended creations of RSX effective 3 March 2022; Cboe halted RSX trading on 4 March 2022 at 16:20 ET. [V: VanEck/Business Wire, Reuters reports] iShares' ERUS and others followed similar paths. [K]
- **Magnitude.** Reports put RSX's premium at more than 500% of its (written-down) NAV at the halt, per Bloomberg data; others cite premiums above 1,000% between the invasion and the halt. [R, figures vary with the NAV basis]
- **Mechanism.** M1 (creation blocked by sanctions) + M3 (NAV unknowable).
- **Precursors.** Market-wide stress, FX collapse (RUB), discounts before the invasion, Moscow Exchange closure (an observable event).
- **Data caveat.** RSX was later liquidated; its historical NAV may no longer be on VanEck's website (P01 probe; MI-04 Wayback fallback). If unavailable, the incident stays in the catalogue as a reference but not in the model data.

#### U11. October 2025: London silver squeeze (global context for the Indian event)

- **What happened.** Silver rose above $50/oz in October 2025 amid tight London liquidity and very high lease rates. [K, re-verify in P03] Whether US silver ETFs (SLV, SIVR) dislocated is an **open empirical question** to be checked in the data (OQ-20).
- **Why it matters.** It links the Indian October 2025 episode (I4) to a global physical-market squeeze, which is the M2/M4 story.

#### U12. Late January–February 2026: precious-metals crash

- **What happened.** Gold and silver peaked around 29 January 2026; silver fell roughly 30% in a single day. The BIS Quarterly Review (16 March 2026) attributed the amplification to leveraged retail investors, leveraged ETFs, CTAs and margin dynamics, and noted that sustained ETF premia had signalled one-sided buying that outpaced primary-market arbitrage. [V as to the BIS statement, via v1 research]
- **Use.** An out-of-sample stress window for both US and Indian commodity ETFs.

### 5.2 India

#### I1. 2013: gold import restrictions and the domestic premium (Layer 1)

- **What happened.** India raised gold import duty in steps during 2013 (to 10% by August) and introduced the "80:20" import rule. Domestic gold traded at a large premium to import parity in late 2013. [K]
- **Use.** A Layer-1 episode for the deterministic local-premium monitor, and a check on whether Indian gold ETFs (then NAV-at-parity) showed a premium. Duty dates must come from the verified duty table.

#### I2. March 2020: COVID-19 stress in Indian ETFs

- **What happened.** Indian ETFs, especially less liquid ones, showed wide price–NAV gaps during the March 2020 crash. [A, to be measured in P15] Treated as a candidate event, confirmed or rejected by the data.

#### I3. 2022 onwards: international ETFs under the overseas-investment cap (structural premiums)

- **What happened.** SEBI asked mutual funds to stop subscriptions into overseas schemes in early February 2022 as the industry-wide US$7 billion limit approached. [V: Business Standard, 29 Jan 2022, and others] SEBI later directed funds to stop inflows into overseas-**ETF**-based schemes from 1 April 2024 as the US$1 billion industry ETF limit neared (per-AMC ETF sub-limit US$300 million). [V: Business Standard 21 Mar 2024; Value Research] With creation shut, international ETFs listed in India have traded at persistent premiums: Mirae Asset NYSE FANG+ ETF at about 22.5% and the S&P 500 Top 50 ETF at about 21% in April 2026 [R: Business Today]; Hang Seng TECH ETF at about 24% in November 2025 [R]; FANG+ in a 12-month range of roughly 12–30% (Sep 2026) [R: Value Research via v1 research]. Mirae has publicly cautioned investors to compare price with iNAV before buying its overseas ETFs. [R: Cafemutual; publication date to be confirmed, OQ-21]
- **Mechanism.** M1 (regulatory capacity cap), structural.
- **How the build treats it.** Structural premiums are *levels*, not onsets. The label's baseline adapts to a persistent level after a capped freeze (System Specification §4.6), so the model forecasts **changes** (sudden widening or collapse), while the deterministic monitor shows the absolute level every day. Without this, every day would be "in episode" and the model would learn nothing.

#### I4. October 2025: silver ETF premiums and fund-of-fund suspensions (the anchor Indian event)

- **What happened.** Silver ETFs traded at 5–10% above iNAV for five straight sessions from 9 October 2025 [R: Business Standard]; Kotak said the domestic silver premium rose from about 0.5% in early September to 5.7% on 9 October, with an intraday peak near 12%. [R: Moneylife, Business Today] Kotak suspended lump-sum and switch-in subscriptions to its Silver ETF FoF effective 10 October (some reports say 9 October); SBI, Tata, ICICI Prudential, Axis, UTI and others followed with similar halts on 13–15 October. [R] Fund houses cited acute scarcity of physical silver in India; Axis noted arbitrageurs could not bridge the gap because physical silver was scarce. [R] Premiums collapsed around 17 October; most AMCs resumed FoF lump-sum investments around 20–24 October. [R]
- **Mechanism.** M2 + M4 (domestic physical squeeze), M6 (festive-season retail demand), with NAV then at import parity so Layer 1 appeared as Layer 2.
- **Important measurement note.** The widely reported 5–10% figures are premiums to **iNAV**. The project's ground truth is the **closing price vs official NAV**. The case study must be evaluated on the project's own measure, with iNAV figures as context only (lesson carried from the v1 review).
- **Precursors to test.** The domestic premium rising for weeks before 9 October (Kotak's figures); silver volume and turnover surging; peer silver ETFs moving together; London squeeze (U11).
- **Who acted.** The suspensions were on **fund-of-funds** (which the AMC controls), not on the ETFs, which kept trading. [R] This is precisely the decision a product team takes, and the decision this system is meant to inform earlier.

#### I5. Late January–February 2026: crash, band lock-ups and an emergency regime change

- **What happened.** On Sunday 1 February 2026 (Budget-day special session) gold ETFs fell about 7% and silver ETFs largely locked at the 20% lower circuit despite a smaller decline in the underlying, because the band was anchored to a stale T-2 NAV; BSE moved the gold/silver ETF band reference to T-1 NAV as an interim step. On 2 February ETFs fell up to 20%. [R: Business Standard] SEBI consulted on ETF base prices and bands on 13 February 2026 and issued a new framework on 15 June 2026, effective 7 September 2026. [V via v1 research]
- **Mechanism.** M7 (band mechanics) + M8.
- **How the build treats it.** Circuit-locked days produce a price that is not a market-clearing price, so premiums on those days are artefacts. Days are classified conservatively (`confirmed_locked`, `near_band`, `unconstrained`, `unknown`) using the band rules in force for that exchange and date, never by assuming a fixed ±20% (lesson from the v1 review). Locked days are excluded from headline metrics and reported separately.

#### I6. September 2026 onwards: new price-band regime and continued international premiums

- **What happened.** The new framework (T-1 last-30-minute VWAP base price; ±6% initial band for gold/silver ETFs with uncapped 3% flexes; ±10% for equity/debt ETFs with up to two 5% flexes; pre-open call auction for gold/silver ETFs) went live on 7 September 2026. [V via v1 research] Mirae and others continued to warn about international ETF premiums. [R]
- **Use.** A short forward-test window; any claims about the new regime must be labelled as based on a few weeks of data.

### 5.3 What the record tells us

1. **Capacity and sourcing failures (M1, M2) produce the largest premiums and give the most warning.** Their precursors (unit growth, local premium, registration headroom) build over days to weeks.
2. **Stale-NAV events (M3) are common, cluster in market-wide stress, and are often triggered abruptly.** The forecastable part is persistence once stress begins.
3. **Near-misses exist** (SLV 2021). Any honest early-warning system will issue some alerts that do not become episodes; the business question is whether the alert budget is tolerable.
4. **Incidents cluster in time** (2008, March 2020, 2022). Statistical tests must resample by time blocks, not by individual ETF-days, or confidence intervals will be far too narrow.

---

## 6. Regulatory frameworks and implications for the build

### 6.1 United States

| Instrument | What it requires | Relevance |
|---|---|---|
| **SEC Rule 6c-11** (adopted 25 Sep 2019) | ETFs relying on the rule must post on their website: daily NAV, market price and premium/discount; a table/chart of premiums and discounts for the most recent calendar year and quarters since; the median bid–ask spread over the last 30 days; and, if the premium or discount exceeds **2% for more than seven consecutive trading days**, a statement of that fact and a discussion of the factors believed to have contributed, kept on the website for at least one year. [V: eCFR 17 CFR 270.6c-11; SEC compliance guide] | **Label template** (2% absolute floor; persistence); **regulatory counter** in the brief |
| Scope of Rule 6c-11 | Applies to open-end management investment companies that are ETFs. It does not apply to ETFs organised as UITs (e.g., SPY, QQQ, DIA) or to exchange-traded products that are not registered investment companies (commodity pools, grantor trusts such as GLD, SLV, USO, UNG). Leveraged/inverse ETFs were initially excluded and later brought within the rule. [K; confirm from the adopting release's scope section, OQ-01] | The disclosure statements cannot be used as labels for the core commodity funds; the project computes its own label |
| Securities Act 1933 registration of shares (commodity pools and grantor trusts) | These funds can only issue shares that have been registered; exhausting the registered amount forces a suspension of creations. [V: UNG 2009 and USO 2020 filings] | **Capacity headroom feature** from filings (P03 capacity table) |
| CFTC position limits and exchange accountability levels | Limit the futures positions a fund can hold; can constrain creations. [K] | Capacity context for futures funds |
| Exchange Limit Up–Limit Down | Intraday pauses on large moves | Intraday; out of scope |

### 6.2 India

| Instrument | What it requires | Relevance |
|---|---|---|
| SEBI (Mutual Funds) Regulations, 2026 (effective 1 Apr 2026) and the Master Circular for Mutual Funds of 20 Mar 2026 | ETFs are MF schemes; at least two market makers; direct creation/redemption in creation-unit multiples; iNAV disclosure. Older scheme documents cite clause numbers of the 2024 master circular. [V/R via v1 research] | Context; clause mapping is OQ-17 |
| **Direct-redemption triggers** (SEBI passive-fund framework, now in the master circular) | Investors may redeem directly with the AMC (up to ₹25 crore, no exit load) if (a) the closing price is at a discount of more than 1% to day-end NAV for 7 continuous trading days, (b) no quotes are available for 3 consecutive trading days, or (c) the total bid size is less than half the creation-unit size, averaged over 7 consecutive trading days. [V: AMC disclosures quoting SEBI; one AMC page shows an older 3%/30-day version, so the current clause must be confirmed, OQ-16] | **Regulatory counter (a)** is fully computable from public data and is an Indian **secondary label**. Trigger (b) is computable from bhavcopy (days with no trades). Trigger (c) needs order-book data and is out of scope. |
| **SEBI circular of 26 Feb 2026** (HO/(68)2026-IMD-POD-2/I/5780/2026) | From 1 Apr 2026, physical gold and silver held by MFs are valued at polled spot prices of recognised stock exchanges that settle physically delivered gold/silver derivatives (MCX the main one), replacing the LBMA AM fixing; AMFI to issue a uniform implementation policy. [V via multiple reports citing the circular; read the primary PDF in P01, OQ-14] | **Measurement break** on 1 Apr 2026 for Layer 2; Layer-1 monitor design (§4.3) |
| SEBI ETF price-band circular, 15 Jun 2026 (HO/47/11/11(1)2026-MRD-POD3/I/13804/2026), effective 7 Sep 2026 (extended from 1 Sep by circular of 28 Aug 2026) | Base price = T-1 last-30-minute VWAP (T-1 NAV targeted from 1 Apr 2027). Commodity ETFs: initial ±6%, flex by 3% after a 15-minute cooling-off triggered at 5.90% (5 minutes in the last 30 minutes), no cap on bands or flexes; equity/debt ETFs: ±10%, flex by 5% up to twice per direction (max ±20%); overnight and liquid ETFs ±5%; pre-open call auction for gold/silver ETFs. [V via v1 research] | Band-proximity monitor; circuit-lock classification; regime indicator |
| Pre-7 Sep 2026 band regime | Fixed ±20% on a T-2 NAV base (interim T-1 base for gold/silver from 1 Feb 2026 on BSE, and exchange-specific interim arrangements). [R via v1 research] | Circuit-lock classification must be exchange- and date-specific (P07) |
| Overseas-investment limits | Industry US$7 billion for MF overseas investment; US$1 billion industry limit for overseas ETFs with a US$300 million per-AMC sub-limit; subscription stops in Feb 2022 and from 1 Apr 2024. [V/R] | Capacity events for international ETFs (catalogue, with `known_at`) |

### 6.3 Implications table

| Fact | Implication | Design consequence [REC] |
|---|---|---|
| Rule 6c-11 excludes commodity trusts and UITs | No regulator-published label for core ETFs | Compute labels from price and NAV; apply the 2%/7-day rule ourselves as a secondary label |
| Registered-share limits are disclosed in filings | Capacity headroom is knowable for US commodity pools | Hand-built capacity table (P03) with `known_at` = filing date |
| India direct-redemption trigger (1%/7 days) | A concrete, regulator-defined discount event | Deterministic counter; Indian secondary label |
| Indian NAV methodology changed on 1 Apr 2026 | Layer 2 premium means something different before and after | Two-layer tracking; documented break; split evaluation |
| India price bands changed (Feb 2026 interim, 7 Sep 2026 new regime) | Historical prices censored by bands differently over time | Conservative lock classification; regime flag; locked days excluded from headline metrics |
| No public daily creation data in India | US creation features cannot transfer | Two model variants: full (US) and transferable core (US→India) |

### 6.4 Compliance guardrails for the system itself [REC]

- Internal decision support for product, sales and risk teams. Every output carries "Model estimate. Not investment advice." No buy/sell/hold language and no return forecasts.
- Data are used for research only; terms of use for every source are recorded (MI-07). No redistribution of raw vendor data.
- Anything shown to distributors or clients would need Mirae compliance review under SEBI's MF advertising and communication norms. [A]

---

## 7. Mirae Asset context, users and business value

### 7.1 Why Mirae Asset is exposed to this problem

- Mirae Asset Investment Managers (India) runs a broad ETF range, including gold (`GOLDETF`), silver (`SILVERAG`, formerly `SILVRETF`, ISIN INF769K01KG6), international ETFs (NYSE FANG+ `MAFANG`, S&P 500 Top 50, Hang Seng TECH) and many domestic equity ETFs, plus fund-of-funds that invest in its ETFs (Silver ETF FoF launched March 2026; Gold ETF FoF). [V/R via v1 research]
- Two of the incident types in §5 hit Mirae's products directly: the October 2025 silver premium (I4) and the structural premium on its international ETFs (I3), about which it has issued investor cautions. [R]
- Gold and silver ETFs were reported as 54% of all Indian ETF flows in February 2026, which makes them a mass-retail, distributor-facing product. [R]
- The brief was prepared for Umesh Daila of the Mirae Asset ETF team, who raised the point about NAV construction that §4 now verifies. [Source: the brief]

### 7.2 Who acts, and on what

| User | Decision the system informs | Output that supports it | Lead time that is useful [A, validate via MI-10] |
|---|---|---|---|
| **Product & Operations** | Whether to pause FoF lump-sum subscriptions; coordinating market makers; monitoring capacity on overseas ETFs | Breakdown probability; root-cause tag; capacity/structural-premium monitor | 1–3 days ahead of onset |
| **Sales & Distribution** | Advising distributors when not to buy at a large premium, or when to prefer the FoF route; preparing for client questions | Daily Stress Brief with plain-language reasons and the closest past incident | Same day to 2 days |
| **Risk & Compliance** | Anticipating the SEBI direct-redemption trigger; preparing disclosures; watching band proximity | Deterministic counters (1%/7-day discount, no-quote days, band distance) | Days before the trigger is hit |

### 7.3 How business value is measured (not just asserted) [REC]

The final evaluation (P14, P15) reports these quantities, each computed from the backtest:

1. **Premium cost avoided.** For each alert at the High level, the average premium paid by a buyer on the alert day minus the premium on the day the gap closes (or after 10 days). Expressed in bps and in ₹ per ₹1 crore of purchases deferred. This turns "we warned early" into "this is what a distributor's client would have overpaid".
2. **Lead time.** Distribution of days between the first High alert and episode onset, for warned episodes.
3. **Alert burden.** Alerts per week across the universe; false alerts per ETF-month outside episodes. An early-warning system that cries wolf is ignored.
4. **Regulatory-trigger anticipation.** For episodes that reached the SEC 2%/7-day or SEBI 1%/7-day trigger, how many trading days of warning were given before the trigger date.
5. **Decision replay.** For October 2025, the date on which the system would have reached High for silver ETFs versus the dates of actual FoF suspensions (10–15 October). Reported as a case study, not as statistical proof.

### 7.4 Positioning

A research prototype and decision-support demonstration, built on public data, reproducible end to end, which a team with licensed data could adopt. It is not a production system, not a trading signal and not advice.

---

## 8. Literature and existing solutions

### 8.1 Academic and institutional work

| Work | Finding relevant here | Use in the project | Grade |
|---|---|---|---|
| Petajisto (2017), "Inefficiencies in the Pricing of Exchange-Traded Funds", *Financial Analysts Journal* 73(1) | Premiums typically within 100–200 bps for illiquid/international ETFs; stale-price effects; mean reversion | Normal-band expectations; timing caveat | [C] |
| Engle and Sarkar (2006), "Premiums-Discounts and Exchange Traded Funds", *Journal of Derivatives* | Domestic ETF premiums small and transient; international ones larger and more persistent | Group-specific scales | [C] |
| Ben-David, Franzoni and Moussawi (2018), "Do ETFs Increase Volatility?", *Journal of Finance* | Arbitrage transmits ETF demand shocks to the underlying | Demand-pressure channel | [C] |
| Pan and Zeng, "ETF Arbitrage under Liquidity Mismatch" (working paper) | AP arbitrage is limited when bonds are illiquid; ETF prices deviate in stress | Bond-ETF mechanism (M3/M5) | [C] |
| Haddad, Moreira and Muir (2021), *Review of Financial Studies*; Falato, Goldstein and Hortaçsu (2021), *Journal of Monetary Economics* | March 2020 bond-market dysfunction and fund fragility | Context for U7 | [C] |
| Aramonte and Avalos (2020), BIS Bulletin No. 6, "The recent distress in corporate bond markets: cues from ETFs" | ETF discounts as a signal of bond-market distress; ETF prices led NAVs | U7; `STALE_NAV` interpretation | [V] |
| BIS Quarterly Review, 16 Mar 2026 | Sustained ETF premia signalled one-sided buying before the 2026 metals crash | U12/I5 | [V via v1] |
| Kaminsky, Lizondo and Reinhart (1998), "Leading Indicators of Currency Crises", *IMF Staff Papers* | The "signals approach" to early warning: evaluate indicators by lead time and noise-to-signal ratio | Event-level evaluation design (lead time, false-alarm rate) | [C] |
| Ardia, Guidotti and Kroencke (2024), "Efficient estimation of bid–ask spreads from open, high, low, and close prices", *Journal of Financial Economics* 161, 103916 | EDGE estimator; open-source Python package `bidask` (functions `edge`, `edge_rolling`) | Spread estimate where no quote history exists | [V] |
| Corwin and Schultz (2012), *Journal of Finance*; Abdi and Ranaldo (2017), *Review of Financial Studies* | Earlier high–low spread estimators | Robustness alternative to EDGE | [C] |
| Amihud (2002), *Journal of Financial Markets* | Illiquidity ratio \|return\| / dollar volume | Liquidity feature | [C] |
| López de Prado (2018), *Advances in Financial Machine Learning* | Purged and embargoed cross-validation for overlapping labels | Walk-forward design | [C] |
| Gneiting and Raftery (2007), *JASA* | Proper scoring rules (Brier, log score) | Primary probabilistic metrics | [C] |
| Saito and Rehmsmeier (2015), *PLOS ONE* | Precision–recall curves are more informative than ROC for imbalanced data | PR-AUC as primary ranking metric | [C] |
| Niculescu-Mizil and Caruana (2005), *ICML* | Boosted trees produce distorted probabilities; isotonic/Platt calibration fixes this | Calibration step | [C] |
| Ke et al. (2017), "LightGBM", *NeurIPS*; Lundberg and Lee (2017), "A Unified Approach to Interpreting Model Predictions", *NeurIPS* | Model and explanation method | Core model and SHAP | [C] |

### 8.2 Existing tools

| Tool | What it does | Gap |
|---|---|---|
| Issuer websites (Rule 6c-11 disclosures) | Current premium, one-year history, 2%/7-day statements | Backward-looking, per fund, no forecast |
| Exchange and AMC iNAV pages (India) | Live price vs iNAV | Present only; no history; no forecast |
| Broker nudges (e.g., iNAV premium warnings at order entry) [R] | Warn a retail buyer at the moment of purchase | Reactive, retail-facing, no forecast |
| Value Research and press trackers of international ETF premiums | Weekly premium tables; heuristic zones (0–3% normal, 3–5% caution, 5–10% stretched, >10% overheated) [R] | Descriptive |
| Data vendors (Bloomberg, TrueData iNAV, BSE iNAV via Deutsche Börse) | Data supply | Data, not decision support |

### 8.3 The gap the project fills

No public, forecast-oriented, backtested system was found (as of 17 Nov 2026) that (a) forecasts the **onset** of ETF arbitrage breakdowns, (b) explains them by **mechanism**, (c) links them to **historical analogues**, and (d) tests whether such a model **transfers across markets** to India. [A: absence of evidence after searching]

---

## 9. The data landscape

> **P01 update (17 Nov 2026):** every source below was probed. Results, including which sources are scriptable, manual-only or unavailable, are in [`reports/data/source_probe_report.md`](../../reports/data/source_probe_report.md) and [`reference/source_registry.csv`](../../reference/source_registry.csv). Where they differ from the planning tables below, the P01 results win. Key changes: Stooq dropped; NSE archive scriptable only from 2016; RSX/EGPT/ERUS NAV unavailable without CRSP; USCF NAV manual (no shares outstanding); AMFI API provides NAV upload timestamps; EIA futures end 2024-04-05.

### 9.1 United States: ETF-level data

| ID | Data | Candidate sources | History | Access | Risks |
|---|---|---|---|---|---|
| US-1 | Daily official close, open, high, low, volume (unadjusted) | **Tiingo** EOD API (free tier, API key) [K]; fallbacks: Stooq CSV, `yfinance` (unofficial) | 1990s onwards | MI-02 for the Tiingo key | Must use **unadjusted** prices against NAV; splits must be handled consistently |
| US-2 | Daily NAV per share | **Issuer websites**: SPDR Gold "Historical Archive (XLSX)" for GLD [V: page lists the download]; iShares fund-page data downloads (NAV history; coverage depth to confirm) [R]; USCF historical data for USO/UNG/BNO/UGA/USL/UNL/CPER/USCI [K]; SSGA NAV history files; Invesco, VanEck, Vanguard, Global X, Xtrackers, abrdn, Teucrium per-fund pages [K] | Since inception (to confirm per issuer) | Scripted where possible; **manual download fallback (MI-04)** | Bot protection, changing URLs, history truncated to recent years, delisted funds removed |
| US-3 | Daily shares outstanding | Same issuer files (GLD archive includes it [K]; iShares and USCF files likely [R]) | Since inception (to confirm) | As US-2 | Reporting lag ambiguity (T vs T+1 settlement); must be verified per issuer (OQ-05) |
| US-4 | Issuer-published premium/discount and NBBO midpoint at NAV time | Issuer pages (Rule 6c-11 funds; GLD archive) | Usually 1 year (6c-11); longer for GLD | Optional | Used only for cross-checking our computed premium |
| US-5 | Optional premium source: CRSP (daily prices, bid/ask, shares, and mutual-fund NAVs) via WRDS | University subscription | Long | **MI-06** (only if the user's institution has WRDS) | Not assumed available |

### 9.2 United States: underlying and market-wide data

| ID | Data | Source | Notes |
|---|---|---|---|
| UM-1 | Gold, silver, platinum, palladium global prices | COMEX continuous futures (`GC=F`, `SI=F` via yfinance/Stooq) as daily proxies; NAV-implied benchmark (GLD NAV ÷ ounces per share ≈ LBMA PM price) | LBMA prices are licensed by IBA; FRED's LBMA gold series was discontinued [K]. Returns-based features tolerate proxies. |
| UM-2 | WTI and Henry Hub futures curve (contracts 1–4) | EIA NYMEX futures series | **EIA crude futures series appear to have stopped after 5 Apr 2024; natural gas pages show recent releases** [R: EIA pages]. Post-2024 curve must come from another source (OQ-08), e.g., continuous front/second-month futures from yfinance (`CL=F`; specific contract tickers) |
| UM-3 | VIX | FRED `VIXCLS` | Daily since 1990 |
| UM-4 | Credit spreads | FRED `BAA10Y` (Moody's Baa minus 10-year Treasury) | ICE BofA OAS series on FRED have restricted history [K, OQ-09] |
| UM-5 | Treasury yields, USD index | FRED `DGS10`, `DTWEXBGS` | |
| UM-6 | FX (USD/INR, USD/RUB, USD/EGP, EUR/USD, etc.) | FRED `DEXINUS` etc.; RBI/FBIL reference rate for INR | |
| UM-7 | Foreign exchange-holiday calendars | `exchange_calendars` Python package | Scheduled closures (known in advance) |
| UM-8 | Unscheduled market closures, trading halts, creation suspensions, registered-share data | Hand-built incident and capacity tables from SEC EDGAR filings and press (P03) | Each row has `effective_at`, `known_at`, source URL |
| UM-9 | CFTC Commitments of Traders (weekly open interest) | CFTC website | Optional: position-limit context for USO/UNG |

### 9.3 India

| ID | Data | Source | Notes |
|---|---|---|---|
| IN-1 | Daily OHLC, close, volume, turnover, number of trades | NSE CM bhavcopy archives: UDiFF format since 8 Jul 2024 (`BhavCopy_NSE_CM_0_0_0_YYYYMMDD_F_0000.csv.zip`) and legacy format before that [V via v1 research]; BSE as fallback | Two schemas; symbol changes (`SILVRETF`→`SILVERAG` on 15 Sep 2025); NSE bot protection on web pages (archive host more stable) |
| IN-2 | Official daily NAV | AMFI `NAVAll.txt` (latest) and NAV-history download (**90 days per request**; old-format download retired) [V]; fallback `mfapi.in` (unofficial full-history API by AMFI scheme code) [K] | Published late evening; key by ISIN and AMFI code |
| IN-3 | Domestic gold/silver spot | MCX polled spot / bhavcopy; IBJA daily rates | Historical availability and automation uncertain (OQ-13); manual fallback MI-05 |
| IN-4 | Import duty table | CBIC notifications, Budget documents | Hand-verified table with effective dates (MI-09) |
| IN-5 | Scheme master (ISIN, AMFI code, symbols, inception, benchmark, creation unit) | AMFI scheme list, SIDs | Hand-verified universe table |
| IN-6 | Monthly scheme AUM | AMFI monthly disclosures | Too lagged for daily signals; context and slow-moving demand feature only |
| IN-7 | Events (FoF suspensions/resumptions, overseas-cap stops, symbol changes, band-regime changes, special sessions) | AMC notices, SEBI/NSE/BSE circulars, press | `known_at` discipline; P03 |
| IN-8 | India VIX | NSE historical index data | Market-wide stress feature |
| IN-9 | Trading calendar and special sessions | Derived from bhavcopy file presence plus NSE holiday lists | Sunday 1 Feb 2026 special session; Muhurat sessions |

### 9.4 What is not available, and the substitute used

| Wanted (proposal) | Status | Substitute [REC] |
|---|---|---|
| Historical daily bid/ask (US) | Not free (CRSP has it) | **EDGE spread estimator** from daily OHLC (`bidask` package), plus Amihud illiquidity and high–low range; CRSP if MI-06 succeeds |
| Order-book depth | Not available historically in either market | Dropped. Not proxied. |
| Historical iNAV (India) | No free archive [R] | Official NAV only. iNAV-based figures are context, never ground truth. |
| Daily creation/redemption or units outstanding (India) | Not public | Monthly AUM-based flow estimate (lagged); FoF suspension events |
| News or search attention | Possible (news APIs, Google Trends) but terms-of-service and point-in-time problems | **Parked** (future work); volume surges serve as the attention proxy |
| Futures roll costs | EIA curve to 2024 (crude); proxies after | Front/second-month spread where available; missing flags otherwise |
| Overseas-cap utilisation (India) | Not published daily (OQ-12) | Suspension events from the catalogue |
| Arbitrage cost (creation fees, financing) | Partly in prospectuses; physical sourcing costs unknown | **Empirical no-arbitrage band** from calm-period premium distribution |

### 9.5 Known data traps

1. **Adjusted vs unadjusted prices.** Vendors' "adjusted close" adjusts for dividends and splits; NAV does not adjust for dividends. Premium must use unadjusted close and split-consistent NAV. USO's 1-for-8 reverse split in April 2020 lands inside the event window.
2. **Issuer NAV files may be split-adjusted while vendor prices are not** (or vice versa). Every ETF needs a split reconciliation check (P07).
3. **Shares-outstanding timing.** Some issuers report shares outstanding reflecting orders accepted on T, others reflecting settlement. Flow features must allow for a one-day ambiguity (OQ-05).
4. **Delisted and liquidated funds** (RSX, ERUS) disappear from issuer websites, creating survivorship bias if ignored. They are deliberately sought (MI-04 Wayback fallback).
5. **NAV restatements and errors** (rare, large single-day spikes that reverse). Detected by the jump-and-reverse check in P07.
6. **India: two bhavcopy schemas, symbol changes, special sessions, circuit-locked days, NAV published late evening, AMFI endpoint changes.**
7. **Holiday mismatches.** A US ETF can trade on a day its NAV uses a stale foreign price. That is signal (NAV staleness), not error, and must be preserved.

### 9.6 Feature availability matrix (the transfer constraint)

| Feature family | US | India | In transferable core model? |
|---|---|---|---|
| Gap state and persistence (premium, robust z-score, run length, momentum) | Yes | Yes | **Yes** |
| Creation activity (shares outstanding changes; creation on premium) | Yes | No (monthly AUM only) | No (US full model only) |
| Capacity headroom (registered shares; caps) | Partly (filings) | Event flags only | Event-flag version only |
| Liquidity (EDGE spread, Amihud, volume, range, zero-trade days) | Yes | Yes | **Yes** |
| NAV staleness (closure fractions, ETF–NAV return divergence) | Yes | Yes | **Yes** |
| Underlying stress (realised volatility, drawdown, gaps; roll yield for futures funds) | Yes | Yes (metals); not applicable (equity) | **Yes** (missing-aware) |
| Local-vs-global (Layer 1) | Limited (COMEX–London proxy) | Yes (if IN-3 obtained) | Yes, missing-aware |
| Demand pressure (volume/turnover surges, peer co-movement) | Yes | Yes | **Yes** |
| Market-wide stress (VIX, credit, FX) | Yes | Yes (India VIX, INR) | **Yes** (market-matched) |
| Calendar (holidays, foreign closures, roll windows, festivals) | Yes | Yes | **Yes** |

---

## 10. Feasibility assessment

### 10.1 Data feasibility

| Component | Feasibility | Main risk | Mitigation |
|---|---|---|---|
| US prices | High | Vendor terms; unadjusted series | Tiingo key (MI-02); fallbacks |
| US NAV and shares | **Medium**: the critical-path risk | Issuer sites block scripts or truncate history | P01 source probe per ETF; MI-04 manual downloads; universe adjusted to what is obtainable; CRSP option (MI-06) |
| US underlying and macro | High | Licensed benchmarks (LBMA) | Proxies; NAV-implied benchmarks |
| India prices and NAV | High (proven in v1 research) | Endpoint changes; bot protection | Archive host; mfapi.in fallback; MI-05 |
| India domestic spot (Layer 1) | **Medium-low** | MCX/IBJA history access | MI-05; if unavailable, Layer 1 is limited to post-Apr-2026 NAV-implied values and the feature is missing-aware |
| Incident catalogue | Medium (labour-intensive) | Date precision; `known_at` | P03 protocol; user sign-off (MI-08) |

### 10.2 Statistical feasibility

- **Event counts.** The proposed US universe (~50–70 ETFs across commodity, bond, international and control groups, 2004–2026) is expected to yield on the order of **50–200 dislocation-episode onsets** under the primary label [A, AS-03], clustered in 2008, 2011, 2013, 2015, 2020 and 2022. P09 counts them and has a hard gate: if the development period has fewer than 40 onsets or the lockbox period fewer than 20, the label or universe is revised *before* any modelling, and the revision is pre-registered.
- **Clustering.** Many onsets occur in the same weeks (March 2020). The effective sample size is much smaller than the onset count. Confidence intervals use a block bootstrap by calendar month, and results are reported both overall and excluding the single largest cluster.
- **Transfer.** India offers a handful of strong episodes (2022–2026 international ETFs, October 2025 silver, February 2026 crash) and an unknown number of smaller ones. The Indian evaluation is therefore partly a **case-study evaluation** with honest uncertainty, plus a quantitative evaluation on whatever onsets the label finds.

### 10.3 Compute and tooling

A laptop is enough: the panel is roughly 70 ETFs × 5,500 days ≈ 400k rows (US) plus ~80 ETFs × up to 4,900 days (India). LightGBM trains in seconds. No GPU, database server or cloud service is needed.

### 10.4 Timeline

Roughly 50–70 working days across 18 phases (about 10–14 weeks full-time, longer part-time); phases P03–P06 can run in parallel, which shortens the critical path. Per-phase estimates are in System Specification §13. The minimum credible cut is P00–P14 (US validation complete) plus the October 2025 India case study from P15.

### 10.5 Principal risks

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| US NAV history unobtainable for key ETFs | Medium | High | P01 probe first; manual downloads; universe flexibility; CRSP |
| Too few onsets | Medium | High | P09 gate; label sensitivity; universe expansion |
| Label dominated by timing artefacts | Medium | High | Persistence; forward-NAV check; group-specific scales |
| Leakage through features or tuning | Medium | Critical | Point-in-time store, leak tests, lockbox opened once, pre-registration |
| Transfer fails (US patterns do not apply to India) | Medium | Medium (a reportable finding) | Core-feature model; India-calibrated variant; honest reporting |
| Scope creep (LLM briefs, intraday, live alerts) | Medium | Medium | Parked list; phase gates |
| Data terms of use | Low | Medium | Research use only; MI-07 |

---

## 11. Rationale for the chosen approach

### 11.1 Why forecast breakdown onsets rather than daily premiums

Daily premium changes are dominated by timing noise and mean reversion; forecasting them well is easy and nearly useless (persistence wins). The decisions people take (pausing FoF subscriptions, warning distributors) respond to **breakdowns**, which are rare, large and persistent. Predicting their onset 1–5 days ahead is harder, more valuable, and directly evaluable by lead time and false-alarm rate.

### 11.2 Why US first, India second

The US offers two decades of daily NAV and price data for many ETFs with documented breakdowns spanning every mechanism in §3, plus public shares-outstanding data to observe the arbitrage pipe directly. India offers few breakdowns and no creation data. Training on India alone would overfit one or two events. Training on the US and testing on India answers a sharper question: **are the warning signs of arbitrage failure universal?**

### 11.3 Why this label definition [REC]

The full specification is in System Specification §4.6–4.8. In short:

- **Daily dislocation indicator:** the gap's deviation from the ETF's own robust baseline must exceed **the larger of** an absolute floor (200 bps, mirroring the SEC's 2%) and 3 robust standard deviations. Using the larger of the two (not "either") stops calm ETFs from triggering on noise and stops volatile ETFs from triggering on their normal swings.
- **Episode:** at least 3 consecutive dislocation days (one-day gaps bridged). Persistence removes most timing artefacts.
- **Target:** whether an episode **starts** within the next 5 trading days, for ETF-days not already in an episode. Days inside an episode are shown as "ACTIVE" deterministically; predicting that an existing episode continues is trivial and would inflate scores.
- **Structural absorption:** if an episode lasts beyond 60 trading days, the baseline resumes adapting, so persistent structural premiums (Indian international ETFs) become the new normal and the model forecasts changes from it. The absolute level is always shown by the deterministic monitor, so a persistently expensive ETF never looks "safe".
- **Secondary labels:** the SEC-style rule (|premium| > 2% for more than 7 consecutive days) and the SEBI-style rule (discount > 1% for 7 consecutive days, India) are evaluated for lead time but not used for training.
- **Operational events** (creation suspensions, subscription halts) from the catalogue are evaluated for lead time; they are too few and too imprecisely dated to train on.
- **Sensitivity:** the absolute floor (100/300 bps), the multiplier (2.5/4) and the persistence (2/5 days) are varied in P14 to show that conclusions do not hinge on one choice.

### 11.4 Why LightGBM, and why it must beat simple baselines

Tree ensembles handle mixed-scale tabular features, missing values (important for missing-aware transfer features) and interactions (a premium *with* falling creation activity means more than either alone), and they train quickly enough for walk-forward refits. With few events, deep learning is not justified. But a model is only worth its complexity if it beats:

- **B0** the base rate (climatology) by asset group;
- **B1** a calibrated single-signal rule (probability as a function of the current robust z-score);
- **B2** a persistence lookup (empirical onset frequency given recent dislocation-day counts and current z-score bin);
- **B3** a regularised logistic regression on about ten core features.

Every baseline outputs a probability, so Brier skill and PR-AUC comparisons are fair (lesson from the v1 review).

### 11.5 Why explanations are grouped into mechanism families

Raw SHAP values over 60 features are unreadable for a product or sales team. Grouping features into the mechanism families of §3 gives a short, stable vocabulary (`CREATION_CONSTRAINT`, `STALE_NAV`, `UNDERLYING_SQUEEZE`, `LIQUIDITY_DRAIN`, `DEMAND_SURGE`, `MARKET_WIDE_STRESS`) that maps directly to who should act. The tags are **validated**: agreement with hand-labelled mechanisms in the incident catalogue is measured against a chance baseline (P13).

### 11.6 Why two model variants

- **Full US model:** every feature, including creation activity and capacity. Answers "how well can arbitrage stress be forecast with the best public data?"
- **Transferable core model:** only features that exist in both markets (§9.6). Trained on the US, applied unchanged to India. Answers "do the warning signs transfer?" Comparing the two also quantifies **how much the unavailable Indian creation data would be worth**, which is itself a useful message for a team that has internal creation data.

### 11.7 Why a strict validation protocol

The research question is whether warning is possible *in advance*. Any leakage invalidates the answer. The protocol therefore uses: a point-in-time data store with `known_at` timestamps; features computed only from data known at decision time; purged and embargoed walk-forward splits; hyper-parameter tuning only inside the development period; a **pre-registration** that freezes labels, thresholds, metrics and success criteria; and a **lockbox** (US data from 1 Jan 2020, all Indian data) opened once, after sign-off (MI-11).

### 11.8 Why a template-generated brief, not an LLM brief

Every sentence in the daily brief must trace to a number. A template (Jinja2) over the model outputs is reproducible and auditable. An LLM narrative layer is parked as future work; if added, it must be grounded only in the generated tables.

---

## 12. Critical reassessment of the proposal and the brief

| # | Claim or design in the proposal/brief | Verdict | Adjustment [REC] |
|---|---|---|---|
| 1 | "Under SEC Rule 6c-11, US ETFs publish daily NAV, price and premium/discount history, and must disclose any premium or discount above 2% that lasts more than 7 trading days. That gives us a ready-made, regulator-defined incident label." | **Partly wrong.** The rule exists as described [V], but it excludes commodity trusts/pools and UITs [K], covers only data since 2019–2020, and the postings are not archived. | Compute labels from NAV and price; use 2%/7 days as a secondary label definition. |
| 2 | "A breakdown is labelled when premium exceeds either 2% or 3× its normal range for 3+ days, or creations are suspended." | **Needs correction.** "Either" fires on calm ETFs; "normal range" is undefined; "creations suspended" mixes a sparse operational event into a price label. | Use `max(200 bps, 3 × robust scale)`; define the scale precisely; keep operational events as a separate evaluated target. |
| 3 | "Excess premium = premium − arbitrage cost (bid-ask spreads + creation charges + financing)." | **Not computable reliably** from public data. | Empirical no-arbitrage band per ETF; bottom-up cost only as a cross-check where inputs exist. |
| 4 | Liquidity features "bid-ask spread, trading volume and order-book depth". | No historical spreads or depth for free. | EDGE estimator, Amihud, volume, range; depth dropped. |
| 5 | Indian data "AMFI NAVs and NSE/BSE prices and iNAV". | No free historical iNAV. | NAV only; iNAV as context. |
| 6 | "Creation activity: whether new units are being created when the ETF trades at a premium." | Feasible in the US only. | US full model only; India uses event flags and monthly AUM flows. |
| 7 | "Demand pressure: unusual fund inflows, trading volume or news attention." | News attention is parked (point-in-time and terms-of-use risks). | Volume/turnover and US share flows only. |
| 8 | "When NAV is stale, the last NAV is first rolled forward using live futures and FX moves." | "Live" (intraday) data are not available; a daily roll-forward is only approximate. | Roll-forward implemented only where a same-day proxy closes near the ETF close; otherwise timing features and persistence handle it; the forward-NAV check flags suspects. |
| 9 | US data "starting with GLD (2004), SLV and USO (2006) and UNG (2007). 20 years." | Correct as to launch years [K]; NAV history depth must be confirmed per issuer. | P01 probe. |
| 10 | Russia ETFs ">100% premium". | Understated; reports cite >500% at the halt [R]. | Catalogue records the reported range and the NAV basis caveat. |
| 11 | "Indian silver ETFs 5–10%+ above iNAV in October 2025." | Correct as reported, but iNAV-based. | Evaluate on close-vs-NAV; iNAV figures are context. |
| 12 | "Since April 2026, Indian gold and silver ETF NAVs use MCX spot prices." | Verified [V]: exchange-polled spot prices (MCX main; BSE also mentioned). | Two-layer tracking; measurement break on 1 Apr 2026. |
| 13 | "Root-cause explainer" and "analogue finder" as AI components. | Sound if validated. | Validation against hand-labelled mechanisms (P13). |
| 14 | "Daily ETF Stress Brief & action playbook." | Sound. "Action playbook" must not become advice. | Template brief with descriptive language and "who acts" routing; compliance guardrails. |
| 15 | "Contrast groups: international-equity ETFs facing closed markets or investment caps." | Sound and necessary for M1/M3 coverage. | Included (EGPT, GREK, RSX, ERUS, ASHR, FXI and others, subject to data). |
| 16 | "Risk & compliance: early sight of SEBI triggers such as the direct-redemption window." | Sound and cheap. | Deterministic counter; Indian secondary label. |

---

## 13. Open questions register

Status is tracked live in [`records/OPEN_QUESTIONS.md`](../../records/OPEN_QUESTIONS.md). "Blocks" names the first phase that cannot finish until the question is answered or a documented default is adopted.

| ID | Question | Why it matters | How to resolve | Default if unresolved | Blocks |
|---|---|---|---|---|---|
| OQ-01 | Exact scope of Rule 6c-11 (UITs, commodity trusts, leveraged funds) | Claims in the report | Read the adopting release (84 FR 57162, "Scope") and 17 CFR 270.6c-11 | State "applies to open-end ETFs; does not apply to commodity trusts" with [K] | P17 (report) |
| OQ-02 | NSE (and BSE) closing-price methodology for ETFs; effect of any closing-auction session | Indian price clock | NSE methodology pages/circulars | Assume last-30-minute VWAP; flag | P05 |
| OQ-03 | For each US issuer: can NAV and shares-outstanding history since inception be downloaded, and how? | Critical path | P01 probe | Manual download (MI-04) | P04 |
| OQ-04 | Are issuer NAV histories split-adjusted? (USO 2020, UNG, others) | Premium correctness | Compare with prices around split dates | Reconcile empirically | P07 |
| OQ-05 | Shares-outstanding timing convention per issuer (T vs T+1) | Flow features | Compare share changes with known creation dates | Lag flows by one day | P10 |
| OQ-06 | Valuation time of each US ETF's NAV (from prospectuses) | Timing features | Prospectus "Net Asset Value" sections | Use the defaults in §4.1 | P08 |
| OQ-07 | Is RSX/ERUS/EGPT/GREK daily NAV history still obtainable? | Coverage of M1/M3 | Issuer sites; Wayback Machine; CRSP | Catalogue-only reference | P04 |
| OQ-08 | Source for WTI/Henry Hub futures curve after April 2024 | Roll-yield feature | Check EIA; yfinance contract tickers | Missing-aware feature after 2024 | P06 |
| OQ-09 | Usable long-history credit-spread series | Market-wide feature | FRED series checks | `BAA10Y` | P06 |
| OQ-10 | Indian gold/silver ETF NAV valuation time and method before and after 1 Apr 2026, per scheme | Layer-2 clock and the measurement break | SIDs; AMFI uniform policy; NAV vs spot regression | Assume LBMA AM + FX + duty before, exchange-polled spot after | P08 |
| OQ-11 | Does SEBI's 2026 price-band framework apply to international ETFs? | Band monitor | NSE/CMTR/76101 and 76041 | Apply the equity-ETF rule and flag | P16 |
| OQ-12 | Is AMC or industry overseas-cap utilisation published anywhere? | Capacity feature (India) | SEBI/AMFI disclosures | Event flags only | P10 |
| OQ-13 | Can MCX/IBJA domestic spot history be downloaded (and since when)? | Layer 1 | P01 probe; MI-05 | Layer 1 limited to NAV-implied post-2026 values | P05 |
| OQ-14 | Exact text of the SEBI circular of 26 Feb 2026 and the AMFI implementation policy (polling time, exchanges) | Layer-1/Layer-2 split | Read the SEBI PDF and AMFI notice | As in §4.1 | P08 |
| OQ-15 | India gold/silver import duty history 2007–2026, including Feb 2026 Budget and any May 2026 change | Layer 1 | CBIC notifications; MI-09 | Do not compute Layer 1 for unverified periods | P05 |
| OQ-16 | Current wording of the SEBI direct-redemption triggers in the 2026 master circular | Indian secondary label | Master circular; recent SIDs | 1%/7-day, 3-day no-quote, bid-size triggers | P09 |
| OQ-17 | Clause mapping from the 2024 to the 2026 MF master circular | Citations | Read the 2026 master circular | Cite via SIDs | P17 |
| OQ-18 | Historical band rules per exchange and date for Indian ETFs (incl. Feb 2026 interim) | Circuit-lock classification | Exchange circulars | `unknown` class | P07 |
| OQ-19 | Corporate actions (splits/consolidations) in Indian ETFs | Price adjustment | Exchange corporate-action files | Detect jumps; reconcile | P07 |
| OQ-20 | Did US silver ETFs dislocate in October 2025 or January–February 2026? | Global context for I4/I5 | Measure in data | Report as found | P14 |
| OQ-21 | Date and wording of Mirae's overseas-ETF investor caution | Report accuracy | Cafemutual article and Mirae notices | Cite without a date | P17 |
| OQ-22 | What lead time and alert budget would Mirae's teams find useful? | Thresholds and framing | Stakeholder conversation (MI-10) | 1–5 days; ≤ 1 High alert per ETF-quarter outside episodes | P11 |
| OQ-23 | Tiingo terms and rate limits for this use | Data access | MI-02/MI-07 | Use fallbacks | P04 |

---

## 14. Assumptions register

| ID | Assumption | Test | Phase |
|---|---|---|---|
| AS-01 | Daily public data carry some advance signal of arbitrage breakdowns | **The core empirical question**: H1–H3 in the pre-registration | P14 |
| AS-02 | Mechanisms of breakdown are similar enough across markets for warning patterns to transfer | Transfer test H6 | P15 |
| AS-03 | The US universe yields enough onsets (≥ 40 development, ≥ 20 lockbox) | Count in P09 | P09 |
| AS-04 | EDGE spread estimates are informative for ETFs | Compare with issuer-published median spreads where available | P10 |
| AS-05 | Persistence (≥ 3 days) removes most timing artefacts | Forward-NAV robustness share | P09 |
| AS-06 | Hand-labelled mechanisms in the catalogue are reliable enough to validate root-cause tags | Second-pass review; user sign-off (MI-08) | P03 |
| AS-07 | An alert budget of about one High alert per ETF-quarter outside episodes is acceptable | Stakeholder feedback (MI-10) | P11 |
| AS-08 | Free data sources remain accessible for the project's duration | Raw-file caching | All |

---

## 15. Glossary

| Term | Meaning |
|---|---|
| **AP / Market Maker** | Firm that creates and redeems ETF units with the fund (US: Authorised Participant; India: Market Maker, at least two per ETF) |
| **Creation unit** | The block size in which units are created or redeemed |
| **NAV** | Net asset value per unit, struck once per day |
| **iNAV / IIV** | Intraday indicative NAV |
| **Premium / discount** | Market price relative to NAV; positive = premium; expressed in basis points (1 bp = 0.01%) |
| **Layer 1 / Layer 2** | Local-vs-global premium in the underlying / ETF price-vs-NAV premium (§4.3) |
| **Dislocation day** | A day on which the gap exceeds the label threshold |
| **Episode** | A run of at least 3 dislocation days |
| **Onset** | First day of an episode |
| **Lead time** | Trading days between the first alert and the onset |
| **Operational event** | Creation suspension, subscription halt, trading halt or capacity exhaustion |
| **Root-cause tag** | The mechanism family that contributed most to an alert |
| **Analogue** | The past incident whose pre-onset signature is closest to the current one |
| **Lockbox** | Data held back from all development until a single final evaluation |
| **Pre-registration** | A frozen document of definitions, thresholds, metrics and pass criteria written before the lockbox is opened |
| **Walk-forward** | Train on the past, test on the next block, roll forward |
| **Purge / embargo** | Removing training rows whose labels overlap the test period / leaving a gap after it |
| **PR-AUC** | Area under the precision–recall curve |
| **Brier score / Brier skill score** | Mean squared error of a probability / its improvement over a reference |
| **Calibration / reliability diagram** | Whether predicted probabilities match observed frequencies / the plot that shows it |
| **SHAP** | Additive feature contributions to a prediction |
| **EDGE** | Ardia–Guidotti–Kroencke bid–ask spread estimator from daily OHLC prices |
| **FoF** | Fund of funds; an Indian MF scheme investing in an ETF, bought at NAV through the AMC |

---

## 16. Source register

**Primary and official**

1. eCFR, 17 CFR 270.6c-11 (Rule 6c-11): https://www.ecfr.gov/current/title-17/chapter-II/part-270/section-270.6c-11
2. SEC, "Exchange-Traded Funds: A Small Entity Compliance Guide": https://www.sec.gov/investment/exchange-traded-funds-small-entity-compliance-guide
3. SEC adopting release, 84 FR 57162 (24 Oct 2019): https://www.federalregister.gov/documents/2019/10/24/2019-21250/exchange-traded-funds
4. United States Natural Gas Fund 8-K filings, July 2009: https://www.sec.gov/Archives/edgar/data/0001376227/000114420409036281/v154295_8k.htm ; https://www.sec.gov/Archives/edgar/data/0001376227/000114420409048126/v160269_8k.htm
5. United States Oil Fund filings (CIK 1327068): 10-K FY2020 https://www.sec.gov/Archives/edgar/data/1327068/000110465921029202/uso-20201231x10k.htm ; 10-Q June 2020 https://www.sec.gov/Archives/edgar/data/1327068/000110465920091976/uso-20200630x10q.htm ; S-3/A https://www.sec.gov/Archives/edgar/data/1327068/000117120020000360/i20347_uso-s3a5.htm ; 10-K FY2024 https://www.sec.gov/Archives/edgar/data/1327068/000141057825000228/uso-20241231x10k.htm
6. BIS Bulletin No. 6 (Aramonte and Avalos, 14 Apr 2020): https://www.bis.org/publ/bisbull06.pdf
7. BIS Quarterly Review, 16 Mar 2026: https://www.bis.org/publ/qtrpdf/r_qt2603w.htm
8. SEBI circular on valuation of physical gold and silver (26 Feb 2026), PDF: https://www.sebi.gov.in/sebi_data/attachdocs/feb-2026/1772102397057.pdf
9. SEBI ETF price-band circular (15 Jun 2026) and extension (28 Aug 2026): see the archived v1 Research Document §12 for URLs (re-check in P01)
10. AMFI NAV download and NAV history pages: https://www.amfiindia.com/net-asset-value/nav-download ; https://www.amfiindia.com/net-asset-value/nav-history ; https://portal.amfiindia.com/spages/NAVAll.txt
11. SPDR Gold Shares (GLD) page with Historical Archive (XLSX): https://www.spdrgoldshares.com/usa/gld/
12. VanEck RSX page (liquidation notice): https://vaneck.com/us/en/investments/rsx/overview ; Business Wire, 4 Mar 2022: https://www.businesswire.com/news/home/20220304005480/en/
13. EIA NYMEX futures prices: https://www.eia.gov/dnav/pet/pet_pri_fut_s1_d.htm ; https://www.eia.gov/dnav/ng/NG_PRI_FUT_S1_W.htm
14. `bidask` package (EDGE estimator): https://pypi.org/project/bidask/

**Credible secondary**

15. etf.com on UNG 2009 and USO 2020: https://www.etf.com/node/71885.md
16. MSCI, "Bond ETFs and underlying price uncertainty": https://www.msci.com/research-and-insights/blog-post/bond-etfs-and-underlying-price-uncertainty ; S&P Global (8 Jul 2020): https://www.spglobal.com/ratings/en/research/articles/200708-credit-trends-how-etfs-contributed-to-liquidity-and-price-discovery-in-the-recent-market-dislocation-11508054 ; WealthManagement on bond-ETF discounts: https://www.wealthmanagement.com/etfs/under-market-stress-fixed-income-etfs-trade-with-wide-discount
17. Interactive Brokers Campus on RSX premium: https://www.interactivebrokers.com/campus/traders-insight/securities/stocks/how-to-fall-nearly-80-and-still-be-overvalued/ ; Bloomberg (8 Mar 2022): https://www.bloomberg.com/news/articles/2022-03-08/one-million-options-contracts-on-biggest-russia-etf-are-in-limbo
18. ETFstream on SLV's 2021 prospectus warning: https://www.etfstream.com/news/blackrock-adds-shortages-warning-to-world-s-largest-silver-etf-following-trading-frenzy/
19. Indian silver episode, Oct 2025: Moneylife https://moneylife.in/article/5-mutual-funds-freeze-silver-etf-subscriptions-as-prices-surge-and-physical-shortage-bites/78585.html ; Business Standard https://www.business-standard.com/amp/markets/news/silver-etfs-trade-at-steep-premiums-amid-global-supply-squeeze-125100901276_1.html ; Business Today https://www.businesstoday.in/mutual-funds/story/investors-would-be-overpaying-10-for-silver-if-nilesh-shah-after-kotak-amc-halts-new-investments-in-fof-497676-2025-10-10
20. SEBI gold/silver valuation change coverage: Business Standard https://www.business-standard.com/markets/news/sebi-gold-silver-valuation-mutual-funds-domestic-spot-prices-126022601142_1.html ; Angel One https://www.angelone.in/news/market-updates/sebi-mandates-exchange-spot-prices-for-valuation-of-gold-and-silver-held-by-mutual-funds ; Bigul https://bigul.co/blog/sebis-new-gold-silver-etf-valuation-rules-what-changes-from-april-1-2026
21. Direct-redemption triggers (AMC disclosures): ICICI Prudential https://arch.icicipruamc.com/Acceptance-of-Direct-Redemption-for-ETFs.aspx ; Nippon India https://mf.nipponindiaim.com/redemptionview
22. Overseas-cap stops: Business Standard (29 Jan 2022) https://business-standard.com/amp/article/markets/sebi-advises-mutual-funds-to-stop-subscriptions-into-overseas-funds-122012901071_1.html ; Business Standard (21 Mar 2024) https://business-standard.com/markets/news/sebi-directs-mutual-funds-to-stop-inflows-into-etf-based-overseas-schemes-124032101060_1.html ; Value Research https://valueresearchonline.com/stories/54675/sebi-halts-amcs-from-investing-in-overseas-etfs-starting-april-1
23. International ETF premiums: Business Today (26 Apr 2026) https://www.businesstoday.in/mutual-funds/story/global-etfs-mafang-sp-500-top-50-trade-at-20-premiums-whats-driving-the-surge-527464-2026-04-26 ; Cafemutual (Mirae caution) https://cafemutual.com/news/industry/38774-mirae-asset-warns-investors-about-overseas-etfs
24. Import-duty reporting (conflicting; verify via CBIC): https://www.newsbytesapp.com/news/business/union-budget-2026-no-change-in-gold-silver-import-duties/story ; https://www.iifl.com/blogs/gold-loan/how-union-budget-customs-duty-announcements-move-gold-prices-in-india

**Carried forward from the archived v1 research (not re-verified in this pass)**: SEBI MF master circular (20 Mar 2026), SEBI ETF band circulars (15 Jun and 28 Aug 2026), NSE circulars on ETF parameters and pre-open, Mirae product identifiers and SIDs, Feb 2026 crash chronology. See [`archive/v1_gold_silver_premium_forecaster/`](../../archive/v1_gold_silver_premium_forecaster/) §6 and §12 of the research document there.

---

## Change log

| Version | Date | Change | Decision |
|---|---|---|---|
| 1.0 | 2026-11-17 | First full edition | D-000 |
| 1.1 | 2026-11-17 | §4.1, §4.3: Indian NAV before Apr 2026 included a notional delivery premium (primary text). §9: pointer to P01 source results. | D-005, D-006 |

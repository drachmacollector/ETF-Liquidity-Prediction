# AI × ETF Flagship Project: Research Findings & Recommendation
**Prepared for:** Internship pitch to Umesh Kumar Daila, Head – ETF Sales, Mirae Asset Investment Managers (India)
**Objective:** Identify one technically sophisticated AI project, grounded in real research and data, that produces measurable results and is strategically relevant to Mirae's ETF distribution business.

---

## 1. Recommendation up front

Build **Project 2: iNAV Deviation & Liquidity-Stress Early-Warning System for Indian ETFs**, with the alt-data nowcasting model from Project 3 folded in as a leading-indicator module. This is the strongest single flagship: it has the best data feasibility, the clearest measurable KPIs, and it maps onto a live, named problem that Mirae's own ETF product head has been publicly quoted on in the last twelve months.

Project 1 (distribution/lead-generation intelligence) is the most *directly* relevant to a Head of Sales, and I'd pursue it as a fast follow-on or stretch add-on — but it has a real data-access problem in the Indian market that I explain honestly in Section 3, rather than papering over it.

The rest of this document is the evidence behind that call.

---

## 2. Grounding research: Mirae Asset India's ETF business and Umesh Daila's role

- Mirae Asset Investment Managers (India) runs roughly **$14.4B in mutual fund AUM**, with a passive/ETF lineup that has grown into thematic and sector products — Nifty India Internet, Nifty India New Age Consumption, Nifty Financial Services — alongside its gold and silver commodity ETFs, and it has been explicit that **passive is a stated strategic growth priority** alongside fixed income.
- Umesh Kumar Daila's title is confirmed as **Head, ETF – Sales**. Public evidence of his role is distribution- and education-facing, not portfolio management: he presented "**Meet the Manager: Inside the ETF Engine**" at the Morningstar Investment Conference (Nov 2025) — a session aimed at advisors and investors, not fund mechanics.
- Mirae's own **Head of ETF Product, Siddharth Srivastava**, was on record in March 2026 discussing gold/silver ETF inflow dynamics and **SEBI's proposed price bands for commodity ETFs** — a direct, current, company-specific hook.
- In October–November 2025, Indian silver ETFs (Nippon, HDFC, Tata, UTI) traded at **5–10%+ premiums to iNAV** during a physical-supply squeeze, prompting some AMCs to halt subscriptions. This is the exact "ETF price/NAV discrepancy" and "liquidity/market-making" problem class the brief asks for, playing out in Mirae's own product category within the last year.
- At the group level, Mirae Asset Securities (USA) has publicly discussed acting as an **Authorized Participant / Designated Liquidity Provider** for ETFs — so liquidity provision and premium/discount management is a theme the wider Mirae ETF franchise already cares about commercially, not just in India.
- Mirae's GIFT City IFSC branch recently launched a **$200M global fund targeting AI and semiconductor ETFs**, evidence the firm is comfortable with AI-as-investment-theme messaging — useful context for a pitch, though not the basis for the technical project itself.

**Implication for the pitch:** because Daila's job is distribution and advisor education rather than fund management, a project framed as "how do I decide who to call and when" or "how do I stop my sales desk from being blindsided by a liquidity/premium event in a flagship product" will land harder than a pure alpha-generation or portfolio-optimization pitch.

---

## 3. Ideas screened and rejected

Per the brief's instruction to be critical rather than exhaustive, these were considered and dropped — stated plainly so it's clear they weren't ignored by omission:

| Idea | Why it's out |
|---|---|
| **Next-day ETF return/price direction prediction (LSTM/RF on OHLC)** | This is the single most reproduced ETF-ML project on arXiv and GitHub (multiple near-identical papers found in this research, e.g. Piovezan & Andrade 2022, sector-ETF LSTM papers). Weak edge once transaction costs are included, no real novelty angle, exactly the "AI stock predictor" pattern the brief asks to avoid. |
| **Generic tracking-error prediction via regression** | Existing literature (Dobson 2020, replication-strategy studies) is largely descriptive/econometric, not a genuine ML modelling challenge, and the signal (expense ratio + replication method + market development) is already well explained by simple factors — little room for AI to add material value. |
| **HMM/regime-detection sector rotation** | Technically legitimate (Hamilton 1989 lineage), but now thoroughly commoditized — it's a stock indicator template on TradingView with dozens of near-identical public scripts. Not differentiated enough to be a resume centerpiece. |
| **Generic LLM chatbot over fund fact sheets ("RAG for ETFs")** | Explicitly excluded by the brief, and correctly so — the AI isn't the reason the product works; it's a UI over static documents. |
| **ETF portfolio optimizer (mean-variance + ML forecasts)** | Reproduced thousands of times, weak novelty, and portfolio construction is a fund-management/PM concern, not a sales/distribution one — poor fit for pitching a sales-org internship. |

---

## 4. Candidate Projects (evaluated in full)

### Project 1 — ETF Distribution Intelligence: Graph-Based Advisor & Distributor Lead Scoring

**Problem.** Sales teams at ETF issuers don't know, in a data-driven way, *which* distributors/advisors/institutional desks are most likely to add a given ETF next, and why. Current practice at most AMCs is relationship-driven and category-based ("similar funds to what they already hold").

**Existing work and gap.** The closest and best precedent is a **Fidelity Investments research paper** (Saxena, Kumar & Mishra, ACM ICAIF Workshop 2022, arXiv:2212.09624), "**Holder Recommendations using Graph Representation Learning & Link Prediction**." It builds a **bipartite graph of holders (funds/ETFs) and holders (institutional investors)** from quarterly **13F filings**, trains a **GraphSAGE** GNN + link-prediction MLP, and beats a cosine-similarity content-filtering baseline by an **absolute 42/22/14 percentage points** in Hits@Top-{50,100,200}, and by 18–19 points even on completely unseen (new) holders. This is a genuine, technically serious, directly on-topic precedent — GNNs applied to fund/ETF sales lead generation is a legitimately under-explored niche (the paper's own related-work section notes how little GML has been applied to this specific problem).

**The gap for India:** 13F filings are a **US-only SEC disclosure** (institutional holders >$100M AUM). There is **no Indian equivalent** — India has no public, holder-level ETF/fund ownership registry. This is exactly the brief's category-A opportunity ("studied in literature, but existing implementations are inaccessible for this market") — but it's a real constraint, not a solved problem, and I want to be upfront about it rather than assume it away.

**Feasible Indian adaptation.** Rather than holder-level 13F data, build the bipartite graph one level up, using data that *is* public in India:
- **Nodes:** distributor/RIA entities (or, more conservatively, distributor *categories* × geography) and ETF/scheme nodes.
- **Edges/features:** AMFI's monthly scheme-wise flow and investor-type data (individual vs. institutional, by AMC), SEBI-mandated AMC disclosure of commission paid to top distributors (published in scheme annual reports / AMC websites), NSE ETF trading-volume and AP-activity data, and scheme-level SIP/lump-sum mix.
- This turns the target from "which named institution will buy" (not answerable in India without 13F-equivalent data) into "which distributor **channel/geography/segment** is under-penetrated for a given ETF and is structurally similar to channels that adopted comparable ETFs" — a coarser but still genuinely useful and defensible prediction task.

**AI solution.** GraphSAGE (or a lighter GCN, given a likely much smaller graph than Fidelity's 5K holders / 2K products) for node embeddings, trained with a link-prediction MLP head exactly as in the reference paper; content-based cosine similarity as the baseline to beat, replicating their evaluation design (Hits@Top-K, tested against a look-ahead-bias-free holdout of newly active distributor-segments).

**Validation.** Point-in-time graph construction (train on quarter T, evaluate on T+1), a strict content-filtering baseline, and Hits@Top-K as the headline metric — directly reusing the reference paper's evaluation protocol so the results are comparable and defensible.

**Business value.** This is the most literal "sales lead generation" tool in the entire idea set — closest possible mapping to Daila's actual job description.

**Novelty/risk, honestly assessed.** High conceptual novelty (very few people apply GNN link prediction to fund distribution, and essentially nobody has done it publicly for India), but **execution risk is real**: coarsened, aggregate-level Indian data will produce a noisier, less impressive result than Fidelity's institution-level 13F graph. Don't oversell the granularity in the pitch — frame it explicitly as "adapting a proven US institutional-research technique to work within India's public-disclosure constraints," which is itself a legitimate research contribution.

**Evidence.**
- Saxena, Kumar & Mishra, *Holder Recommendations using Graph Representation Learning & Link Prediction*, ACM ICAIF Graph Learning & KG in Finance Workshop, 2022 — arxiv.org/abs/2212.09624
- Brogaard, Gerasimova & Liu, *Advising the Advisors: Evidence from ETFs*, SSRN 3972562 (cited by the above; model portfolios materially move ETF flows)
- Kostovetsky & Warner, *The Market for Fund Benchmarks: Evidence from ETFs*, SSRN 3804002
- AMFI monthly data releases (amfiindia.com) for scheme/investor-type flows

---

### Project 2 — iNAV Deviation & Liquidity-Stress Early-Warning System (RECOMMENDED FLAGSHIP)

**Problem.** Indian ETFs — especially commodity ETFs (gold, silver) and thinly-traded thematic ETFs — periodically trade at large premiums or discounts to their indicative NAV (iNAV) when Authorized Participant creation/redemption can't keep pace with demand or physical-asset supply. This is not hypothetical: in October–November 2025, silver ETFs from multiple large Indian AMCs traded **5–10%+ above iNAV**, several AMCs **halted new subscriptions**, and SEBI is actively **considering price bands for commodity ETFs** — a live regulatory debate on which Mirae's own Head of ETF Product has publicly commented. Retail investors buying at those premiums lose money the moment the premium reverts.

**Existing work and gap.** Academic and practitioner literature on ETF premium/discount and arbitrage efficiency is substantial for **US and Chinese markets** (spot-futures arbitrage ML for CSI 300 using LASSO/XGBoost/BPNN/LSTM; extensive market-microstructure literature on AP behavior and ETF arbitrage bounds), but:
- Almost none of it is India-specific.
- What exists on India is descriptive market commentary (financial press explaining *why* premiums happened after the fact), not a predictive, backtested early-warning model.
- This is squarely the brief's category-A/B opportunity: mature methodology elsewhere, fragmented pieces (time-series forecasting + market-microstructure theory + regulatory context), nobody has combined them into a live monitoring system for the Indian market specifically.

**AI solution.**
- **Core model:** gradient-boosted quantile regression (LightGBM/XGBoost quantile loss) or a temporal model (LSTM/Temporal Fusion Transformer) forecasting the **distribution** (not just point estimate) of next-session premium/discount-to-iNAV, so the output is a probabilistic early warning ("70% chance of >3% premium tomorrow"), not a single number.
- **Features:** underlying commodity spot-price momentum and volatility (gold/silver INR spot), historical AP creation/redemption unit volumes (where disclosed), ETF trading volume vs. 20-day average, bid-ask spread trends, and — because the Oct 2025 episode was explicitly driven by "festival season buying," per Nippon India's own ommodities head — a **seasonality/demand-surge feature layer** (this is where Project 3's nowcasting signal plugs in as a leading indicator, see below).
- **Secondary component:** an unsupervised anomaly-detection layer (isolation forest or autoencoder reconstruction error on the multivariate feature set) to flag premium/discount episodes that don't fit the learned "normal" regime at all — useful precisely because the biggest real-world events (like Oct 2025) are structural breaks, not smooth extrapolations of history.

**Data and feasibility.** Genuinely good, unlike Project 1. NSE/BSE daily bhavcopy and historical price data are scrapeable via existing open tooling (e.g., the `nser` R package and several PyPI NSE-scraper packages confirm this is a solved data-engineering problem, not a research risk); iNAV is published intraday by AMCs/exchanges for every listed ETF; domestic gold/silver spot prices are available from MCX and bullion-association sources; AMFI publishes monthly flow data as corroborating context.

**Validation.** Walk-forward backtesting (train on data up to time T, test strictly on T+1 onward — no shuffled train/test split, which would leak information across a serially correlated series), pinball loss for the quantile forecasts, precision/recall on "premium event" classification against a defined threshold (e.g., >2% deviation), and an explicit backtest of the **Oct–Nov 2025 silver premium episode** as an out-of-sample stress test — if the model would have flagged elevated risk in the days before that event using only information available at the time, that's a genuinely strong, citable result for a resume and an interview. Guard against look-ahead bias by using only data that would have been publicly available at each forecast timestamp, and against survivorship bias by including delisted/merged ETFs in the historical universe where feasible.

**Business value.** Multiple concrete uses for a sales/distribution desk: (1) an internal risk dashboard so RMs don't recommend a product mid-premium-spike, (2) a factual, data-backed talking point for advisors ("here's when it's a bad time to buy this ETF") that builds trust rather than just pushing product, (3) a potential input to Mirae's own AP/market-making conversations. This is the kind of tool an AMC's ETF desk would plausibly actually use.

**Novelty.** Genuinely differentiated — this is not a reproduced Kaggle project, it targets a market (India) with almost no published ML work on the topic, and it's validated against a real, named, dated market event rather than a synthetic backtest.

**Evidence.**
- Business Standard, "Silver ETFs trade at steep premiums amid physical supply shortage," Oct 2025
- Business Standard, interview with Siddharth Srivastava (Mirae Asset Head – ETF Product) on gold/silver ETF flows and SEBI's proposed price bands for commodity ETFs, Mar 2026
- Zhang & Cao et al., *Stock Index Spot–Futures Arbitrage Prediction Using Machine Learning Models*, PMC9601484 (methodological precedent: LASSO/XGBoost/BPNN/LSTM for arbitrage-signal prediction)
- Dobson, *ETFs tracking errors on global markets with consideration of regional diversity*, MPRA 103695 (baseline market-structure literature)
- `nser` CRAN package and NSE Python scrapers (confirms data feasibility)

---

### Project 3 — Alternative-Data Nowcasting of Retail ETF/Bullion Demand (feeds into Project 2)

**Problem.** AMFI's official flow data is published **monthly, with a lag** — by the time an AMC sees that retail gold/silver ETF demand spiked, the premium event may already be over. A leading indicator would let the sales/product desk (and the Project 2 model) see demand building in near-real time.

**Existing work and gap.** There's a real, credible academic line here: Da, Engelberg & Gao's foundational work on Google search volume as investor attention; **Chen, Chen, Lai & Yang (2023, Review of Pacific Basin Financial Markets & Policies)**, "*Investor Attention, Fee Structure, and Newly Issued Funds*," which finds Google Trends search-volume indices are **positively associated with fund inflows and (for equity funds) fund survival** — explicit precedent that this signal works for fund flows, not just stock returns; and the broader macro **nowcasting literature** (Giannone, Reichlin & Small) that establishes the mixed-frequency modelling techniques (e.g., MIDAS-style regression, dynamic factor models) needed to fuse a daily/weekly alt-data signal with a monthly official-data target. Nobody has applied this specifically to Indian gold/silver ETF flows, where the underlying demand is unusually narrative-driven (festival buying, price-rally chasing) and therefore plausibly *more* search-attention-sensitive than equity fund flows.

**AI solution.** An NLP + time-series nowcasting pipeline: Google Trends search-interest indices for gold/silver/ETF-buying queries, financial-news sentiment (headline-level sentiment scoring on Indian financial press), combined via a small dynamic-factor or gradient-boosted mixed-frequency model to nowcast the *direction and rough magnitude* of the next AMFI flow release, ahead of its publication — and, more importantly for the flagship, feed as a real-time input feature into Project 2's premium/discount model.

**Validation.** Standard nowcasting evaluation: compare nowcast-then-actual vs. naive (last-month-value) forecast, tested strictly on data available before each AMFI release date.

**Why it's a module, not a standalone flagship.** On its own, this is a solid, well-precedented but comparatively modest project — good methodology, real academic grounding, but a thinner "so what" for a sales pitch than Project 2. Bolted onto Project 2 as the demand-surge leading-indicator layer, it materially strengthens the flagship without diluting focus.

**Evidence.**
- Chen, Chen, Lai & Yang, *Investor Attention, Fee Structure, and Newly Issued Funds*, Review of Pacific Basin Financial Markets and Policies, 2023
- Da, Engelberg & Gao (foundational Google-search/investor-attention literature, referenced across the above)
- Giannone, Reichlin & Small, *Nowcasting: The real-time informational content of macroeconomic data*, Journal of Monetary Economics, 2008

---

## 5. Suggested build sequence (for handoff to an AI coding tool)

1. **Data layer:** scrape/store NSE bhavcopy + iNAV history for all listed Indian ETFs (start with the ~15–20 gold/silver/thematic ETFs where premium events are most common), MCX gold/silver spot, AMFI monthly flow releases.
2. **Baseline:** simple rolling-volatility threshold model for premium/discount — this is your baseline to beat, and it's what the "be critical about existing solutions" section of the pitch deck will reference.
3. **Core model (Project 2):** quantile GBM/LSTM on the engineered feature set; walk-forward backtest; explicit Oct–Nov 2025 silver-premium stress test.
4. **Nowcasting module (Project 3):** Google Trends + news-sentiment pipeline, fused as an additional feature into step 3, ablation-tested (does it actually improve the premium forecast, yes/no, by how much) — a clean, honest ablation result is more impressive than a vague "we used alt data" claim.
5. **Stretch (Project 1):** once the above is working and you have a working prototype to show, revisit the distribution-intelligence angle as a second, smaller module or a "future work" section in the pitch — it's the best story for Daila specifically, so it's worth having even a partial, honestly-caveated version ready to discuss.

---

## 6. What to say to Daila

> "I looked at what's actually breaking in the Indian ETF market right now — silver ETFs traded 5–10% over their iNAV last October, and SEBI is now considering price bands because of it. I built a model that forecasts the probability of that kind of premium event a day or more ahead, using only data that would have been publicly available at the time, and backtested it against that exact October episode. I also built a leading-indicator layer using search and news data, since your own team's public comments point to retail sentiment as the driver. I'd like to walk you through what it flagged, and talk about whether something like this would be useful to your desk or the product team."

That's a pitch built on a named, dated, verifiable event in Mirae's own product line — not a generic capstone project.

# P01 — Primary-text notes

Summaries of primary sources read in P01 (task T01.5), with the open question each one settles. Quotes are short and exact; full texts were read from the URLs given. Date read: 2026-11-17.

## 1. SEC Rule 6c-11: scope and the 2%/7-day disclosure → OQ-01 RESOLVED

Source: eCFR, 17 CFR 270.6c-11 (versioner API, text as of 2026-11-01): https://www.ecfr.gov/current/title-17/chapter-II/part-270/section-270.6c-11

- Definition: *"Exchange-traded fund means a registered open-end management company: (A) That issues (and redeems) creation units to (and from) authorized participants … and (B) Whose shares are listed on a national securities exchange and traded at market-determined prices."*
- **Consequence:** the rule covers only registered open-end management companies. It does **not** cover unit investment trusts (SPY, DIA, QQQ) or exchange-traded products that are not registered investment companies (commodity trusts and pools such as GLD, IAU, SLV, USO, UNG). This confirms Research Document §1.5 point 1 and §6.1 (grade upgraded from [K] to [V]).
- Website disclosure (paragraph (c)(1)(vi)): *"If the exchange-traded fund's premium or discount is greater than 2% for more than seven consecutive trading days, a statement … and a discussion of the factors … which must be maintained on the website for at least one year thereafter."*
- *"Market price means: (A) The official closing price … or (B) If it more accurately reflects the market value … at the time as of which the exchange-traded fund calculates current net asset value per share, the price that is the midpoint between the national best bid and national best offer as of that time."* Issuer-published premiums can therefore be closing-price based or NBBO-midpoint based. P08's cross-check must allow for this.

## 2. SEBI circular of 26 Feb 2026 on gold/silver valuation → OQ-14 RESOLVED; OQ-10 narrowed

Source: SEBI circular HO/(68)2026-IMD-POD-2/I/5780/2026, 26 Feb 2026 (2 pages): https://www.sebi.gov.in/sebi_data/attachdocs/feb-2026/1772102397057.pdf

- **Old method (para 1):** *"physical Gold and Silver held by Gold and Silver Exchange Traded Funds (ETFs) is valued at AM fixing prices of London Bullion Market Association (LBMA). The final valuation is arrived at after adjusting the LBMA prices with necessary metric and currency conversions, addition of transportation costs, customs duty, applicable taxes and levies and factoring notional premium or discount to arrive at domestic valuations."*
- **New method (para 3):** with effect from **1 April 2026**, *"mutual funds shall value physical Gold and Silver by using the polled spot prices published by the recognized stock exchanges which are used for settlement of physically delivered Gold and Silver derivatives contracts"*, complying with SEBI's spot-polling guidelines.
- **Para 4:** *"AMFI in consultation with SEBI shall prescribe a uniform policy in this regard."* The AMFI policy text (polling time, exchange choice) was not located in P01. It remains part of OQ-10, to be checked empirically in P08 (NAV vs MCX spot).
- **Correction to the Research Document (§4.1, §4.3):** the old NAV was not pure import parity. It included a "notional premium or discount". The Mirae Silver ETF SID (below) describes this as the premium "usually charged for delivery of silver to the place where it is stored", i.e., a delivery premium, not the domestic market's squeeze premium. Revised wording: before 1 Apr 2026, `NAV ≈ import parity + notional delivery premium`. Layer 1 inside NAV (`LP_NAV`) was small and slow-moving, not exactly zero. P08 estimates it empirically. Logged as decision D-005.

## 3. Mirae Asset Silver ETF SID (dated 30 Oct 2023) → OQ-16 RESOLVED; inception-date conflict (from the archived v1 research) settled

Source: https://www.miraeassetmf.co.in/docs/default-source/sid/sid_mirae-asset-silver-etf.pdf

- **Direct-redemption triggers (verbatim):** investors may redeem directly with the AMC *"without any exit load if: a. Traded price (closing price) of the ETF units is at discount of more than 1% to the day end NAV for 7 continuous trading days, or b. No quotes for such ETFs are available on stock exchange(s) for 3 consecutive trading days, or c. Total bid size on the exchange is less than half of creation units size daily, averaged over a period of 7 consecutive trading days."* Redemption requests received up to 3.00 p.m. are processed at that day's closing NAV. **System Specification §4.8 (`sebi_trigger`, `noquote_trigger`) is consistent.**
- **Valuation (old regime):** LBMA AM fixing plus conversions, duty and levies, *"Provided that the adjustment … may be made on the basis of a notional premium that is usually charged for delivery of silver to the place where it is stored on behalf of the Fund."*
- **Benchmark:** "Domestic Price of Physical Silver (based on London Bullion Market association (LBMA) Silver daily spot fixing price.)"
- **Inception date:** *"Inception date of the Scheme: June 09, 2023"* (settles the 9 vs 14 June conflict noted in the archived v1 research). The first AMFI NAV is dated 12 Jun 2023 (P01 probe).
- **Symbol at SID date:** "NSE Symbol: SILVRETF, BSE Scrip Code: 543922". The current NSE symbol in bhavcopy is `SILVERAG` (ISIN INF769K01KG6, P01 probe). The change date (reported as 15 Sep 2025) is verified in P02.
- **Primary market:** market makers create/redeem in creation-unit size at NAV-based prices; large investors may deal directly for more than ₹25 crore.
- **iNAV:** disclosed "on a continuous basis on NSE and BSE and will be updated depending upon the availability of the underlying price of silver".

## 4. NSE closing price → OQ-02 RESOLVED (with caveat)

Sources: Value Research, "NSE closing auction: how it works" (2026) https://www.valueresearchonline.com/stories/229255/nse-closing-auction-how-it-works-and-what-it-means-for-investors/ ; NewsOnAir (2 Aug 2026) https://newsonair.gov.in/nse-to-introduce-new-method-for-closing-price-discovery-through-closing-auction-session-from-tomorrow/

- Historically the NSE closing price is the volume-weighted average price of trades between 15:00 and 15:30 IST.
- From **3 Aug 2026**, a **closing auction session (CAS)** sets the close for stocks in the F&O segment. Other securities ("Category II") keep the 30-minute VWAP.
- **ETFs are not F&O underlyings**, so ETF closes are expected to remain 30-minute VWAPs [R]. Caveat: the exchange circular itself was not read. P05 flags 3 Aug 2026 as a possible break and checks it.

## 5. US NAV valuation clocks → OQ-06 partially RESOLVED

- **GLD / GLDM** (SPDR Gold "Historical Archive", column header): *"NAV/Share at 10:30am NYT"*. The archive also gives *"Indicative Price per Share at 4:15pm NYT"*, *"Mid point of bid/ask spread at 4:15pm NYT"* and the issuer premium (mid vs indicative value at 4:15pm). This is valuable: the issuer's own premium is computed at a matched clock (4:15pm), not against the 10:30am NAV. P08 uses it as a timing-robust cross-check for GLD.
- **SLV** (iShares fund page text): the page labels NAV as an early-morning New York value and notes that NAV *"prior to this date reflects the London Silver Fix benchmark"* (LBMA silver price at 12:00 London ≈ 07:00 New York). Exact wording to be copied into `reference/nav_clock.csv` in P02 from the prospectus.
- **USO/UNG:** USCF fund page: *"On April 28, 2020, there was a 1-for-8 reverse share split. Historical shares outstanding, net asset value per share has been adjusted to reflect the 1-for-8 reverse share split on a retroactive basis."* (also OQ-04: USCF NAV history is split-adjusted).
- Bond and equity ETFs: 16:00 ET (standard; prospectus check in P02).

## 6. Other facts confirmed in passing

- **EIA futures:** both crude (RCLC1–4) and natural gas (RNGC1–4) daily futures series end on **2024-04-05** (OQ-08: EIA confirmed discontinued). yfinance serves single NYMEX contracts (e.g., `CLZ26.NYM` from 2017, `NGZ26.NYM` from 2013), so a post-2024 front/second-month curve can be built from contract series (P06).
- **FRED ICE BofA high-yield OAS (`BAMLH0A0HYM2`)** starts 2023-11-20 on FRED (licensing). OQ-09 resolved: use `BAA10Y` (from 1986) and `AAA10Y`.
- **AMFI NAV upload time:** the AMFI API returns an upload timestamp per NAV (e.g., Mirae Silver ETF 12 Jun 2023 at 22:49 IST). Labelled "Z" but it is IST wall-clock time (it matches the display string). This gives an exact `known_at` for Indian NAVs, better than the 23:30 IST default in System Specification §7.
- **Rule 6c-11 coverage of iShares/SSGA open-end funds:** not needed for the label (we compute our own), noted only for the report.

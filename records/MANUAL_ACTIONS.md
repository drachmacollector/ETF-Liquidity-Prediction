# Manual Actions Tracker

Guides: [`docs/manual/`](../docs/manual/MI-00_Index.md). Workflow: [`docs/process/Documentation_Logging_and_Phase_Gates.md`](../docs/process/Documentation_Logging_and_Phase_Gates.md) §8.

Statuses: `NOT_NEEDED_YET` · `REQUESTED` · `IN_PROGRESS_USER` · `DONE` · `VERIFIED` · `DECLINED` · `NOT_APPLICABLE`

| MI | Title | Needed by | Required? | Status | Requested | Done | Verified | Items / notes |
|---|---|---|---|---|---|---|---|---|
| MI-01 | Commit policy; optional GitHub remote | P00 | Decision required | VERIFIED | 2026-11-17 | 2026-11-17 | 2026-11-17 | D-003: commit + push after every phase; simple messages. Remote `origin` = github.com/drachmacollector/ETF-Liquidity-Prediction (confirmed reachable, `main` in sync) |
| MI-02 | Tiingo API key | P01/P04 | Required (unless fallback chosen) | VERIFIED | 2026-11-17 | 2026-11-17 | 2026-11-17 | Key in `.env`; `/api/test` and `/tiingo/daily/gld` return 200 (needs `Content-Type: application/json`) |
| MI-03 | FRED API key | P06 | Optional | NOT_NEEDED_YET | | | | CSV downloads work without a key (P01) |
| MI-04 | Manual US issuer downloads | P04 | **Essential items required** (D-009) | VERIFIED (essentials) | 2026-11-17 | 2026-11-17 | 2026-11-17 | Rows 1–3 done and checked (USO, UNG from 2009-01-02; GREK from 2015-04-13, covers the 2015 Athens closure). Extra: BNO, CPER. Rows 4–10 remainder: no user action needed now; P04 tries them automatically (D-010) and re-requests only what fails |
| MI-05 | Manual India data downloads | P05 | Required for Layer 1 | VERIFIED | 2026-11-17 | 2026-11-17 | 2026-11-17 | MCX polled spot, Ahmedabad: gold (10 g) 2005-06-06 → 2026-11-17, 14,679 polls on 5,758 days; silver (1 kg) 2005-05-14 → 2026-11-17, 14,739 polls. IBJA 30-day PDF kept as a cross-check. Bhavcopy row (optional) not needed: NSE archive now scripted from 2007 (D-010) |
| MI-06 | WRDS/CRSP access check | P01/P04 | Optional | DECLINED | 2026-11-17 | 2026-11-17 | 2026-11-17 | User: institution not registered with WRDS. Decision D-011 (free sources only) |
| MI-07 | Data terms-of-use acceptance | P01 | Required | VERIFIED | 2026-11-17 | 2026-11-17 | 2026-11-17 | D-004: blanket research-use acceptance; sources prohibiting automation become manual-only; EDGAR uses a generic identifier. Summary for the record: `reports/data/terms_of_use_summary.md` |
| MI-08 | Incident catalogue review | P03 (entry condition of P12, D-016) | Required | REQUESTED | 2026-11-18 | | | Review `reports/catalogue/catalogue_report.md` and `reference/incidents.csv` (24 incidents, 48 operational events). Two pass-1/pass-2 disagreements to decide: INC-US-2022-RUSSIA (CRE vs STL), INC-IN-2020-COVID (LIQ vs MKT). Reply "Approved as is" or a list of changes (guide MI-08) |
| MI-09 | India duty and regulatory fact verification | P02 | Required for flagged rows | REQUESTED | 2026-11-17 | | | 11 items (D1–D7, B1–B4) below. Does not block P03–P06; unverified periods are left out of Layer 1 / lock classification until confirmed |
| MI-10 | Stakeholder validation conversation | P11 | Optional | NOT_NEEDED_YET | | | | |
| MI-11 | Pre-registration sign-off; lockbox authorisation | P13→P14 | Required (hard gate) | NOT_NEEDED_YET | | | | |
| MI-12 | Brief wording review; final sign-off; optional hosting | P16/P17 | Review required | NOT_NEEDED_YET | | | | |

## Item lists

### MI-04 — US fund NAV histories (requested 2026-11-17)

Guide: [`docs/manual/MI-04_Manual_US_Issuer_Downloads.md`](../docs/manual/MI-04_Manual_US_Issuer_Downloads.md). Save each file **without opening and re-saving it in Excel**. Put it in the folder shown, keeping the ticker at the start of the file name. Download the longest history offered.

| # | Priority | Ticker(s) | Where | What to click | Save to | Done |
|---|---|---|---|---|---|---|
| 1 | **Essential** | USO | https://www.uscfinvestments.com/uso | "Download Historical NAV Performance" (CSV, e.g. `uso-historicalnav-YYYYMMDD.csv`) | `data/manual_drop/us_iss_uscf/` | [x] 2026-11-17 |
| 2 | **Essential** | UNG | https://www.uscfinvestments.com/ung | same button | `data/manual_drop/us_iss_uscf/` | [x] 2026-11-17 |
| 3 | **Essential** | GREK | https://www.globalxetfs.com/funds/grek/ | NAV / price history download (longest range) | `data/manual_drop/us_iss_globalx/` | [x] 2026-11-17 (premium/discount file; NAV = price − premium) |
| 4 | High | BNO, UGA, USL, UNL | https://www.uscfinvestments.com/bno (then /uga, /usl, /unl) | same button | `data/manual_drop/us_iss_uscf/` | BNO [x]; others → P04 automation |
| 5 | Medium | CPER, USCI | https://www.uscfinvestments.com/cper , /usci | same button | `data/manual_drop/us_iss_uscf/` | CPER [x]; USCI → P04 automation |
| 6 | Medium | ASHR | https://etf.dws.com/en-us/ASHR-harvest-csi-300-china-a-shares-etf/ | NAV history download | `data/manual_drop/us_iss_xtrackers/` | [ ] |
| 7 | Medium | DBC, DBA, DBO, BKLN | invesco.com/us fund pages | "Prices & Performance" → historical NAV/price | `data/manual_drop/us_iss_invesco/` | [ ] |
| 8 | Medium | SIVR, PPLT, PALL | abrdn US ETF pages (search "abrdn Silver ETF Trust SIVR") | NAV history download | `data/manual_drop/us_iss_abrdn/` | [ ] |
| 9 | Low | CORN, WEAT, SOYB | teucrium.com fund pages | NAV history | `data/manual_drop/us_iss_teucrium/` | [ ] |
| 10 | Lowest (optional) | BND, VOO | investor.vanguard.com fund pages | "Price & performance" → historical prices (NAV and market price) | `data/manual_drop/us_iss_vanguard/` | [ ] |

Rows 6–10 and the rest of rows 4–5: **no action needed now** — P04 tries them automatically (D-010).

When done, tell the agent which rows you completed (e.g., "MI-04 rows 1–5 done"). If a site offers only recent history, download what is there and say so.

### MI-05 — Indian domestic gold and silver price history (requested 2026-11-17)

Guide: [`docs/manual/MI-05_Manual_India_Data_Downloads.md`](../docs/manual/MI-05_Manual_India_Data_Downloads.md).

| # | Priority | What | Where | Save to | Done |
|---|---|---|---|---|---|
| 1 | **Required** ✔ | Domestic **gold** daily price history, as far back as offered (ideally 2007 → today) | MCX "Spot Market Price" (or MCX Bhavcopy near-month GOLD futures); otherwise IBJA rates | `data/manual_drop/in_spot/` named `MCX_GOLD_<spot-or-bhav>_<from>_<to>.<ext>` or `IBJA_GOLD_<AM-or-PM>_<from>_<to>.<ext>` | [ ] |
| 2 | **Required** | Domestic **silver** daily price history (ideally 2021 → today; earlier if easy) | same | `data/manual_drop/in_spot/` with `SILVER` in the name | [ ] |
| 3 | Optional | NSE bhavcopy for 2010–2015 (only if you want pre-2016 Indian prices beyond yfinance) | NSE "All Reports" archives | `data/manual_drop/in_bhav/` | [ ] |

Tell the agent which source you used and the earliest date you could get.

### MI-06 — WRDS/CRSP check (optional, requested 2026-11-17)

Reply "WRDS: yes" or "WRDS: no" after checking with your institution (guide: [`docs/manual/MI-06_WRDS_CRSP_Access_Check.md`](../docs/manual/MI-06_WRDS_CRSP_Access_Check.md)). If yes, the agent will send the exact query specification.

### MI-09 — India import-duty and price-band facts (requested 2026-11-17)

Guide: [`docs/manual/MI-09_India_Duty_and_Regulatory_Fact_Verification.md`](../docs/manual/MI-09_India_Duty_and_Regulatory_Fact_Verification.md). The agent confirmed the 2012, 2019, 2021, 2023 and 2024 Budget changes and the NSE September 2026 band rules from primary documents. These items rest only on press reports or listings. Reply one line per item: `D3: confirmed`, `D6: corrected to 1 Jul 2022`, or `could not confirm`, with the URL you used. CBIC's notification site does not answer scripts; the gazette (https://egazette.gov.in) or CBIC (https://taxinformation.cbic.gov.in) usually has the notification text.

| Item | Table / row | Fact to confirm | Where to look |
|---|---|---|---|
| D1 | `duty_india` gold & silver 2007-01-01 → 2012-01-16 | Specific duties before 17 Jan 2012 (gold Rs per 10 g; silver Rs per kg) and the dates they changed (reported: gold Rs 100 → 200 → 300; silver Rs 1,000 → 1,500) | Budget speeches 2008–2011; CBIC tariff notifications |
| D2 | gold 2012-01-17 → 2012-03-16 (2%); silver 2012-01-17 → 2013-08-12 (6%) | Notification 02/2012-Customs (16 Jan 2012, in force 17 Jan 2012): gold 2%, silver 6% ad valorem | CBIC / e-gazette |
| D3 | gold 2013-01-21 → 2013-06-04 | Gold 4% → 6% from 21 Jan 2013 (notification number) | CBIC / e-gazette |
| D4 | gold 2013-06-05 → 2013-08-12 | Gold 6% → 8% from 5 Jun 2013 | CBIC / e-gazette |
| D5 | gold & silver 2013-08-13 → 2019-07-05 | 10% from 13 Aug 2013; whether education cess or SWS added to the effective rate in 2013–2019 | CBIC / e-gazette |
| D6 | gold 2022-06-30 → 2024-07-23 | Notification 33/2022-Customs: effective 30 Jun or 1 Jul 2022; total 15% (12.5% BCD + 2.5% AIDC, SWS nil) | CBIC / e-gazette / PIB |
| D7 | gold & silver from 2026-05-13 | Reported Notification 16/2026-Customs: 10% BCD + 5% AIDC = 15% from 13 May 2026 | CBIC / e-gazette / PIB |
| B1 | `band_regimes_india` NSE & BSE, all groups, 2007-01-01 → 2026-09-06 | Before Sep 2026: fixed ±20% band on T-2 NAV — since when, and whether it differed earlier | NSE/BSE circulars (ETF price bands) |
| B2 | NSE `international` from 2026-09-07 | Whether overseas equity ETFs follow the equity rule (±10%, 5% flex to ±20%) under NSE circular 122/2026 (OQ-11) | NSE circular 122/2026; SEBI circulars of 15 Jun and 28 Aug 2026 |
| B3 | BSE `gold_silver` 2026-02-01 and 2026-02-02 → 2026-09-06 | BSE moved gold/silver ETF bands to T-1 NAV on Sunday 1 Feb 2026 "for today only"; reverted on 2 Feb? Did NSE do the same? | BSE notices of 1 Feb 2026; NSE circulars |
| B4 | BSE `gold_silver` from 2026-09-07 | BSE circular implementing the same SEBI rules (date, bands) | BSE notices |

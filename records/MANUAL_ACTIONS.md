# Manual Actions Tracker

Guides: [`docs/manual/`](../docs/manual/MI-00_Index.md). Workflow: [`docs/process/Documentation_Logging_and_Phase_Gates.md`](../docs/process/Documentation_Logging_and_Phase_Gates.md) §8.

Statuses: `NOT_NEEDED_YET` · `REQUESTED` · `IN_PROGRESS_USER` · `DONE` · `VERIFIED` · `DECLINED` · `NOT_APPLICABLE`

| MI | Title | Needed by | Required? | Status | Requested | Done | Verified | Items / notes |
|---|---|---|---|---|---|---|---|---|
| MI-01 | Commit policy; optional GitHub remote | P00 | Decision required | VERIFIED | 2026-11-17 | 2026-11-17 | 2026-11-17 | D-003: commit + push after every phase; simple messages. Remote `origin` = github.com/drachmacollector/ETF-Liquidity-Prediction (confirmed reachable, `main` in sync) |
| MI-02 | Tiingo API key | P01/P04 | Required (unless fallback chosen) | VERIFIED | 2026-11-17 | 2026-11-17 | 2026-11-17 | Key in `.env`; `/api/test` and `/tiingo/daily/gld` return 200 (needs `Content-Type: application/json`) |
| MI-03 | FRED API key | P06 | Optional | NOT_NEEDED_YET | | | | CSV downloads work without a key (P01) |
| MI-04 | Manual US issuer downloads | P04 | **Essential items required** (D-009) | REQUESTED | 2026-11-17 | | | Item list below. Essential: USO, UNG, GREK. Entry condition for completing P04 |
| MI-05 | Manual India data downloads | P05 | Required for Layer 1 | REQUESTED | 2026-11-17 | | | Item list below (domestic gold/silver spot history) |
| MI-06 | WRDS/CRSP access check | P01/P04 | Optional | REQUESTED | 2026-11-17 | | | Would recover RSX/EGPT/ERUS NAV (I-005), USO/UNG shares (I-001) and real bid/ask. Reply "WRDS: yes/no" |
| MI-07 | Data terms-of-use acceptance | P01 | Required | VERIFIED | 2026-11-17 | 2026-11-17 | 2026-11-17 | D-004: blanket research-use acceptance; sources prohibiting automation become manual-only; EDGAR uses a generic identifier. Summary for the record: `reports/data/terms_of_use_summary.md` |
| MI-08 | Incident catalogue review | P03 | Required | NOT_NEEDED_YET | | | | |
| MI-09 | India duty and regulatory fact verification | P02 | Required for flagged rows | NOT_NEEDED_YET | | | | Item list added by P02 |
| MI-10 | Stakeholder validation conversation | P11 | Optional | NOT_NEEDED_YET | | | | |
| MI-11 | Pre-registration sign-off; lockbox authorisation | P13→P14 | Required (hard gate) | NOT_NEEDED_YET | | | | |
| MI-12 | Brief wording review; final sign-off; optional hosting | P16/P17 | Review required | NOT_NEEDED_YET | | | | |

## Item lists

### MI-04 — US fund NAV histories (requested 2026-11-17)

Guide: [`docs/manual/MI-04_Manual_US_Issuer_Downloads.md`](../docs/manual/MI-04_Manual_US_Issuer_Downloads.md). Save each file **without opening and re-saving it in Excel**. Put it in the folder shown, keeping the ticker at the start of the file name. Download the longest history offered.

| # | Priority | Ticker(s) | Where | What to click | Save to | Done |
|---|---|---|---|---|---|---|
| 1 | **Essential** | USO | https://www.uscfinvestments.com/uso | "Download Historical NAV Performance" (CSV, e.g. `uso-historicalnav-YYYYMMDD.csv`) | `data/manual_drop/us_iss_uscf/` | [ ] |
| 2 | **Essential** | UNG | https://www.uscfinvestments.com/ung | same button | `data/manual_drop/us_iss_uscf/` | [ ] |
| 3 | **Essential** | GREK | https://www.globalxetfs.com/funds/grek/ | NAV / price history download (longest range) | `data/manual_drop/us_iss_globalx/` | [ ] |
| 4 | High | BNO, UGA, USL, UNL | https://www.uscfinvestments.com/bno (then /uga, /usl, /unl) | same button | `data/manual_drop/us_iss_uscf/` | [ ] |
| 5 | Medium | CPER, USCI | https://www.uscfinvestments.com/cper , /usci | same button | `data/manual_drop/us_iss_uscf/` | [ ] |
| 6 | Medium | ASHR | https://etf.dws.com/en-us/ASHR-harvest-csi-300-china-a-shares-etf/ | NAV history download | `data/manual_drop/us_iss_xtrackers/` | [ ] |
| 7 | Medium | DBC, DBA, DBO, BKLN | invesco.com/us fund pages | "Prices & Performance" → historical NAV/price | `data/manual_drop/us_iss_invesco/` | [ ] |
| 8 | Medium | SIVR, PPLT, PALL | abrdn US ETF pages (search "abrdn Silver ETF Trust SIVR") | NAV history download | `data/manual_drop/us_iss_abrdn/` | [ ] |
| 9 | Low | CORN, WEAT, SOYB | teucrium.com fund pages | NAV history | `data/manual_drop/us_iss_teucrium/` | [ ] |
| 10 | Lowest (optional) | BND, VOO | investor.vanguard.com fund pages | "Price & performance" → historical prices (NAV and market price) | `data/manual_drop/us_iss_vanguard/` | [ ] |

When done, tell the agent which rows you completed (e.g., "MI-04 rows 1–5 done"). If a site offers only recent history, download what is there and say so.

### MI-05 — Indian domestic gold and silver price history (requested 2026-11-17)

Guide: [`docs/manual/MI-05_Manual_India_Data_Downloads.md`](../docs/manual/MI-05_Manual_India_Data_Downloads.md).

| # | Priority | What | Where | Save to | Done |
|---|---|---|---|---|---|
| 1 | **Required** | Domestic **gold** daily price history, as far back as offered (ideally 2007 → today) | MCX "Spot Market Price" (or MCX Bhavcopy near-month GOLD futures); otherwise IBJA rates | `data/manual_drop/in_spot/` named `MCX_GOLD_<spot-or-bhav>_<from>_<to>.<ext>` or `IBJA_GOLD_<AM-or-PM>_<from>_<to>.<ext>` | [ ] |
| 2 | **Required** | Domestic **silver** daily price history (ideally 2021 → today; earlier if easy) | same | `data/manual_drop/in_spot/` with `SILVER` in the name | [ ] |
| 3 | Optional | NSE bhavcopy for 2010–2015 (only if you want pre-2016 Indian prices beyond yfinance) | NSE "All Reports" archives | `data/manual_drop/in_bhav/` | [ ] |

Tell the agent which source you used and the earliest date you could get.

### MI-06 — WRDS/CRSP check (optional, requested 2026-11-17)

Reply "WRDS: yes" or "WRDS: no" after checking with your institution (guide: [`docs/manual/MI-06_WRDS_CRSP_Access_Check.md`](../docs/manual/MI-06_WRDS_CRSP_Access_Check.md)). If yes, the agent will send the exact query specification.

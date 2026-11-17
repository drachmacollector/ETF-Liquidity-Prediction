# Manual Actions Tracker

Guides: [`docs/manual/`](../docs/manual/MI-00_Index.md). Workflow: [`docs/process/Documentation_Logging_and_Phase_Gates.md`](../docs/process/Documentation_Logging_and_Phase_Gates.md) §8.

Statuses: `NOT_NEEDED_YET` · `REQUESTED` · `IN_PROGRESS_USER` · `DONE` · `VERIFIED` · `DECLINED` · `NOT_APPLICABLE`

| MI | Title | Needed by | Required? | Status | Requested | Done | Verified | Items / notes |
|---|---|---|---|---|---|---|---|---|
| MI-01 | Commit policy; optional GitHub remote | P00 | Decision required | VERIFIED | 2026-11-17 | 2026-11-17 | 2026-11-17 | D-003: commit + push after every phase; simple messages. Remote `origin` = github.com/drachmacollector/ETF-Liquidity-Prediction (confirmed reachable, `main` in sync) |
| MI-02 | Tiingo API key | P01/P04 | Required (unless fallback chosen) | VERIFIED | 2026-11-17 | 2026-11-17 | 2026-11-17 | Key in `.env`; `/api/test` and `/tiingo/daily/gld` return 200 (needs `Content-Type: application/json`) |
| MI-03 | FRED API key | P06 | Optional | NOT_NEEDED_YET | | | | |
| MI-04 | Manual US issuer downloads | P04 | Conditional | NOT_NEEDED_YET | | | | File list added by P01 |
| MI-05 | Manual India data downloads | P05 | Conditional | NOT_NEEDED_YET | | | | File/date list added by P01 |
| MI-06 | WRDS/CRSP access check | P01/P04 | Optional | NOT_NEEDED_YET | | | | |
| MI-07 | Data terms-of-use acceptance | P01 | Required | VERIFIED | 2026-11-17 | 2026-11-17 | 2026-11-17 | D-004: blanket research-use acceptance; sources prohibiting automation become manual-only; EDGAR uses a generic identifier |
| MI-08 | Incident catalogue review | P03 | Required | NOT_NEEDED_YET | | | | |
| MI-09 | India duty and regulatory fact verification | P02 | Required for flagged rows | NOT_NEEDED_YET | | | | Item list added by P02 |
| MI-10 | Stakeholder validation conversation | P11 | Optional | NOT_NEEDED_YET | | | | |
| MI-11 | Pre-registration sign-off; lockbox authorisation | P13→P14 | Required (hard gate) | NOT_NEEDED_YET | | | | |
| MI-12 | Brief wording review; final sign-off; optional hosting | P16/P17 | Review required | NOT_NEEDED_YET | | | | |

## Item lists

_(When an MI is requested, the agent writes its exact item list here, e.g., the files to download, and ticks items off as they are verified.)_

# MI-06 — WRDS / CRSP Access Check (optional upgrade)

| Field | Value |
|---|---|
| Needed by phase | P01 (decision), P04 (data) |
| Required or optional | Optional. Useful if issuer NAV histories are incomplete, and it provides real daily closing bid/ask quotes to validate the spread estimator |
| Estimated user time | 15 minutes, plus waiting for your institution |
| What you will need | Your institutional email/login |

## Why this needs you

CRSP (via Wharton Research Data Services, WRDS) is licensed per institution. Only you can check whether your institution subscribes and request an account.

## Step-by-step

1. Ask your institution's library or finance department: "Do we subscribe to WRDS, and does the subscription include the CRSP US Stock database and the CRSP Survivor-Bias-Free US Mutual Fund database?"
2. If yes: go to https://wrds-www.wharton.upenn.edu → **Register** → choose your institution → request a **student/academic** account with your institutional email. Wait for approval.
3. Once approved, tell the agent. The agent will write the exact query specification (tickers/PERMNOs, fields: date, PRC, BID, ASK, VOL, SHROUT, and for funds daily NAV where available; date range) for you to run in the WRDS web query form, and the export settings (CSV, comma-delimited, dates as YYYY-MM-DD).
4. Run the queries, download the CSV files, and place them in `data/manual_drop/crsp/` named `crsp_<dataset>_<YYYYMMDD>.csv`.
5. Check your institution's licence terms: data must not be redistributed; the repository will not contain the raw files (they stay in the gitignored `data/` folder).

## What to give the agent

"WRDS available: yes/no". If yes, the CSV files in the folder.

## What the agent does next

If no: records decision "no CRSP" and continues with free sources. If yes: implements the `us_crsp` adapter (P04 T04.4), uses CRSP as a second NAV source and the bid/ask closes to validate the EDGE spread estimator (P10 assumption AS-04).

## If something goes wrong

Access can take days; the project does not wait for it. CRSP is added later if it arrives before P07 completes; afterwards it is used only for validation, not to change curated data (to keep evaluation stable).

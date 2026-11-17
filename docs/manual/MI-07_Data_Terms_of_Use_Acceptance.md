# MI-07 — Data Terms of Use: Review and Acceptance

| Field | Value |
|---|---|
| Needed by phase | End of P01; entry condition for P04, P05, P06 |
| Required or optional | Required |
| Estimated user time | 15–20 minutes |

## Why this needs you

Accepting the terms of a data source is your decision, not the agent's. The project uses data for non-commercial research and a demonstration; some sources restrict automated access or redistribution.

## Step-by-step

1. Open `reports/data/terms_of_use_summary.md` (the agent writes it in P01). For each source it lists the terms URL, what is allowed, any restrictions, and how the project plans to use the source.
2. For any source where you want more detail, open its terms URL and read the relevant sections (automated access, personal/research use, redistribution, attribution).
3. Decide, for each source: **Accept** (use as planned), **Accept manual-only** (no scripted downloads; manual downloads via MI-04/MI-05), or **Reject** (do not use).
4. Also decide the **SEC EDGAR user agent**: EDGAR asks automated clients to identify themselves with contact information. Choose: (a) use a generic project identifier only (may be rejected; filings then fetched by hand in P03), or (b) provide a contact email *you* choose for that header. The agent will not use your email unless you say so here.
5. Reply to the agent with a short list, e.g.:
   ```
   Tiingo: accept · Stooq: accept · yfinance: accept (fallback only) · iShares: manual-only · NSE archives: accept ·
   AMFI: accept · mfapi.in: accept · MCX: manual-only · IBJA: manual-only · FRED: accept · EIA: accept ·
   EDGAR: generic identifier only
   ```

## How to check it worked

The agent records your list in `records/DECISIONS.md` and `reference/source_registry.csv` (column `user_acceptance`).

## What the agent does next

Configures each source accordingly (disables scripted access for manual-only or rejected sources), adds a "Data terms" section to the data card in P17, and marks MI-07 VERIFIED.

## Guidance (not legal advice)

- Research use and no redistribution of raw data are the safe defaults. The repository never contains raw vendor files.
- Outputs shown to Mirae Asset (charts, aggregated statistics) are derived results; if anything is to be published externally, re-check the terms then.

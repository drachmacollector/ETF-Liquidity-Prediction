# MI-09 — Verification of India Import-Duty Rows and Regulatory Facts

| Field | Value |
|---|---|
| Needed by phase | P02 (duty and band-regime tables); P01 primary-text items the agent could not read |
| Required or optional | Required for the rows the agent flags (`verified = n`) |
| Estimated user time | 20–60 minutes |

## Why this needs you

Some official sites (CBIC, SEBI, exchanges) block automated reading or publish only scanned PDFs, and press reports conflict (e.g., whether the February 2026 Budget changed gold and silver import duty, and whether a further change happened in May 2026). A wrong duty rate corrupts the Layer-1 analysis, so unverified periods are left out until confirmed.

## Step-by-step

1. Open the list the agent writes in `records/MANUAL_ACTIONS.md` under MI-09 (each item: table, row, the fact to confirm, suggested sources).
2. For **duty rows**: search the CBIC customs notifications (https://www.cbic.gov.in → Customs → Notifications) or the Budget documents (https://www.indiabudget.gov.in) for the notification that changed the basic customs duty and AIDC on gold/silver bars and doré around the date in question. Note: notification number, date, effective date, and the rates.
3. For **band-regime rows**: open the exchange circular named in the row (NSE: https://www.nseindia.com/resources/exchange-communication-circulars; BSE: https://www.bseindia.com/markets/MarketInfo/NoticesCirculars.aspx) and confirm the base price rule and band percentages and the effective date.
4. For **regulatory text items** (e.g., SEBI circular of 26 Feb 2026 on valuation; direct-redemption trigger wording): open the SEBI page/PDF and confirm the quoted rule.
5. Reply with one line per item: `<item id>: confirmed | corrected to <value> | could not confirm`, plus the URL you used.

## What the agent does next

Updates the rows (`verified = y` with your source URL, or leaves `n`), logs a decision for each correction, re-runs `esw reference validate`, and marks MI-09 VERIFIED. Rows still unconfirmed remain excluded from Layer 1 / lock classification and are listed in the limitations.

# MI-08 — Incident Catalogue Review and Sign-off

| Field | Value |
|---|---|
| Needed by phase | P03 (before P03 is VERIFIED) |
| Required or optional | Required |
| Estimated user time | 45–90 minutes |

## Why this needs you

The incident catalogue's mechanism labels are the ground truth for testing the root-cause explainer. They must be set by people reading the evidence, **before** any model exists, and an independent human check makes them credible.

## Step-by-step

1. Open `reports/catalogue/catalogue_report.md` for the overview, then `reference/incidents.csv` (Excel is fine for reading; **do not save** from Excel — make edits in the agent session or in a text editor).
2. For each incident, check:
   - Is the **primary family** right? (`CRE` creation constraint, `STL` stale NAV, `UND` underlying squeeze/local premium, `LIQ` liquidity drain, `DEM` demand surge, `MKT` market-wide stress — definitions in Research Document §3.)
   - Are the dates plausible (onset, peak, end)?
   - Is it correctly marked as a **near-miss** where nothing persistent happened (e.g., SLV February 2021)?
3. Skim `reference/operational_events.csv`: do the `known_at` dates look like publication dates (not effective dates)?
4. Reply to the agent with either "Approved as is" or a list of changes in this form:
   ```
   INC-US-2013-TAPER: primary family STL → MKT (reason: …)
   INC-IN-2020-COVID: drop (reason: not a documented incident)
   ```

## What the agent does next

Applies your changes, records each as a decision ("Decided by: user"), recomputes agreement statistics (agent vs user) for the report, and marks MI-08 VERIFIED. After this, the labels are only changed through a logged decision, and never after P12 begins.

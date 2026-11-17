# MI-03 — FRED API Key (optional)

| Field | Value |
|---|---|
| Needed by phase | P06 (market-wide series), P16 (refresh) |
| Required or optional | Optional. FRED's CSV download (`fredgraph.csv`) works without a key; the API is more robust for many series |
| Estimated user time | 5 minutes |

## Step-by-step

1. Go to https://fred.stlouisfed.org and click **My Account** → **Create New Account** (or sign in).
2. Go to https://fredaccount.stlouisfed.org/apikeys and click **Request API Key**. Enter a short description such as "Research project on ETF pricing (non-commercial)". Accept the terms.
3. Copy the 32-character key. Add to `.env`:
   ```
   FRED_API_KEY=<key>
   ```
4. Tell the agent "FRED key added".

## How to check it worked

`.env` has the line; `git status` does not list `.env`.

## What the agent does next

Runs a single API call for `VIXCLS`, records success in the probe matrix, switches the FRED adapter to API mode, sets MI-03 → VERIFIED.

## If something goes wrong

If the key is rejected, regenerate it on the API keys page. If you skip this MI, nothing breaks; the agent uses CSV downloads.

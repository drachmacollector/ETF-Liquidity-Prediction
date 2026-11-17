# MI-02 — Tiingo API Key (US daily prices)

| Field | Value |
|---|---|
| Needed by phase | P01 (probe), P04 (backfill), P16 (daily refresh) |
| Required or optional | Required, unless you and the agent agree in P01 to use a fallback source (Stooq/yfinance) as primary |
| Estimated user time | 10 minutes |
| What you will need | An email address for the Tiingo account |

## Why this needs you

Tiingo provides clean, unadjusted daily US prices through a stable API, but it needs a personal account and an API token, and its terms must be accepted by you.

## Step-by-step

1. Go to https://www.tiingo.com and click **Sign Up** (top right). Create a free account and confirm your email.
2. Sign in. Open your account menu → **API** (or go directly to https://www.tiingo.com/account/api/token).
3. Copy the token shown on that page (a long string of letters and numbers).
4. In the repository root, open `.env` (create it by copying `.env.example` if the agent has not done so) and set:
   ```
   TIINGO_API_KEY=<paste the token here>
   ```
   Save the file. Do not paste the token into the chat.
5. Read Tiingo's terms of use and pricing page for the free tier (limits on requests per hour/day and unique symbols per month). Tell the agent "Tiingo key added; terms read". If you have a paid plan, say so (it changes rate limits).

## What to give the agent

- Nothing in chat except the confirmation sentence. The key lives in `.env`.

## How to check it worked (you)

- `.env` contains a line starting with `TIINGO_API_KEY=` followed by your token.
- `git status` does **not** list `.env` (it is gitignored).

## What the agent does next

1. Runs `python -m esw doctor` (shows `TIINGO_API_KEY: set`, never the value).
2. Runs the P01 Tiingo probe for five tickers and records history depth and rate limits in the probe matrix.
3. Sets MI-02 → VERIFIED; resumes P01/P04.

## If something goes wrong

| Problem | What to do |
|---|---|
| Probe returns 401/403 | Re-copy the token (no spaces or quotes); regenerate it on the token page if needed |
| Free-tier limits too tight for the universe | The agent will batch downloads over several days or use fallbacks; you may decide to upgrade (optional) |
| You prefer not to create an account | Tell the agent; it will use Stooq/yfinance as primary with cross-checks and log decision D-0xx |

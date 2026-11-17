# MI-05 — Manual Downloads of Indian Data (domestic gold/silver spot; NSE files if blocked)

| Field | Value |
|---|---|
| Needed by phase | P05 (identified in P01) |
| Required or optional | **Conditional.** Domestic spot history (MCX or IBJA) is likely needed by hand. NSE bhavcopy files only if automated access fails for some date ranges |
| Estimated user time | 20–60 minutes |
| What you will need | A web browser; possibly a free registration on the MCX or IBJA website |

## Why this needs you

The Layer-1 analysis (domestic vs global metal price, Research Document §4.3) needs a history of Indian domestic gold and silver prices. Exchange and association websites often provide these only through interactive pages.

## Part A — Domestic spot history (MCX preferred, IBJA as alternative)

**Option A1: MCX**

1. Go to https://www.mcxindia.com and open **Market Data**. Look for **Spot Market Price** (polled spot prices) or **Bhavcopy** (daily settlement of futures).
2. For **Spot Market Price**: select commodity **GOLD** (then repeat for **SILVER**), choose the earliest available "from" date and today as "to" date (the site may limit range; download in yearly chunks if needed), and export/download (CSV/Excel).
3. If spot history is not available far back, download **Bhavcopy** files for the same period (they contain near-month futures settlement prices) — tell the agent which one you used.
4. Name files `MCX_<GOLD|SILVER>_<spot|bhav>_<from>_<to>.<ext>` and place them in `data/manual_drop/in_spot/`.

**Option A2: IBJA**

1. Go to https://www.ibjarates.com and find the historical rates section (gold 999/995 per 10 g and silver 999 per kg; AM and PM rates).
2. Export or copy the history for the longest range available. If the site shows a table without export, save the page as "Webpage, HTML only" per year.
3. Name files `IBJA_<GOLD|SILVER>_<AM|PM>_<from>_<to>.<ext>` in `data/manual_drop/in_spot/`.

Tell the agent which option(s) you used and the earliest date you could get.

## Part B — NSE bhavcopy (only if the agent asks)

1. The agent gives you a list of missing dates.
2. Go to https://www.nseindia.com/all-reports (current) or the archives page linked from it (historical), select **Equities** → **Bhavcopy** for each listed date, and download the file.
3. Do not unzip or rename; place the files in `data/manual_drop/in_bhav/`.

## How to check it worked (you)

- The spot files show daily prices in rupees going back as far as the site allows; gold per 10 g, silver per kg (note the units on the page and tell the agent).

## What the agent does next

1. Runs `esw ingest in-spot --manual` (and `in-bhav --manual` if Part B), logs files with checksums.
2. Checks units, purity and time of day; reports coverage per metal and series in `coverage_in.md`.
3. Marks MI-05 VERIFIED, or lists missing ranges.

## If something goes wrong

| Problem | What to do |
|---|---|
| Registration required | Register only if you are comfortable; otherwise try IBJA; otherwise tell the agent (Layer 1 will be limited and that is documented) |
| Range limits | Download year by year; keep each file's own date range in its name |

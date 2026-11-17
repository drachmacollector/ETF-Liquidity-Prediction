# MI-04 — Manual Downloads of US ETF NAV and Shares-Outstanding History

| Field | Value |
|---|---|
| Needed by phase | P04 (identified in P01) |
| Required or optional | **Conditional**: only for sources the P01 probe marks `MANUAL_ONLY` or `BLOCKED`. The agent will give you an exact list (ticker, website, file to download) when it requests this MI |
| Estimated user time | 2–5 minutes per file; typically 15–60 minutes in total |
| What you will need | A normal web browser |

## Why this needs you

Some fund websites serve their historical-data files only to a browser (cookies, JavaScript, bot protection). The agent first tries to automate these downloads with a browser-like client (D-010); this guide is used only for the files that automation still cannot reach.

## General procedure (applies to every file)

1. Open the fund page URL the agent gives you.
2. Find the historical-data download (names vary: "Historical Archive", "Data Download", "NAV History", "Historical NAV", "Premium/Discount history"). Choose the **longest date range** offered ("since inception" or the earliest start date allowed).
3. Save the file **without opening and re-saving it in Excel** (re-saving can change dates and numbers).
4. Rename it to `<TICKER>_<what>_<YYYYMMDD of download>.<original extension>`, e.g., `SLV_navhistory_20261120.xls`.
5. Move it to `data/manual_drop/<source_id>/` where `<source_id>` is given in the agent's list (e.g., `us_iss_ishares`).
6. Tick the file off in the list the agent wrote in `records/MANUAL_ACTIONS.md`.

## Issuer-specific hints (layouts change; follow what you see)

| Issuer | Where to look |
|---|---|
| SPDR Gold (GLD) | https://www.spdrgoldshares.com/usa/gld/ → section **Historical Data** → **Historical Archive (XLSX)** |
| iShares (SLV, IAU, LQD, HYG, EWJ, ERUS, …) | Fund page on ishares.com → look for **Data Download** or a download icon near "Holdings"/"Performance"; the file may include a "Historical" sheet with NAV and shares outstanding. If only the last year is offered, download that and tell the agent |
| SSGA (SPY, JNK) | ssga.com fund page → **Performance** or **Documents** → NAV history download |
| USCF (USO, UNG, BNO, UGA, USL, UNL, CPER, USCI) | uscfinvestments.com → fund → **Historical Data** / **Download** |
| Invesco (DBC, DBA, BKLN, QQQ) | invesco.com/us fund page → **Prices & Performance** → historical NAV/price download |
| VanEck (EGPT, RSX) | vaneck.com fund page → **Prices** / **Premium/Discount** history. For liquidated funds (RSX), see "Wayback" below |
| Global X (GREK), Xtrackers (ASHR), abrdn (SIVR, PPLT, PALL), Teucrium (CORN, WEAT), Vanguard (BND, VOO) | Fund page → historical prices/NAV download |

**Wayback Machine (for delisted funds):** go to https://web.archive.org, paste the fund's old historical-data URL (the agent supplies it), pick a capture from shortly before liquidation, and download the file if the capture contains it. Save it as `<TICKER>_wayback_<capturedate>.<ext>` in `data/manual_drop/us_wayback/`.

## How to check it worked (you)

- Each file opens (you may open a *copy* to look) and has a date column going back to about the fund's launch and a NAV column.
- Files are in the right folder with the right names.

## What the agent does next

1. Runs `esw ingest us-nav --manual` which parses every file in `data/manual_drop/us_*`, logs each with `status = manual` and a checksum.
2. Checks date range, NAV column and (if present) shares outstanding against the probe expectations; reports any file that does not parse.
3. Marks each item VERIFIED in `records/MANUAL_ACTIONS.md`; re-requests only the files that failed.

## If something goes wrong

| Problem | What to do |
|---|---|
| The site only offers recent history | Download what is offered; tell the agent; it will look for alternatives (Wayback, CRSP via MI-06) |
| The download is a web page, not a file | Save it as "Webpage, HTML only" with the same naming; the agent can parse tables from HTML |
| The site asks you to confirm you are a US investor / accept terms | Accept only if true and acceptable to you; otherwise skip the file and tell the agent |

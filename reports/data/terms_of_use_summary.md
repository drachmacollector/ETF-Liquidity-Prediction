# P01 — Terms-of-use summary (for MI-07)

**User decision already recorded:** D-004 (17 Nov 2026), blanket acceptance for non-commercial research use. Raw vendor data are never committed or redistributed. Sources whose terms prohibit automated access are used only through manual downloads. SEC EDGAR is accessed with a generic project identifier.

This table records, per source, how the project uses it and the relevant restriction. It is a summary for the record, not legal advice.

| Source | Terms URL | How the project uses it | Key restrictions / notes | Access mode |
|---|---|---|---|---|
| Tiingo (US prices) | https://www.tiingo.com/about/terms | Daily EOD API with the user's key | Personal/non-commercial use on the free tier; rate limits; no redistribution of raw data | Scripted (API key, MI-02) |
| yfinance / Yahoo Finance | https://legal.yahoo.com/us/en/yahoo/terms/otos/index.html | Fallback prices (India before 2016), futures contracts, FX, India VIX | Unofficial interface; personal use; may change without notice | Scripted (library), fallback only |
| Stooq | https://stooq.com | Not used | Serves a JavaScript browser check to scripts; not bypassed | Dropped |
| SPDR Gold Shares (GLD, GLDM) | https://www.spdrgoldshares.com/usa/terms-of-use/ | Historical archive XLSX | Website content; research use; attribution | Scripted |
| iShares / BlackRock | https://www.ishares.com/us/terms-of-use | Fund "Data Download" files (NAV, shares outstanding) | Downloaded content is for internal use | Scripted |
| SSGA (SPY, DIA, JNK) | https://www.ssga.com/us/en/intermediary/terms-of-use | NAV history XLSX | Website content; research use | Scripted |
| USCF (USO, UNG, …) | https://www.uscfinvestments.com/terms-of-use | NAV history CSV from the fund page button | API behind the button needs a page-issued token: not scripted | Manual (MI-04) |
| Invesco, VanEck, Global X, Xtrackers, abrdn, Teucrium, Vanguard | Issuer sites | NAV history if offered | Pages rendered by JavaScript, moved, or rate-limited | Manual (MI-04) where needed |
| Wayback Machine | https://archive.org/about/terms.php | Search for archived NAV files of delisted funds | Research use of archived copies | Scripted (CDX search) |
| SEC EDGAR | https://www.sec.gov/os/accessing-edgar-data | Filing index and filings (capacity, operational events) | Fair access ≤ 10 requests/second; declare a user agent | Scripted |
| NSE archives | https://www.nseindia.com/terms-of-use | Daily CM bhavcopy files, 2016 onwards | Exchange data; no redistribution; files before 2016 return 403; the newer host and nseindia.com APIs do not answer scripts (not bypassed) | Scripted (archives host) + manual for gaps (MI-05) |
| BSE | https://www.bseindia.com/static/about/termsofuse.aspx | Not used (403 to scripts) | — | Dropped (manual if ever needed) |
| AMFI | https://www.amfiindia.com/disclaimer | NAVAll.txt and NAV-history API | Public NAV data; research use | Scripted |
| mfapi.in | https://www.mfapi.in/ | Full NAV history per scheme (mirror of AMFI) | Free, unofficial; cross-checked against AMFI | Scripted |
| MCX | https://www.mcxindia.com/terms-of-use | Domestic polled spot / bhavcopy | 403 to scripts | Manual (MI-05) |
| IBJA | https://www.ibjarates.com/ | Domestic gold/silver rates | History only as 30-day PDFs; paid API exists | Manual (MI-05) |
| FRED | https://fred.stlouisfed.org/legal/ | Macro, volatility, credit, FX series | Public; some series licensed (ICE BofA truncated) | Scripted |
| EIA | https://www.eia.gov/about/copyrights_reuse.php | NYMEX futures curve to Apr 2024 | US government public domain | Scripted |
| exchange_calendars (library) | Apache-2.0 licence | Trading calendars | — | Library |

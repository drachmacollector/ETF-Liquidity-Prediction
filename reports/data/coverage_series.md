# Series coverage (P06)

Staged under `data/staged/series/`. Lag (business days) and time zone come from `reference/series_catalogue.csv` and drive `known_at` in P07.

| series_id         | first      | last       |   obs |   gaps_gt5bd | unit      | source_id   |   roll_flags |   lag | tz                  |
|:------------------|:-----------|:-----------|------:|-------------:|:----------|:------------|-------------:|------:|:--------------------|
| aaa10y            | 1983-01-03 | 2026-11-16 | 10965 |            0 | percent   | mkt_fred    |          nan |     1 | America/New_York    |
| baa10y            | 1986-01-02 | 2026-11-16 | 10218 |            0 | percent   | mkt_fred    |          nan |     1 | America/New_York    |
| brent_fut         | 2007-07-30 | 2026-11-17 |  4806 |            1 | USD/bbl   | mkt_yf      |           14 |     0 | America/New_York    |
| copper_usd_fut    | 2000-08-30 | 2026-11-17 |  6584 |            0 | USD/lb    | mkt_yf      |            9 |     0 | America/New_York    |
| eurusd            | 1999-01-04 | 2026-11-13 |  6988 |            0 | USD/EUR   | mkt_fred    |          nan |     1 | America/New_York    |
| gold_usd_fut      | 2000-08-30 | 2026-11-17 |  6580 |            0 | USD/oz    | mkt_yf      |           14 |     0 | America/New_York    |
| gold_usd_navimpl  | 2004-11-18 | 2026-11-16 |  5532 |            0 | USD/oz    | derived     |          nan |     0 | Europe/London       |
| gvz               | 2008-06-03 | 2026-11-16 |  4646 |            0 | index     | mkt_fred    |          nan |     0 | America/New_York    |
| hh_c1             | 1994-01-13 | 2024-04-05 |  7496 |            0 | USD/MMBtu | mkt_eia     |          nan |     1 | America/New_York    |
| hh_c2             | 1994-01-12 | 2024-04-05 |  7500 |            0 | USD/MMBtu | mkt_eia     |          nan |     1 | America/New_York    |
| hh_c3             | 1994-01-19 | 2024-04-05 |  7452 |            0 | USD/MMBtu | mkt_eia     |          nan |     1 | America/New_York    |
| hh_c4             | 1993-12-20 | 2024-04-05 |  7453 |            0 | USD/MMBtu | mkt_eia     |          nan |     1 | America/New_York    |
| hh_fut            | 2000-08-30 | 2026-11-17 |  6585 |            0 | USD/MMBtu | mkt_yf      |           13 |     0 | America/New_York    |
| idx_athex         | 1997-07-01 | 2026-11-16 |  7289 |            1 | index     | mkt_yf      |          nan |     0 | Europe/Athens       |
| idx_bvsp          | 1993-04-27 | 2026-11-17 |  8313 |            0 | index     | mkt_yf      |          nan |     0 | America/Sao_Paulo   |
| idx_hsi           | 1986-12-31 | 2026-11-16 |  9841 |            0 | index     | mkt_yf      |          nan |     0 | Asia/Hong_Kong      |
| idx_mxx           | 1991-11-08 | 2026-11-17 |  8771 |            0 | index     | mkt_yf      |          nan |     0 | America/Mexico_City |
| idx_n225          | 1965-01-05 | 2026-11-16 | 15207 |            1 | index     | mkt_yf      |          nan |     0 | Asia/Tokyo          |
| idx_ndx           | 1985-10-01 | 2026-11-17 | 10363 |            0 | index     | mkt_yf      |          nan |     0 | America/New_York    |
| idx_nifty50       | 2007-09-17 | 2026-11-16 |  4701 |            0 | index     | mkt_yf      |          nan |     0 | Asia/Kolkata        |
| idx_nyfang        | 2014-09-22 | 2026-11-17 |  3058 |            0 | index     | mkt_yf      |          nan |     0 | America/New_York    |
| idx_spx           | 1927-12-30 | 2026-11-17 | 24838 |            1 | index     | mkt_yf      |          nan |     0 | America/New_York    |
| idx_xu100         | 1997-07-01 | 2026-11-16 |  7337 |            3 | index     | mkt_yf      |          nan |     0 | Europe/Istanbul     |
| ovx               | 2007-05-10 | 2026-11-16 |  4914 |            0 | index     | mkt_fred    |          nan |     0 | America/New_York    |
| palladium_usd_fut | 1998-09-28 | 2026-11-17 |  6618 |           18 | USD/oz    | mkt_yf      |           23 |     0 | America/New_York    |
| platinum_usd_fut  | 1997-10-29 | 2026-11-17 |  6607 |           22 | USD/oz    | mkt_yf      |           19 |     0 | America/New_York    |
| rbob_fut          | 2000-11-01 | 2026-11-17 |  6543 |            0 | USD/gal   | mkt_yf      |           25 |     0 | America/New_York    |
| silver_usd_fut    | 2000-08-30 | 2026-11-17 |  6581 |            0 | USD/oz    | mkt_yf      |           22 |     0 | America/New_York    |
| tedrate           | 1986-01-02 | 2022-01-21 |  8853 |            0 | percent   | mkt_fred    |          nan |     1 | America/New_York    |
| usd_broad         | 2006-01-02 | 2026-11-13 |  5231 |            0 | index     | mkt_fred    |          nan |     1 | America/New_York    |
| usd_major_old     | 1973-01-02 | 2019-12-31 | 11834 |            0 | index     | mkt_fred    |          nan |     1 | America/New_York    |
| usdbrl            | 1995-01-02 | 2026-11-13 |  7992 |            0 | BRL/USD   | mkt_fred    |          nan |     1 | America/New_York    |
| usdcny            | 1981-01-02 | 2026-11-13 | 11449 |            0 | CNY/USD   | mkt_fred    |          nan |     1 | America/New_York    |
| usdegp            | 2001-06-01 | 2026-11-17 |  6385 |            2 | EGP/USD   | mkt_yf      |          nan |     0 | Europe/London       |
| usdhkd            | 1981-01-02 | 2026-11-13 | 11509 |            0 | HKD/USD   | mkt_fred    |          nan |     1 | America/New_York    |
| usdinr            | 1973-01-02 | 2026-11-13 | 13501 |            0 | INR/USD   | mkt_fred    |          nan |     1 | America/New_York    |
| usdinr_yf         | 2003-12-01 | 2026-11-17 |  5955 |            1 | INR/USD   | mkt_yf      |          nan |     0 | Europe/London       |
| usdjpy            | 1971-01-04 | 2026-11-13 | 14003 |            1 | JPY/USD   | mkt_fred    |          nan |     1 | America/New_York    |
| usdmxn            | 1993-11-08 | 2026-11-13 |  8277 |            0 | MXN/USD   | mkt_fred    |          nan |     1 | America/New_York    |
| usdrub            | 2003-12-01 | 2026-11-17 |  5849 |            2 | RUB/USD   | mkt_yf      |          nan |     0 | Europe/London       |
| usdtry            | 2005-01-03 | 2026-11-17 |  5687 |            0 | TRY/USD   | mkt_yf      |          nan |     0 | Europe/London       |
| ust10y            | 1962-01-02 | 2026-11-16 | 16203 |            0 | percent   | mkt_fred    |          nan |     1 | America/New_York    |
| ust2y             | 1976-06-01 | 2026-11-16 | 12611 |            0 | percent   | mkt_fred    |          nan |     1 | America/New_York    |
| vix               | 1990-01-02 | 2026-11-16 |  9318 |            0 | index     | mkt_fred    |          nan |     0 | America/New_York    |
| wti_c1            | 1983-04-04 | 2024-04-05 | 10183 |            0 | USD/bbl   | mkt_eia     |          nan |     1 | America/New_York    |
| wti_c2            | 1985-01-02 | 2024-04-05 |  9594 |            0 | USD/bbl   | mkt_eia     |          nan |     1 | America/New_York    |
| wti_c3            | 1983-03-30 | 2024-04-05 | 10219 |            0 | USD/bbl   | mkt_eia     |          nan |     1 | America/New_York    |
| wti_c4            | 1985-01-02 | 2024-04-05 |  9551 |            0 | USD/bbl   | mkt_eia     |          nan |     1 | America/New_York    |
| wti_fut           | 2000-08-23 | 2026-11-17 |  6588 |            0 | USD/bbl   | mkt_yf      |           17 |     0 | America/New_York    |

## Unavailable series and affected features

| series | reason | features affected |
|---|---|---|
| silver_usd_navimpl | iShares SLV download has no ounces/share | silver NAV-implied benchmark → use silver_usd_fut |
| usdinr_rbi | FBIL/RBI reference-rate archive not scriptable in P06 | Layer-1 parity uses FRED DEXINUS (noon NY) / yfinance INR=X |
| wti/hh curve after 2024-04-05 | EIA discontinued; yfinance drops expired contracts (D-017) | roll yield / contango features missing after 2024-04-05 |
| idx_csi300, idx_hstech, idx_egx30, idx_moex | yfinance has no usable history | closure diagnostics for those markets (ASHR, EGPT, RSX, ERUS are excluded anyway); MAHKTECH uses idx_hsi |

## Roll handling

Continuous futures (`*_fut`) carry `roll_flag` and `ret`: a day whose log return is more than 6 robust SDs from the trailing 60-day median (using data to the previous day only) is flagged and its return set to null. Features use `ret`, never level differences.

## FX for home markets of included international ETFs

EWJ→usdjpy, EWH/FXI→usdhkd (usdcny), EWZ→usdbrl, EWW→usdmxn, INDA→usdinr, TUR→usdtry, GREK→eurusd, EEM→usd_broad; Indian international ETFs→usdinr (+usdhkd for Hong Kong).

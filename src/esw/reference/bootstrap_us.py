"""One-off builder for `reference/instruments_us.csv` and the US part of `symbol_history.csv` (P02 T02.1).

The CSVs in `reference/` are the source of truth once written and reviewed; this module records how
they were first assembled, from:

* identifiers: iShares product screener (CUSIP/ISIN/inception, P01 raw), SEC "Official List of
  Section 13(f) Securities" (CUSIP; 2026Q3, and 2021Q4/2023Q4 for delisted funds), SEC
  `company_tickers_exchange.json` / `company_tickers_mf.json` (CIK, series ID);
* listing/delisting dates: Tiingo metadata (`startDate`/`endDate`), cross-checked with issuer
  inception dates and the P01 probe history;
* legal form: prospectus/registration type (P01 primary-text notes: Rule 6c-11 covers only
  registered open-end funds) and the SEC listing (exchange-listed trust/pool vs fund series);
* data sources and feasibility: `reports/data/universe_feasibility_us.csv` (P01) plus the MI-04
  files received on 2026-11-17.
"""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from esw.config import Settings, get_settings
from esw.ingest.candidates import US_CANDIDATES

VERIFIED_ON = "2026-11-17"
SEC_13F = "https://www.sec.gov/files/investment/13flist2026q3.txt"
SEC_13F_2021 = "https://www.sec.gov/files/investment/13flist2021q4.txt"
SEC_13F_2023 = "https://www.sec.gov/files/investment/13flist2023q4.txt"

# ticker -> (name, issuer, subgroup, underlying, legal_form, rule_6c11, cusip, cusip_source, source_url, notes)
US_FACTS: dict[str, tuple[str, str, str, str, str, str, str, str, str, str]] = {
    "GLD": (
        "SPDR Gold Shares",
        "World Gold Trust Services (SPDR)",
        "gold",
        "Physical gold (LBMA Gold Price PM)",
        "grantor_trust",
        "n",
        "78463V107",
        SEC_13F,
        "https://www.spdrgoldshares.com/usa/gld/",
        "",
    ),
    "GLDM": (
        "SPDR Gold MiniShares Trust",
        "World Gold Trust Services (SPDR)",
        "gold",
        "Physical gold (LBMA Gold Price PM)",
        "grantor_trust",
        "n",
        "98149E303",
        SEC_13F,
        "https://www.spdrgoldshares.com/usa/gldm/",
        "Series of World Gold Trust",
    ),
    "IAU": (
        "iShares Gold Trust",
        "iShares (BlackRock)",
        "gold",
        "Physical gold (LBMA Gold Price PM)",
        "grantor_trust",
        "n",
        "",
        "",
        "https://www.ishares.com/us/products/239561/ishares-gold-trust",
        "",
    ),
    "SLV": (
        "iShares Silver Trust",
        "iShares (BlackRock)",
        "silver",
        "Physical silver (LBMA Silver Price)",
        "grantor_trust",
        "n",
        "",
        "",
        "https://www.ishares.com/us/products/239855/ishares-silver-trust",
        "",
    ),
    "SIVR": (
        "abrdn Physical Silver Shares ETF",
        "abrdn",
        "silver",
        "Physical silver (LBMA Silver Price)",
        "grantor_trust",
        "n",
        "003264108",
        SEC_13F,
        "https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK=1450922",
        "Formerly ETFS/Aberdeen Standard Silver Trust",
    ),
    "PPLT": (
        "abrdn Physical Platinum Shares ETF",
        "abrdn",
        "pgm",
        "Physical platinum (LBMA Platinum Price PM)",
        "grantor_trust",
        "n",
        "003260106",
        SEC_13F,
        "https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK=1460235",
        "Formerly ETFS Platinum Trust",
    ),
    "PALL": (
        "abrdn Physical Palladium Shares ETF",
        "abrdn",
        "pgm",
        "Physical palladium (LBMA Palladium Price PM)",
        "grantor_trust",
        "n",
        "003262102",
        SEC_13F,
        "https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK=1459862",
        "Formerly ETFS Palladium Trust",
    ),
    "USO": (
        "United States Oil Fund, LP",
        "USCF",
        "crude",
        "NYMEX WTI crude oil futures (front month, roll schedule per prospectus)",
        "commodity_pool",
        "n",
        "91232N207",
        SEC_13F,
        "https://www.uscfinvestments.com/uso",
        "CUSIP changed with the 2020 reverse split",
    ),
    "UNG": (
        "United States Natural Gas Fund, LP",
        "USCF",
        "natgas",
        "NYMEX Henry Hub natural gas futures (front month)",
        "commodity_pool",
        "n",
        "912318409",
        SEC_13F,
        "https://www.uscfinvestments.com/ung",
        "CUSIP changed with the 2024 reverse split (912318300 in 2021Q4 list)",
    ),
    "BNO": (
        "United States Brent Oil Fund, LP",
        "USCF",
        "crude",
        "ICE Brent crude futures (front month)",
        "commodity_pool",
        "n",
        "91167Q100",
        SEC_13F,
        "https://www.uscfinvestments.com/bno",
        "",
    ),
    "UGA": (
        "United States Gasoline Fund, LP",
        "USCF",
        "crude",
        "NYMEX RBOB gasoline futures (front month)",
        "commodity_pool",
        "n",
        "91201T102",
        SEC_13F,
        "https://www.uscfinvestments.com/uga",
        "Refined product; grouped with crude",
    ),
    "USL": (
        "United States 12 Month Oil Fund, LP",
        "USCF",
        "crude",
        "NYMEX WTI futures, 12 consecutive months",
        "commodity_pool",
        "n",
        "91288V103",
        SEC_13F,
        "https://www.uscfinvestments.com/usl",
        "",
    ),
    "UNL": (
        "United States 12 Month Natural Gas Fund, LP",
        "USCF",
        "natgas",
        "NYMEX natural gas futures, 12 consecutive months",
        "commodity_pool",
        "n",
        "91288X109",
        SEC_13F,
        "https://www.uscfinvestments.com/unl",
        "",
    ),
    "CPER": (
        "United States Copper Index Fund",
        "USCF",
        "broad_commodity",
        "COMEX copper futures (SummerHaven Copper Index)",
        "commodity_pool",
        "n",
        "911718104",
        SEC_13F,
        "https://www.uscfinvestments.com/cper",
        "Series of United States Commodity Index Funds Trust; base metal",
    ),
    "USCI": (
        "United States Commodity Index Fund",
        "USCF",
        "broad_commodity",
        "SummerHaven Dynamic Commodity Index futures",
        "commodity_pool",
        "n",
        "911717106",
        SEC_13F,
        "https://www.uscfinvestments.com/usci",
        "Series of United States Commodity Index Funds Trust",
    ),
    "DBC": (
        "Invesco DB Commodity Index Tracking Fund",
        "Invesco",
        "broad_commodity",
        "DBIQ Optimum Yield Diversified Commodity Index futures",
        "commodity_pool",
        "n",
        "46138B103",
        SEC_13F,
        "https://www.invesco.com/us/financial-products/etfs/product-detail?audienceType=Investor&ticker=DBC",
        "",
    ),
    "DBA": (
        "Invesco DB Agriculture Fund",
        "Invesco",
        "agri",
        "DBIQ Diversified Agriculture Index futures",
        "commodity_pool",
        "n",
        "46140H106",
        SEC_13F,
        "https://www.invesco.com/us/financial-products/etfs/product-detail?audienceType=Investor&ticker=DBA",
        "Series of Invesco DB Multi-Sector Commodity Trust",
    ),
    "DBO": (
        "Invesco DB Oil Fund",
        "Invesco",
        "crude",
        "DBIQ Optimum Yield Crude Oil Index (WTI futures)",
        "commodity_pool",
        "n",
        "46140H403",
        SEC_13F,
        "https://www.invesco.com/us/financial-products/etfs/product-detail?audienceType=Investor&ticker=DBO",
        "Series of Invesco DB Multi-Sector Commodity Trust",
    ),
    "GSG": (
        "iShares S&P GSCI Commodity-Indexed Trust",
        "iShares (BlackRock)",
        "broad_commodity",
        "S&P GSCI Total Return Index (CERFs/futures)",
        "commodity_pool",
        "n",
        "",
        "",
        "https://www.ishares.com/us/products/239757/ishares-s-p-gsci-commodity-indexed-trust",
        "",
    ),
    "CORN": (
        "Teucrium Corn Fund",
        "Teucrium",
        "agri",
        "CBOT corn futures (three contracts)",
        "commodity_pool",
        "n",
        "88166A102",
        SEC_13F,
        "https://teucrium.com/funds/corn",
        "Series of Teucrium Commodity Trust",
    ),
    "WEAT": (
        "Teucrium Wheat Fund",
        "Teucrium",
        "agri",
        "CBOT wheat futures (three contracts)",
        "commodity_pool",
        "n",
        "88166A870",
        SEC_13F,
        "https://teucrium.com/funds/weat",
        "Series of Teucrium Commodity Trust",
    ),
    "SOYB": (
        "Teucrium Soybean Fund",
        "Teucrium",
        "agri",
        "CBOT soybean futures (three contracts)",
        "commodity_pool",
        "n",
        "88166A607",
        SEC_13F,
        "https://teucrium.com/funds/soyb",
        "Series of Teucrium Commodity Trust",
    ),
    "LQD": (
        "iShares iBoxx $ Investment Grade Corporate Bond ETF",
        "iShares (BlackRock)",
        "ig_corp",
        "Markit iBoxx USD Liquid Investment Grade Index",
        "open_end",
        "y",
        "",
        "",
        "https://www.ishares.com/us/products/239566/ishares-iboxx-investment-grade-corporate-bond-etf",
        "",
    ),
    "HYG": (
        "iShares iBoxx $ High Yield Corporate Bond ETF",
        "iShares (BlackRock)",
        "hy_corp",
        "Markit iBoxx USD Liquid High Yield Index",
        "open_end",
        "y",
        "",
        "",
        "https://www.ishares.com/us/products/239565/ishares-iboxx-high-yield-corporate-bond-etf",
        "",
    ),
    "MUB": (
        "iShares National Muni Bond ETF",
        "iShares (BlackRock)",
        "muni",
        "ICE AMT-Free US National Municipal Index",
        "open_end",
        "y",
        "",
        "",
        "https://www.ishares.com/us/products/239766/ishares-national-muni-bond-etf",
        "",
    ),
    "EMB": (
        "iShares J.P. Morgan USD Emerging Markets Bond ETF",
        "iShares (BlackRock)",
        "em_debt",
        "J.P. Morgan EMBI Global Core Index",
        "open_end",
        "y",
        "",
        "",
        "https://www.ishares.com/us/products/239572/ishares-j-p-morgan-usd-emerging-markets-bond-etf",
        "",
    ),
    "AGG": (
        "iShares Core U.S. Aggregate Bond ETF",
        "iShares (BlackRock)",
        "treasury",
        "Bloomberg US Aggregate Bond Index",
        "open_end",
        "y",
        "",
        "",
        "https://www.ishares.com/us/products/239458/ishares-core-u-s-aggregate-bond-etf",
        "Broad aggregate (mostly Treasury/agency MBS); subgroup treasury as nearest code",
    ),
    "TLT": (
        "iShares 20+ Year Treasury Bond ETF",
        "iShares (BlackRock)",
        "treasury",
        "ICE US Treasury 20+ Year Index",
        "open_end",
        "y",
        "",
        "",
        "https://www.ishares.com/us/products/239454/ishares-20-year-treasury-bond-etf",
        "",
    ),
    "JNK": (
        "SPDR Bloomberg High Yield Bond ETF",
        "State Street (SSGA)",
        "hy_corp",
        "Bloomberg High Yield Very Liquid Index",
        "open_end",
        "y",
        "78468R622",
        SEC_13F,
        "https://www.ssga.com/us/en/intermediary/etfs/spdr-bloomberg-high-yield-bond-etf-jnk",
        "",
    ),
    "BKLN": (
        "Invesco Senior Loan ETF",
        "Invesco",
        "loans",
        "Morningstar LSTA US Leveraged Loan 100 Index",
        "open_end",
        "y",
        "46138G508",
        SEC_13F,
        "https://www.invesco.com/us/financial-products/etfs/product-detail?audienceType=Investor&ticker=BKLN",
        "",
    ),
    "BND": (
        "Vanguard Total Bond Market ETF",
        "Vanguard",
        "treasury",
        "Bloomberg US Aggregate Float Adjusted Index",
        "open_end",
        "unknown",
        "921937835",
        SEC_13F,
        "https://investor.vanguard.com/investment-products/etfs/profile/bnd",
        "ETF share class of a mutual fund; the Rule 6c-11 adopting release left share-class ETFs on their own exemptive relief [K]",
    ),
    "EWJ": (
        "iShares MSCI Japan ETF",
        "iShares (BlackRock)",
        "single_country_dm",
        "MSCI Japan Index",
        "open_end",
        "y",
        "",
        "",
        "https://www.ishares.com/us/products/239665/ishares-msci-japan-etf",
        "",
    ),
    "EWH": (
        "iShares MSCI Hong Kong ETF",
        "iShares (BlackRock)",
        "single_country_dm",
        "MSCI Hong Kong 25/50 Index",
        "open_end",
        "y",
        "",
        "",
        "https://www.ishares.com/us/products/239657/ishares-msci-hong-kong-etf",
        "",
    ),
    "EWZ": (
        "iShares MSCI Brazil ETF",
        "iShares (BlackRock)",
        "single_country_em",
        "MSCI Brazil 25/50 Index",
        "open_end",
        "y",
        "",
        "",
        "https://www.ishares.com/us/products/239612/ishares-msci-brazil-etf",
        "",
    ),
    "EWW": (
        "iShares MSCI Mexico ETF",
        "iShares (BlackRock)",
        "single_country_em",
        "MSCI Mexico IMI 25/50 Index",
        "open_end",
        "y",
        "",
        "",
        "https://www.ishares.com/us/products/239670/ishares-msci-mexico-etf",
        "",
    ),
    "FXI": (
        "iShares China Large-Cap ETF",
        "iShares (BlackRock)",
        "single_country_em",
        "FTSE China 50 Index (Hong Kong-listed shares)",
        "open_end",
        "y",
        "",
        "",
        "https://www.ishares.com/us/products/239536/ishares-china-large-cap-etf",
        "",
    ),
    "EEM": (
        "iShares MSCI Emerging Markets ETF",
        "iShares (BlackRock)",
        "regional",
        "MSCI Emerging Markets Index",
        "open_end",
        "y",
        "",
        "",
        "https://www.ishares.com/us/products/239637/ishares-msci-emerging-markets-etf",
        "",
    ),
    "INDA": (
        "iShares MSCI India ETF",
        "iShares (BlackRock)",
        "single_country_em",
        "MSCI India Index",
        "open_end",
        "y",
        "",
        "",
        "https://www.ishares.com/us/products/239659/ishares-msci-india-etf",
        "",
    ),
    "TUR": (
        "iShares MSCI Turkey ETF",
        "iShares (BlackRock)",
        "single_country_em",
        "MSCI Turkey IMI 25/50 Index",
        "open_end",
        "y",
        "",
        "",
        "https://www.ishares.com/us/products/239689/ishares-msci-turkey-etf",
        "",
    ),
    "ERUS": (
        "iShares MSCI Russia ETF",
        "iShares (BlackRock)",
        "single_country_em",
        "MSCI Russia 25/50 Index",
        "open_end",
        "y",
        "46434G798",
        SEC_13F_2021,
        "https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK=930667",
        "Halted March 2022 and liquidated",
    ),
    "EGPT": (
        "VanEck Egypt Index ETF",
        "VanEck",
        "single_country_em",
        "MarketVector Egypt Index",
        "open_end",
        "y",
        "92189F775",
        SEC_13F_2023,
        "https://www.vaneck.com/us/en/investments/egypt-etf-egpt/",
        "Liquidated 2024",
    ),
    "RSX": (
        "VanEck Russia ETF",
        "VanEck",
        "single_country_em",
        "MarketVector Russia Index",
        "open_end",
        "y",
        "92189F403",
        SEC_13F_2021,
        "https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK=1137360",
        "Halted 4 Mar 2022; delisted; in liquidation",
    ),
    "GREK": (
        "Global X MSCI Greece ETF",
        "Global X",
        "single_country_dm",
        "MSCI All Greece Select 25/50 Index",
        "open_end",
        "y",
        "37954Y319",
        SEC_13F,
        "https://www.globalxetfs.com/funds/grek/",
        "",
    ),
    "ASHR": (
        "Xtrackers Harvest CSI 300 China A-Shares ETF",
        "Xtrackers (DWS)",
        "single_country_em",
        "CSI 300 Index (China A-shares)",
        "open_end",
        "y",
        "233051879",
        SEC_13F,
        "https://etf.dws.com/en-us/ASHR-harvest-csi-300-china-a-shares-etf/",
        "",
    ),
    "SPY": (
        "SPDR S&P 500 ETF Trust",
        "State Street (SSGA)",
        "large_cap_us",
        "S&P 500 Index",
        "uit",
        "n",
        "78462F103",
        SEC_13F,
        "https://www.ssga.com/us/en/intermediary/etfs/spdr-sp-500-etf-trust-spy",
        "",
    ),
    "DIA": (
        "SPDR Dow Jones Industrial Average ETF Trust",
        "State Street (SSGA)",
        "large_cap_us",
        "Dow Jones Industrial Average",
        "uit",
        "n",
        "78467X109",
        SEC_13F,
        "https://www.ssga.com/us/en/intermediary/etfs/spdr-dow-jones-industrial-average-etf-trust-dia",
        "",
    ),
    "IVV": (
        "iShares Core S&P 500 ETF",
        "iShares (BlackRock)",
        "large_cap_us",
        "S&P 500 Index",
        "open_end",
        "y",
        "",
        "",
        "https://www.ishares.com/us/products/239726/ishares-core-s-p-500-etf",
        "",
    ),
    "IWM": (
        "iShares Russell 2000 ETF",
        "iShares (BlackRock)",
        "large_cap_us",
        "Russell 2000 Index",
        "open_end",
        "y",
        "",
        "",
        "https://www.ishares.com/us/products/239710/ishares-russell-2000-etf",
        "Small-cap; subgroup large_cap_us used for the control group",
    ),
    "QQQ": (
        "Invesco QQQ Trust / Invesco QQQ ETF",
        "Invesco",
        "large_cap_us",
        "Nasdaq-100 Index",
        "uit",
        "unknown",
        "46090E103",
        SEC_13F,
        "https://www.invesco.com/us/financial-products/etfs/product-detail?audienceType=Investor&ticker=QQQ",
        "Historically a UIT (Invesco QQQ Trust, Series 1). SEC now lists QQQ as a fund series (S000101292), consistent with a conversion to an open-end fund; conversion date not verified (OQ-25)",
    ),
    "VOO": (
        "Vanguard S&P 500 ETF",
        "Vanguard",
        "large_cap_us",
        "S&P 500 Index",
        "open_end",
        "unknown",
        "922908363",
        SEC_13F,
        "https://investor.vanguard.com/investment-products/etfs/profile/voo",
        "ETF share class of a mutual fund; see BND note",
    ),
}

# Tiingo `exchangeCode` -> exchange code used in `symbol_history`. Tiingo reports the NYSE group as
# "NYSE"; exchange-traded products of that group list on NYSE Arca.
TIINGO_EXCHANGE = {"NYSE ARCA": "NYSEARCA", "NYSE": "NYSEARCA", "NASDAQ": "NASDAQ", "BATS": "CBOE"}

# MI-04 files received 2026-11-17 (in data/manual_drop/), with what they contain.
MANUAL_RECEIVED = {
    "USO": "USCF NAV CSV 2009-01-02..2026-11-16 (NAV only; not split-adjusted)",
    "UNG": "USCF NAV CSV 2009-01-02..2026-11-16 (NAV only; not split-adjusted)",
    "BNO": "USCF NAV CSV 2010-06-02..2026-11-16 (NAV only; not split-adjusted)",
    "CPER": "USCF NAV CSV 2011-11-15..2026-11-16 (NAV only)",
    "GREK": "Global X premium/discount CSV 2015-04-13..2026-11-16; NAV = close - premium (no shares outstanding)",
}


def isin_from_cusip(cusip: str, country: str = "US") -> str:
    """ISIN = country + CUSIP + Luhn check digit (letters A=10..Z=35)."""
    if not cusip:
        return ""
    digits = "".join(str(int(c, 36)) for c in country + cusip)
    total = 0
    for i, ch in enumerate(reversed(digits)):
        n = int(ch)
        if i % 2 == 0:
            n *= 2
            n = n - 9 if n > 9 else n
        total += n
    return f"{country}{cusip}{(10 - total % 10) % 10}"


def _ishares_ids(raw: Path) -> dict[str, dict]:
    d = json.loads((raw / "_probes" / "us_iss_ishares" / "product_screener.json").read_text(encoding="utf-8"))
    out = {}
    for v in d.values():
        t = v.get("localExchangeTicker")
        if t in US_CANDIDATES:
            out[t] = {"cusip": v["cusip"], "isin": v["isin"], "inception": str(v["inceptionDate"]["r"])}
    return out


def _sec_ciks(raw: Path) -> dict[str, str]:
    out: dict[str, str] = {}
    for name, sym in (("company_tickers_exchange.json", "ticker"), ("company_tickers_mf.json", "symbol")):
        p = raw / "sec_edgar" / name
        if p.exists():
            d = json.loads(p.read_text(encoding="utf-8"))
            i_cik, i_sym = d["fields"].index("cik"), d["fields"].index(sym)
            for row in d["data"]:
                out.setdefault(str(row[i_sym]), str(row[i_cik]))
    return out


# Delisted funds are no longer in the SEC ticker files: CIK of the registrant (trust) from EDGAR.
CIK_DELISTED = {"EGPT": "1137360"}


def _tiingo_meta(raw: Path, ticker: str) -> dict:
    for p in (
        raw / "_probes" / "us_px_tiingo" / f"{ticker}_meta.json",
        raw / "us_px_tiingo" / "meta" / f"{ticker}_meta.json",
    ):
        if p.exists():
            return json.loads(p.read_text(encoding="utf-8"))
    return {}


def build_instruments_us(settings: Settings | None = None) -> pd.DataFrame:
    settings = settings or get_settings()
    raw = settings.path("raw")
    feas = pd.read_csv(settings.path("reports") / "data" / "universe_feasibility_us.csv", dtype=str).fillna(
        ""
    )
    feas = feas.set_index("ticker")
    ish = _ishares_ids(raw)
    ciks = {**_sec_ciks(raw), **CIK_DELISTED}
    rows = []
    for t, (group, nav_src) in US_CANDIDATES.items():
        name, issuer, sub, und, form, r6, cusip, cusip_src, url, notes = US_FACTS[t]
        f = feas.loc[t]
        meta = _tiingo_meta(raw, t)
        note_parts = [notes] if notes else []
        isin = ""
        if t in ish:
            cusip, isin = ish[t]["cusip"], ish[t]["isin"]
            note_parts.append(
                f"iShares inception {ish[t]['inception'][:4]}-{ish[t]['inception'][4:6]}-{ish[t]['inception'][6:]}"
            )
            cusip_src = "iShares product screener (P01)"
        elif cusip:
            isin = isin_from_cusip(cusip)
        listing = meta.get("startDate", "") or f.get("price_start", "")
        end = meta.get("endDate", "")
        delisting = end if t in {"RSX", "EGPT", "ERUS"} else ""
        status = f["status"]
        include = status in {"FEASIBLE", "FEASIBLE_MANUAL"}
        exclude_reason = "" if include else "nav_unavailable (I-005)"
        if t in MANUAL_RECEIVED:
            note_parts.append(f"MI-04 received: {MANUAL_RECEIVED[t]}")
        elif status == "FEASIBLE_MANUAL":
            note_parts.append("NAV pending: P04 automated download (D-010), else MI-04")
        if cusip_src:
            note_parts.append(f"CUSIP source: {cusip_src}")
        shares_src = nav_src if f["shares_out"] == "y" else ""
        exch = TIINGO_EXCHANGE.get(meta.get("exchangeCode", ""), meta.get("exchangeCode", ""))
        rows.append(
            {
                "instrument_id": f"US:{t}",
                "market": "US",
                "ticker": t,
                "isin": isin,
                "cusip": cusip,
                "cik": ciks.get(t, ""),
                "name": name,
                "issuer": issuer,
                "group": group,
                "subgroup": sub,
                "underlying": und,
                "legal_form": form,
                "rule_6c11": r6,
                "listing_date": listing,
                "delisting_date": delisting,
                "currency": "USD",
                "nav_source_id": nav_src,
                "px_source_id": "us_px_tiingo",
                "shares_source_id": shares_src,
                "include": "true" if include else "false",
                "exclude_reason": exclude_reason,
                "notes": "; ".join(note_parts),
                "source_url": url,
                "verified_by": "agent (P02)",
                "verified_on": VERIFIED_ON,
                "_exchange": exch,
            }
        )
    return pd.DataFrame(rows)

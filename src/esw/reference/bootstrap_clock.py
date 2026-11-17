"""One-off builders for `nav_clock.csv` and `corporate_actions_manual.csv` (P02 T02.4, T02.6)."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

SEBI_2026 = "https://www.sebi.gov.in/sebi_data/attachdocs/feb-2026/1772102397057.pdf"
MIRAE_SILVER_SID = "https://www.miraeassetmf.co.in/docs/default-source/sid/sid_mirae-asset-silver-etf.pdf"
CME_SETTLE = "https://www.cmegroup.com/market-data/settlements.html"

# US: ticker -> list of (effective_from or None=listing, nav_basis, time, tz, source_url, notes)
_FUT = "futures_settle"
US_CLOCK: dict[str, list[tuple]] = {
    "GLD": [
        (
            None,
            "lbma_pm",
            "15:00",
            "Europe/London",
            "https://www.spdrgoldshares.com/usa/gld/",
            "LBMA Gold Price PM (London PM fix before 20 Mar 2015); issuer archive labels NAV at 10:30am New York and also gives a 4:15pm indicative value (P01 notes §5)",
        )
    ],
    "GLDM": [
        (
            None,
            "lbma_pm",
            "15:00",
            "Europe/London",
            "https://www.spdrgoldshares.com/usa/gldm/",
            "LBMA Gold Price PM; NAV labelled 10:30am New York",
        )
    ],
    "IAU": [
        (
            None,
            "lbma_pm",
            "15:00",
            "Europe/London",
            "https://www.ishares.com/us/products/239561/ishares-gold-trust",
            "LBMA Gold Price PM per prospectus [K]; exact wording to confirm in P08 (OQ-06)",
        )
    ],
    "SLV": [
        (
            None,
            "lbma_silver_noon",
            "12:00",
            "Europe/London",
            "https://www.ishares.com/us/products/239855/ishares-silver-trust",
            "LBMA Silver Price (London Silver Fix before Aug 2014) per iShares page note (P01 notes §5)",
        )
    ],
    "SIVR": [
        (
            None,
            "lbma_silver_noon",
            "12:00",
            "Europe/London",
            "https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK=1450922",
            "LBMA Silver Price [K]",
        )
    ],
    "PPLT": [
        (
            None,
            "lbma_pm",
            "14:00",
            "Europe/London",
            "https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK=1460235",
            "LBMA Platinum Price PM (LPPM PM fix before Dec 2014) [K]; basis code lbma_pm used for the PM platinum price",
        )
    ],
    "PALL": [
        (
            None,
            "lbma_pm",
            "14:00",
            "Europe/London",
            "https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK=1459862",
            "LBMA Palladium Price PM [K]",
        )
    ],
    "USO": [
        (
            None,
            _FUT,
            "14:30",
            "America/New_York",
            "https://www.uscfinvestments.com/uso",
            "NYMEX WTI settlement (14:28-14:30 ET window) [K]",
        )
    ],
    "UNG": [
        (
            None,
            _FUT,
            "14:30",
            "America/New_York",
            "https://www.uscfinvestments.com/ung",
            "NYMEX Henry Hub settlement [K]",
        )
    ],
    "BNO": [
        (
            None,
            _FUT,
            "19:30",
            "Europe/London",
            "https://www.uscfinvestments.com/bno",
            "ICE Brent settlement (19:28-19:30 London) [K]",
        )
    ],
    "UGA": [
        (
            None,
            _FUT,
            "14:30",
            "America/New_York",
            "https://www.uscfinvestments.com/uga",
            "NYMEX RBOB settlement [K]",
        )
    ],
    "USL": [
        (
            None,
            _FUT,
            "14:30",
            "America/New_York",
            "https://www.uscfinvestments.com/usl",
            "NYMEX WTI settlement [K]",
        )
    ],
    "UNL": [
        (
            None,
            _FUT,
            "14:30",
            "America/New_York",
            "https://www.uscfinvestments.com/unl",
            "NYMEX natural gas settlement [K]",
        )
    ],
    "CPER": [
        (
            None,
            _FUT,
            "13:00",
            "America/New_York",
            "https://www.uscfinvestments.com/cper",
            "COMEX copper settlement [K]",
        )
    ],
    "USCI": [
        (
            None,
            _FUT,
            "14:30",
            "America/New_York",
            "https://www.uscfinvestments.com/usci",
            "Several exchanges; latest settlement about 14:30 ET [K]",
        )
    ],
    "DBC": [
        (
            None,
            _FUT,
            "14:30",
            "America/New_York",
            CME_SETTLE,
            "Several exchanges; latest settlement about 14:30 ET [K]",
        )
    ],
    "DBA": [
        (
            None,
            _FUT,
            "14:15",
            "America/New_York",
            CME_SETTLE,
            "CBOT grains 13:15 CT, ICE softs and CME livestock; latest about 14:15 ET [K]",
        )
    ],
    "DBO": [(None, _FUT, "14:30", "America/New_York", CME_SETTLE, "NYMEX WTI settlement [K]")],
    "GSG": [
        (
            None,
            _FUT,
            "14:30",
            "America/New_York",
            "https://www.ishares.com/us/products/239757/ishares-s-p-gsci-commodity-indexed-trust",
            "S&P GSCI futures (several exchanges); latest settlement about 14:30 ET [K]",
        )
    ],
    "CORN": [
        (
            None,
            _FUT,
            "13:15",
            "America/Chicago",
            "https://teucrium.com/funds/corn",
            "CBOT corn settlement [K]",
        )
    ],
    "WEAT": [
        (
            None,
            _FUT,
            "13:15",
            "America/Chicago",
            "https://teucrium.com/funds/weat",
            "CBOT wheat settlement [K]",
        )
    ],
    "SOYB": [
        (
            None,
            _FUT,
            "13:15",
            "America/Chicago",
            "https://teucrium.com/funds/soyb",
            "CBOT soybean settlement [K]",
        )
    ],
    "EWJ": [
        (
            None,
            "foreign_close",
            "15:00",
            "Asia/Tokyo",
            "https://www.ishares.com/us/products/239665/ishares-msci-japan-etf",
            "Tokyo close 15:00",
        ),
        (
            "2024-11-05",
            "foreign_close",
            "15:30",
            "Asia/Tokyo",
            "https://www.jpx.co.jp/english/equities/trading/domestic/index.html",
            "TSE extended the afternoon session to 15:30 from 5 Nov 2024 [K]",
        ),
    ],
    "EWH": [
        (
            None,
            "foreign_close",
            "16:00",
            "Asia/Hong_Kong",
            "https://www.ishares.com/us/products/239657/ishares-msci-hong-kong-etf",
            "HKEX close (closing auction to about 16:10 since 2016) [K]",
        )
    ],
    "FXI": [
        (
            None,
            "foreign_close",
            "16:00",
            "Asia/Hong_Kong",
            "https://www.ishares.com/us/products/239536/ishares-china-large-cap-etf",
            "HKEX close [K]",
        )
    ],
    "EWZ": [
        (
            None,
            "foreign_close",
            "17:00",
            "America/Sao_Paulo",
            "https://www.ishares.com/us/products/239612/ishares-msci-brazil-etf",
            "B3 close varies 17:00-18:00 local with US daylight saving [K]",
        )
    ],
    "EWW": [
        (
            None,
            "foreign_close",
            "15:00",
            "America/Mexico_City",
            "https://www.ishares.com/us/products/239670/ishares-msci-mexico-etf",
            "BMV close [K]",
        )
    ],
    "EEM": [
        (
            None,
            "foreign_close",
            None,
            None,
            "https://www.ishares.com/us/products/239637/ishares-msci-emerging-markets-etf",
            "Many home markets; no single valuation time",
        )
    ],
    "INDA": [
        (
            None,
            "foreign_close",
            "15:30",
            "Asia/Kolkata",
            "https://www.ishares.com/us/products/239659/ishares-msci-india-etf",
            "NSE/BSE close",
        )
    ],
    "TUR": [
        (
            None,
            "foreign_close",
            "18:00",
            "Europe/Istanbul",
            "https://www.ishares.com/us/products/239689/ishares-msci-turkey-etf",
            "Borsa Istanbul close (17:30 before 2016 per reports) [K]",
        )
    ],
    "ERUS": [
        (
            None,
            "foreign_close",
            "18:45",
            "Europe/Moscow",
            "https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK=930667",
            "MOEX main session close [K]",
        )
    ],
    "RSX": [
        (
            None,
            "foreign_close",
            "18:45",
            "Europe/Moscow",
            "https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK=1137360",
            "MOEX main session close [K]",
        )
    ],
    "EGPT": [
        (
            None,
            "foreign_close",
            "14:30",
            "Africa/Cairo",
            "https://www.vaneck.com/us/en/investments/egypt-etf-egpt/",
            "EGX close [K]",
        )
    ],
    "GREK": [
        (
            None,
            "foreign_close",
            "17:20",
            "Europe/Athens",
            "https://www.globalxetfs.com/funds/grek/",
            "ATHEX close (closing auction) [K]",
        )
    ],
    "ASHR": [
        (
            None,
            "foreign_close",
            "15:00",
            "Asia/Shanghai",
            "https://etf.dws.com/en-us/ASHR-harvest-csi-300-china-a-shares-etf/",
            "Shanghai/Shenzhen close",
        )
    ],
}
BOND_TICKERS = ["LQD", "HYG", "MUB", "EMB", "AGG", "TLT", "JNK", "BKLN", "BND"]
US_EQ_TICKERS = ["SPY", "DIA", "IVV", "IWM", "QQQ", "VOO"]


def build_nav_clock(us: pd.DataFrame, ind: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for r in us.itertuples(index=False):
        t = r.ticker
        start = str(r.listing_date)
        if t in US_CLOCK:
            spec = US_CLOCK[t]
        elif t in BOND_TICKERS:
            spec = [
                (
                    None,
                    "evaluated_bond",
                    "16:00",
                    "America/New_York",
                    r.source_url,
                    "Evaluated bond prices at 4pm ET [K]",
                )
            ]
        elif t in US_EQ_TICKERS:
            spec = [(None, "us_close_16et", "16:00", "America/New_York", r.source_url, "")]
        else:
            raise KeyError(t)
        for i, (eff, basis, tm, tz, url, note) in enumerate(spec):
            nxt = spec[i + 1][0] if i + 1 < len(spec) else None
            rows.append(
                {
                    "instrument_id": r.instrument_id,
                    "effective_from": eff or start,
                    "effective_to": (pd.Timestamp(nxt) - pd.Timedelta(days=1)).date().isoformat()
                    if nxt
                    else "",
                    "nav_basis": basis,
                    "valuation_time_local": tm or "",
                    "valuation_tz": tz or "",
                    "source_url": url,
                    "notes": note,
                }
            )
    for r in ind.itertuples(index=False):
        start_candidates = [d for d in (r.listing_date, r.inception_date) if isinstance(d, str) and d]
        start = min(start_candidates) if start_candidates else "2007-01-01"
        if r.group in ("IN_GOLD", "IN_SILVER"):
            metal_time = (
                ("10:30", "LBMA Gold Price AM") if r.group == "IN_GOLD" else ("12:00", "LBMA Silver Price")
            )
            pre_note = f"{metal_time[1]} converted to INR with duty, levies and a notional delivery premium (SEBI circular 26 Feb 2026 para 1; D-005)"
            if start <= "2026-03-31":
                rows.append(
                    {
                        "instrument_id": r.instrument_id,
                        "effective_from": start,
                        "effective_to": "2026-03-31",
                        "nav_basis": "in_import_parity",
                        "valuation_time_local": metal_time[0],
                        "valuation_tz": "Europe/London",
                        "source_url": SEBI_2026,
                        "notes": pre_note,
                    }
                )
            rows.append(
                {
                    "instrument_id": r.instrument_id,
                    "effective_from": max(start, "2026-04-01"),
                    "effective_to": "",
                    "nav_basis": "in_domestic_spot",
                    "valuation_time_local": "",
                    "valuation_tz": "Asia/Kolkata",
                    "source_url": SEBI_2026,
                    "notes": "Exchange-polled spot used to settle physical gold/silver derivatives (SEBI circular para 3, from 1 Apr 2026); polling time per AMFI uniform policy not yet located (OQ-10)",
                }
            )
        elif r.group == "IN_INTL":
            hk = "hk" in (r.subgroup or "")
            rows.append(
                {
                    "instrument_id": r.instrument_id,
                    "effective_from": start,
                    "effective_to": "",
                    "nav_basis": "foreign_close",
                    "valuation_time_local": "16:00",
                    "valuation_tz": "Asia/Hong_Kong" if hk else "America/New_York",
                    "source_url": r.source_url,
                    "notes": "Previous overseas session close (Indian NAV for day t uses the overseas close of t-1 for US underlyings) [K]",
                }
            )
        else:
            rows.append(
                {
                    "instrument_id": r.instrument_id,
                    "effective_from": start,
                    "effective_to": "",
                    "nav_basis": "in_close",
                    "valuation_time_local": "15:30",
                    "valuation_tz": "Asia/Kolkata",
                    "source_url": r.source_url,
                    "notes": "Indian market close",
                }
            )
    return pd.DataFrame(rows)


# --------------------------------------------------------------------------- corporate actions (US)
# Verified when yfinance and Tiingo `splitFactor` agree on date and ratio (P02 checks) and, where the
# NAV source is raw, the NAV file shows the same jump.
NAV_ADJUSTED_SOURCES = {"us_iss_ishares"}  # iShares NAV histories are retroactively split-adjusted
NAV_DATE_OVERRIDE = {("BNO", "2013-08-29"): "2013-08-28"}  # USCF NAV file halves one day earlier


def build_corporate_actions_us(raw: Path, us: pd.DataFrame) -> pd.DataFrame:
    rows = []
    nav_src = dict(zip(us["ticker"], us["nav_source_id"], strict=True))
    for p in sorted((raw / "us_px_yf" / "splits").glob("*_splits.json")):
        t = p.stem.split("_")[0]
        for date, ratio in json.loads(p.read_text()).items():
            if date.startswith("_"):
                continue
            tw = raw / "us_px_tiingo" / "split_windows" / f"{t}_{date}.json"
            tiingo = (
                [r for r in json.loads(tw.read_text()) if r.get("splitFactor", 1) != 1] if tw.exists() else []
            )
            agree = any(r["date"][:10] == date and abs(r["splitFactor"] - ratio) < 1e-4 for r in tiingo)
            kind = "split" if ratio > 1 else "reverse_split"
            label = (
                f"{int(round(ratio))}-for-1 split"
                if ratio > 1
                else f"1-for-{int(round(1 / ratio))} reverse split"
            )
            base_note = f"{label}; shares per old share = {ratio:g}. yfinance + Tiingo splitFactor {'agree' if agree else 'DISAGREE'}"
            src = f"https://api.tiingo.com/tiingo/daily/{t.lower()}/prices (splitFactor); yfinance Ticker('{t}').splits"
            if nav_src.get(t) in NAV_ADJUSTED_SOURCES:
                rows.append(
                    {
                        "instrument_id": f"US:{t}",
                        "ex_date": date,
                        "type": kind,
                        "ratio": ratio,
                        "applies_to": "price",
                        "verified": "y" if agree else "n",
                        "source_url": src,
                        "notes": base_note + "; issuer NAV history is already split-adjusted (no jump)",
                    }
                )
            elif (t, date) in NAV_DATE_OVERRIDE:
                rows.append(
                    {
                        "instrument_id": f"US:{t}",
                        "ex_date": date,
                        "type": kind,
                        "ratio": ratio,
                        "applies_to": "price",
                        "verified": "y" if agree else "n",
                        "source_url": src,
                        "notes": base_note,
                    }
                )
                rows.append(
                    {
                        "instrument_id": f"US:{t}",
                        "ex_date": NAV_DATE_OVERRIDE[(t, date)],
                        "type": kind,
                        "ratio": ratio,
                        "applies_to": "nav",
                        "verified": "y",
                        "source_url": "data/manual_drop/us_iss_uscf (USCF NAV CSV)",
                        "notes": "USCF NAV file changes basis one trading day before the price ex-date",
                    }
                )
            else:
                rows.append(
                    {
                        "instrument_id": f"US:{t}",
                        "ex_date": date,
                        "type": kind,
                        "ratio": ratio,
                        "applies_to": "both",
                        "verified": "y" if agree else "n",
                        "source_url": src,
                        "notes": base_note + "; raw issuer NAV (where available) shows the same jump",
                    }
                )
    return pd.DataFrame(rows)

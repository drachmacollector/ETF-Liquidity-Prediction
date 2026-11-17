"""Parsers for every source format confirmed in P01. Reused by the ingestion adapters in P04–P06.

Each parser takes raw bytes (exactly as downloaded) and returns a typed, source-shaped DataFrame.
Golden-file tests in `tests/unit/test_parsers.py` pin the expected columns.
"""

from __future__ import annotations

import io
import json
import re
import zipfile
from html import unescape

import pandas as pd


# --------------------------------------------------------------------------- US issuers
def parse_spdr_gold_archive(raw: bytes) -> pd.DataFrame:
    """SPDR Gold Trust "Historical Archive" XLSX (GLD, GLDM). Holiday rows are dropped."""
    xl = pd.ExcelFile(io.BytesIO(raw), engine="calamine")
    sheet = next(s for s in xl.sheet_names if "Historical Archive" in s)
    df = pd.read_excel(xl, sheet_name=sheet)
    df.columns = [str(c).strip() for c in df.columns]
    rename = {}
    for c in df.columns:
        lc = c.lower()
        if lc == "date":
            rename[c] = "date"
        elif lc.startswith("closing price"):
            rename[c] = "issuer_close"
        elif lc.startswith("ounces of gold per share"):
            rename[c] = "oz_per_share"
        elif lc.startswith("nav/share"):
            rename[c] = "nav"
        elif lc.startswith("indicative price per share"):
            rename[c] = "indicative_price_415"
        elif lc.startswith("mid point of bid/ask"):
            rename[c] = "issuer_mid"
        elif lc.startswith("premium/discount"):
            rename[c] = "issuer_prem_pct"
        elif lc.startswith("daily share volume"):
            rename[c] = "issuer_volume"
        elif lc.startswith("total ounces"):
            rename[c] = "total_oz"
        elif lc.startswith("tonnes"):
            rename[c] = "tonnes"
        elif lc.startswith("total net asset value"):
            rename[c] = "total_net_assets"
    df = df.rename(columns=rename)
    df["date"] = pd.to_datetime(df["date"], format="%d-%b-%Y", errors="coerce")
    df = df.dropna(subset=["date"])
    num_cols = [c for c in df.columns if c != "date"]
    for c in num_cols:
        df[c] = pd.to_numeric(df[c], errors="coerce")  # "US Holiday" / "HOLIDAY" -> NaN
    df = df.dropna(subset=["nav"]).sort_values("date").reset_index(drop=True)
    df["shares_out"] = df["total_net_assets"] / df["nav"]
    df["issuer_prem_bps"] = df["issuer_prem_pct"] * 100.0
    return df


_SS_NS = "urn:schemas-microsoft-com:office:spreadsheet"


def _xml_sheet_rows(text: str, sheet: str) -> list[list[str]]:
    """Rows of one worksheet from a SpreadsheetML (XML 2003) file, tolerant of malformed markup."""
    m = re.search(rf'<ss:Worksheet ss:Name="{re.escape(sheet)}">(.*?)</ss:Worksheet>', text, flags=re.S)
    if not m:
        raise ValueError(f"worksheet {sheet!r} not found")
    rows = []
    for row in re.findall(r"<ss:Row[^>]*>(.*?)</ss:Row>", m.group(1), flags=re.S):
        cells = re.findall(r"<ss:Cell[^>]*>(.*?)</ss:Cell>|<ss:Cell[^>]*/>", row, flags=re.S)
        vals = []
        for c in cells:
            d = re.search(r"<ss:Data[^>]*>(.*?)</ss:Data>", c or "", flags=re.S)
            vals.append(unescape(d.group(1)).strip() if d else "")
        rows.append(vals)
    return rows


def parse_ishares_fund_download(raw: bytes) -> pd.DataFrame:
    """iShares "Data Download" (SpreadsheetML): the `Historical` sheet (NAV, shares outstanding)."""
    text = raw.decode("utf-8", errors="replace")
    rows = _xml_sheet_rows(text, "Historical")
    header_idx = next(i for i, r in enumerate(rows) if r and r[0] == "As Of")
    header = rows[header_idx]
    body = [r for r in rows[header_idx + 1 :] if r and r[0]]
    df = pd.DataFrame([r[: len(header)] for r in body], columns=header)
    out = pd.DataFrame(
        {
            "date": pd.to_datetime(df["As Of"], format="%b %d, %Y", errors="coerce"),
            "nav": pd.to_numeric(df["NAV per Share"], errors="coerce"),
            "ex_dividend": pd.to_numeric(df.get("Ex-Dividends"), errors="coerce"),
            "shares_out": pd.to_numeric(df["Shares Outstanding"].str.replace(",", ""), errors="coerce"),
        }
    )
    return out.dropna(subset=["date", "nav"]).sort_values("date").reset_index(drop=True)


def parse_ssga_navhist(raw: bytes) -> pd.DataFrame:
    """SSGA `navhist-us-en-<ticker>.xlsx`: Date, NAV, Shares Outstanding, Total Net Assets."""
    x = pd.read_excel(io.BytesIO(raw), header=None, engine="calamine")
    header_idx = next(i for i in range(min(len(x), 20)) if str(x.iat[i, 0]).strip() == "Date")
    df = x.iloc[header_idx + 1 :, :4].copy()
    df.columns = ["date", "nav", "shares_out", "total_net_assets"]
    df["date"] = pd.to_datetime(df["date"], format="%d-%b-%Y", errors="coerce")
    for c in ("nav", "shares_out", "total_net_assets"):
        df[c] = pd.to_numeric(df[c], errors="coerce")
    return df.dropna(subset=["date", "nav"]).sort_values("date").reset_index(drop=True)


def parse_tiingo_prices(raw: bytes) -> pd.DataFrame:
    """Tiingo daily prices JSON. `close/open/high/low/volume` are raw (unadjusted)."""
    df = pd.DataFrame(json.loads(raw))
    if df.empty:
        return df
    df["date"] = pd.to_datetime(df["date"]).dt.tz_localize(None)
    keep = ["date", "open", "high", "low", "close", "volume", "adjClose", "divCash", "splitFactor"]
    df = df[[c for c in keep if c in df.columns]].rename(
        columns={"adjClose": "adj_close", "divCash": "div_cash", "splitFactor": "split_factor"}
    )
    return df.sort_values("date").reset_index(drop=True)


# --------------------------------------------------------------------------- India
BHAV_UDIFF_MAP = {
    "TradDt": "date",
    "ISIN": "isin",
    "TckrSymb": "symbol",
    "SctySrs": "series",
    "OpnPric": "open",
    "HghPric": "high",
    "LwPric": "low",
    "ClsPric": "close",
    "LastPric": "last",
    "PrvsClsgPric": "prev_close",
    "TtlTradgVol": "volume",
    "TtlTrfVal": "traded_value",
    "TtlNbOfTxsExctd": "n_trades",
}
BHAV_LEGACY_MAP = {
    "TIMESTAMP": "date",
    "ISIN": "isin",
    "SYMBOL": "symbol",
    "SERIES": "series",
    "OPEN": "open",
    "HIGH": "high",
    "LOW": "low",
    "CLOSE": "close",
    "LAST": "last",
    "PREVCLOSE": "prev_close",
    "TOTTRDQTY": "volume",
    "TOTTRDVAL": "traded_value",
    "TOTALTRADES": "n_trades",
}
BHAV_COLUMNS = list(dict.fromkeys(BHAV_UDIFF_MAP.values())) + ["source_schema"]


def parse_nse_bhavcopy(raw: bytes) -> pd.DataFrame:
    """NSE CM bhavcopy (zipped CSV), legacy or UDiFF schema, normalised to `BHAV_COLUMNS`."""
    if raw[:2] == b"PK":
        with zipfile.ZipFile(io.BytesIO(raw)) as z:
            raw = z.read(z.namelist()[0])
    df = pd.read_csv(io.BytesIO(raw), dtype=str)
    df.columns = [c.strip() for c in df.columns]
    df = df.loc[:, [c for c in df.columns if c and not c.startswith("Unnamed")]]
    if "TckrSymb" in df.columns:
        df = df.rename(columns=BHAV_UDIFF_MAP)
        df["date"] = pd.to_datetime(df["date"], format="%Y-%m-%d")
        df["source_schema"] = "udiff"
    elif "SYMBOL" in df.columns:
        df = df.rename(columns=BHAV_LEGACY_MAP)
        df["date"] = pd.to_datetime(df["date"], format="%d-%b-%Y")
        df["source_schema"] = "legacy"
    else:
        raise ValueError(f"unknown bhavcopy schema: {list(df.columns)[:8]}")
    for c in ("open", "high", "low", "close", "last", "prev_close", "volume", "traded_value", "n_trades"):
        df[c] = pd.to_numeric(df[c], errors="coerce")
    for c in ("isin", "symbol", "series"):
        df[c] = df[c].str.strip()
    return df[BHAV_COLUMNS].reset_index(drop=True)


def parse_amfi_navall(raw: bytes) -> pd.DataFrame:
    """AMFI `NAVAll.txt`: semicolon-delimited rows under category/AMC header lines."""
    rows, category, amc = [], None, None
    for line in raw.decode("utf-8", errors="replace").splitlines():
        line = line.strip()
        if not line or line.startswith("Scheme Code"):
            continue
        parts = line.split(";")
        if len(parts) >= 6 and parts[0].isdigit():
            rows.append(
                {
                    "amfi_scheme_code": int(parts[0]),
                    "isin_growth": parts[1] if parts[1] not in ("-", "") else None,
                    "isin_reinv": parts[2] if parts[2] not in ("-", "") else None,
                    "scheme_name": parts[3].strip(),
                    "nav": pd.to_numeric(parts[-2], errors="coerce"),
                    "date": pd.to_datetime(parts[-1], format="%d-%b-%Y", errors="coerce"),
                    "category": category,
                    "amc": amc,
                }
            )
        elif "Schemes(" in line or line.startswith(("Open Ended", "Close Ended", "Interval")):
            category = line
        else:
            amc = line
    return pd.DataFrame(rows)


def parse_amfi_all_for_date(raw: bytes) -> pd.DataFrame:
    """AMFI `/api/nav-history?query_type=all_for_date`: one row per scheme plan, with upload timestamp."""
    data = json.loads(raw)["data"] or []
    rows = []
    for mf in data:
        for sch in mf.get("schemes", []):
            for n in sch.get("navs", []):
                rows.append(
                    {
                        "amc": mf.get("mfName"),
                        "amfi_scheme_code": int(n["SD_ID"]),
                        "nav_name": n.get("NAV_Name"),
                        "isin_growth": n.get("ISIN_PO") or None,
                        "isin_reinv": n.get("ISIN_RI") or None,
                        "nav": pd.to_numeric(n.get("hNAV_Amt"), errors="coerce"),
                        "date": pd.to_datetime(n.get("hNAV_Date")).tz_localize(None).normalize(),
                        # AMFI labels this "Z" but the value is IST wall-clock time (matches hNAV_Upload_display).
                        "uploaded_at_ist": pd.to_datetime(n.get("hNAV_Dtstamp"))
                        .tz_localize(None)
                        .tz_localize("Asia/Kolkata"),
                    }
                )
    return pd.DataFrame(rows)


def parse_mfapi(raw: bytes) -> pd.DataFrame:
    """`api.mfapi.in/mf/<code>`: full NAV history for one scheme."""
    d = json.loads(raw)
    df = pd.DataFrame(d.get("data", []))
    if df.empty:
        return df
    df["date"] = pd.to_datetime(df["date"], format="%d-%m-%Y")
    df["nav"] = pd.to_numeric(df["nav"], errors="coerce")
    df["amfi_scheme_code"] = int(d["meta"]["scheme_code"])
    df["isin_growth"] = d["meta"].get("isin_growth")
    return df[["amfi_scheme_code", "isin_growth", "date", "nav"]].sort_values("date").reset_index(drop=True)


# --------------------------------------------------------------------------- market series
def parse_fred_csv(raw: bytes) -> pd.DataFrame:
    """FRED `fredgraph.csv`: observation_date, <SERIES>; '.' and blanks are missing."""
    df = pd.read_csv(io.BytesIO(raw), na_values=[".", ""])
    date_col = df.columns[0]
    value_col = df.columns[1]
    return pd.DataFrame(
        {"date": pd.to_datetime(df[date_col]), "value": pd.to_numeric(df[value_col], errors="coerce")}
    ).assign(series_code=value_col)


def parse_eia_xls(raw: bytes) -> pd.DataFrame:
    """EIA `hist_xls/*.xls` daily history: first data sheet, columns date and value."""
    sheets = pd.read_excel(io.BytesIO(raw), sheet_name=None, header=None, engine="calamine")
    name = next(s for s in sheets if s.lower().startswith("data"))
    df = sheets[name]
    hdr = next(i for i in range(10) if str(df.iat[i, 0]).strip().lower() == "date")
    out = df.iloc[hdr + 1 :, :2].copy()
    out.columns = ["date", "value"]
    out["date"] = pd.to_datetime(out["date"], errors="coerce")
    out["value"] = pd.to_numeric(out["value"], errors="coerce")
    return out.dropna(subset=["date"]).reset_index(drop=True)


def date_span(df: pd.DataFrame, col: str = "date") -> tuple[str | None, str | None, int]:
    """(first, last, rows) helper for probe reports."""
    if df is None or df.empty or col not in df:
        return None, None, 0
    s = df[col].dropna()
    if s.empty:
        return None, None, 0
    return str(s.min().date()), str(s.max().date()), int(len(df))


def parse_amfi_historical_period(raw: bytes) -> pd.DataFrame:
    """AMFI `/api/nav-history?query_type=historical_period&sd_id=<code>` (max 5-year window)."""
    d = json.loads(raw).get("data") or {}
    rows = []
    for g in d.get("nav_groups", []):
        for rec in g.get("historical_records", []):
            rows.append(
                {
                    "nav_name": g.get("nav_name"),
                    "date": pd.to_datetime(rec["date"]),
                    "nav": pd.to_numeric(rec.get("nav"), errors="coerce"),
                    # Labelled "Z" but it is IST wall-clock time (matches upload_time_display).
                    "uploaded_at_ist": pd.to_datetime(rec.get("upload_time"))
                    .tz_localize(None)
                    .tz_localize("Asia/Kolkata"),
                }
            )
    return pd.DataFrame(rows)

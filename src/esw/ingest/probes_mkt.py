"""P01 probes for market-wide, underlying and FX series and for calendars."""

from __future__ import annotations

import io

from esw.ingest import parsers as P
from esw.ingest.probe import ProbeRow, ProbeRunner, probe

FRED_CSV = "https://fred.stlouisfed.org/graph/fredgraph.csv?id={sid}"
FRED_TOS = "https://fred.stlouisfed.org/legal/"
FRED_SERIES = {
    "VIXCLS": "vix",
    "OVXCLS": "ovx",
    "GVZCLS": "gvz",
    "BAA10Y": "baa10y",
    "AAA10Y": "aaa10y",
    "BAMLH0A0HYM2": "hy_oas (history check)",
    "DGS10": "ust10y",
    "DGS2": "ust2y",
    "TEDRATE": "tedrate",
    "DTWEXBGS": "usd_broad",
    "DEXINUS": "usdinr",
    "DEXBZUS": "usdbrl",
    "DEXMXUS": "usdmxn",
    "DEXCHUS": "usdcny",
    "DEXJPUS": "usdjpy",
    "DEXHKUS": "usdhkd",
    "DEXUSEU": "eurusd",
}


@probe("mkt_fred")
def probe_fred(r: ProbeRunner) -> list[ProbeRow]:
    rows = []
    for sid, name in FRED_SERIES.items():
        url = FRED_CSV.format(sid=sid)
        resp = r.http.get(url)
        if resp.status_code != 200:
            rows.append(
                ProbeRow(
                    "mkt_fred",
                    name,
                    f"series:{sid}",
                    url,
                    "file",
                    status="NOT_FOUND",
                    notes=f"HTTP {resp.status_code}",
                )
            )
            continue
        r.save_raw("mkt_fred", f"{sid}.csv", resp.content, url=url, http_status=200)
        df = P.parse_fred_csv(resp.content)
        a, b, n = P.date_span(df.dropna(subset=["value"]))
        if sid == "VIXCLS":
            lines = resp.content.decode().splitlines()
            r.save_fixture(
                "mkt_fred", "VIXCLS_trimmed.csv", ("\n".join(lines[:30] + ["2001-01-01,."]) + "\n").encode()
            )
        note = ""
        if sid == "BAMLH0A0HYM2":
            note = "ICE BofA series: FRED serves only ~3 years of history (licensing). Not usable for 2004+ (OQ-09)."
        rows.append(
            ProbeRow(
                "mkt_fred",
                name,
                f"series:{sid}",
                FRED_CSV,
                "file",
                "none",
                "PARTIAL" if sid == "BAMLH0A0HYM2" else "OK",
                a,
                b,
                n,
                "date, value",
                "n",
                "CSV needs no key; API key optional (MI-03)",
                FRED_TOS,
                "Public data; cite source; some series licensed",
                note,
            )
        )
    return rows


@probe("mkt_eia")
def probe_eia(r: ProbeRunner) -> list[ProbeRow]:
    rows = []
    for code, base in [
        ("RCLC1", "pet"),
        ("RCLC2", "pet"),
        ("RCLC3", "pet"),
        ("RCLC4", "pet"),
        ("RNGC1", "ng"),
        ("RNGC2", "ng"),
        ("RNGC3", "ng"),
        ("RNGC4", "ng"),
    ]:
        url = f"https://www.eia.gov/dnav/{base}/hist_xls/{code}d.xls"
        resp = r.http.get(url)
        if resp.status_code != 200:
            rows.append(
                ProbeRow(
                    "mkt_eia", "NYMEX futures contract", f"series:{code}", url, "file", status="NOT_FOUND"
                )
            )
            continue
        r.save_raw("mkt_eia", f"{code}d.xls", resp.content, url=url, http_status=200)
        df = P.parse_eia_xls(resp.content)
        a, b, n = P.date_span(df.dropna(subset=["value"]))
        if code == "RCLC1":
            import pandas as pd

            x = pd.read_excel(io.BytesIO(resp.content), sheet_name=None, header=None)
            name = next(s for s in x if s.lower().startswith("data"))
            buf = io.BytesIO()
            with pd.ExcelWriter(buf, engine="openpyxl") as w:
                pd.DataFrame([["fixture"]]).to_excel(w, sheet_name="Contents", index=False, header=False)
                x[name].iloc[:40].to_excel(w, sheet_name=name, index=False, header=False)
            r.save_fixture("mkt_eia", "RCLC1_trimmed.xlsx", buf.getvalue())
        rows.append(
            ProbeRow(
                "mkt_eia",
                "NYMEX futures contract 1-4 daily settle",
                f"series:{code}",
                url,
                "file",
                "none",
                "PARTIAL",
                a,
                b,
                n,
                "date, value",
                "n",
                "",
                "https://www.eia.gov/about/copyrights_reuse.php",
                "Public domain (US government)",
                f"History ends {b}: EIA stopped publishing futures prices after 2024-04-05 (OQ-08).",
            )
        )
    return rows


@probe("mkt_fut_yf")
def probe_yf_futures(r: ProbeRunner) -> list[ProbeRow]:
    import yfinance as yf

    rows = []
    for t, note in [
        ("GC=F", "gold front (continuous, roll jumps)"),
        ("SI=F", "silver front"),
        ("PL=F", "platinum front"),
        ("PA=F", "palladium front"),
        ("CL=F", "WTI front"),
        ("NG=F", "Henry Hub front"),
        ("CLZ26.NYM", "WTI single contract (curve after 2024)"),
        ("NGZ26.NYM", "natgas single contract"),
        ("RUB=X", "USD/RUB"),
        ("EGP=X", "USD/EGP"),
        ("TRY=X", "USD/TRY"),
        ("^EGX30.CA", "Egypt EGX30"),
        ("IMOEX.ME", "Moscow index"),
        ("GD.AT", "Athens general index"),
        ("^NSEI", "Nifty 50"),
    ]:
        try:
            df = yf.Ticker(t).history(period="max", auto_adjust=False)
        except Exception as exc:  # noqa: BLE001
            df, note = None, f"{note}; error {type(exc).__name__}"
        ok = df is not None and len(df) > 0
        rows.append(
            ProbeRow(
                "mkt_fut_yf",
                note,
                f"yf:{t}",
                "yfinance",
                "library",
                "none",
                "OK" if ok else "NOT_FOUND",
                str(df.index.min().date()) if ok else "",
                str(df.index.max().date()) if ok else "",
                len(df) if ok else 0,
                "OHLCV",
                "n",
                "Unofficial",
                "https://legal.yahoo.com/us/en/yahoo/terms/otos/index.html",
                "Unofficial; fallback/proxy only",
                note,
            )
        )
    return rows


@probe("mkt_cal")
def probe_calendars(r: ProbeRunner) -> list[ProbeRow]:
    import exchange_calendars as xc

    names = set(xc.get_calendar_names(include_aliases=True))
    rows = []
    for code, market in [
        ("XNYS", "NYSE"),
        ("XBOM", "BSE (India; NSE not in library)"),
        ("XNSE", "NSE"),
        ("XLON", "London"),
        ("XHKG", "Hong Kong"),
        ("XTKS", "Tokyo"),
        ("XSHG", "Shanghai"),
        ("XIST", "Istanbul"),
        ("BVMF", "Sao Paulo"),
        ("XMEX", "Mexico"),
        ("XCAI", "Cairo"),
        ("XATH", "Athens"),
        ("MISX", "Moscow"),
    ]:
        ok = code in names
        first = ""
        if ok:
            cal = xc.get_calendar(code)
            first = str(cal.first_session.date())
        rows.append(
            ProbeRow(
                "mkt_cal",
                f"exchange calendar: {market}",
                f"cal:{code}",
                "exchange_calendars",
                "library",
                "none",
                "OK" if ok else "NOT_FOUND",
                first,
                "",
                "",
                "sessions, holidays, early closes",
                "",
                notes=""
                if ok
                else "Not in exchange_calendars: build a small hand table in P02 if needed; "
                "unscheduled closures come from the operational-event table (P03).",
            )
        )
    return rows

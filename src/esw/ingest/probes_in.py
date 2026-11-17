"""P01 probes for Indian sources: NSE bhavcopy, BSE, AMFI, mfapi, domestic spot, India VIX."""

from __future__ import annotations

import io
import json
import zipfile
from datetime import date

import pandas as pd

from esw.ingest import parsers as P
from esw.ingest.candidates import IN_CONTROL_SYMBOLS, classify_india
from esw.ingest.probe import ProbeRow, ProbeRunner, probe

NSE_ARCHIVE = "https://archives.nseindia.com/content"
NSE_ARCHIVE_NEW = "https://nsearchives.nseindia.com/content"
NSE_TOS = "https://www.nseindia.com/terms-of-use"
AMFI_TOS = "https://www.amfiindia.com/disclaimer"
AMFI_API = "https://www.amfiindia.com/api/nav-history"
FIXTURE_SYMBOLS = {"GOLDBEES", "SILVERAG", "SILVRETF", "NIFTYBEES", "MAFANG", "GOLDETF", "SILVERBEES"}

_MON = ["JAN", "FEB", "MAR", "APR", "MAY", "JUN", "JUL", "AUG", "SEP", "OCT", "NOV", "DEC"]


def udiff_url(d: date, base: str = NSE_ARCHIVE) -> str:
    return f"{base}/cm/BhavCopy_NSE_CM_0_0_0_{d:%Y%m%d}_F_0000.csv.zip"


def legacy_url(d: date, base: str = NSE_ARCHIVE) -> str:
    return f"{base}/historical/EQUITIES/{d.year}/{_MON[d.month - 1]}/cm{d.day:02d}{_MON[d.month - 1]}{d.year}bhav.csv.zip"


def _trim_bhav_zip(raw: bytes, keep_symbols: set[str], extra_rows: int = 15) -> bytes:
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        name = z.namelist()[0]
        lines = z.read(name).decode("utf-8", errors="replace").splitlines()
    head, body = lines[0], lines[1:]
    sym_col = 7 if head.startswith("TradDt") else 0
    picked = [ln for ln in body if ln.split(",")[sym_col] in keep_symbols] + body[:extra_rows]
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr(name, "\n".join([head, *picked]) + "\n")
    return buf.getvalue()


@probe("in_bhav_udiff")
def probe_bhav_udiff(r: ProbeRunner) -> list[ProbeRow]:
    # The newer host stalls on non-browser clients: one attempt, recorded, not retried or worked around.
    d0 = date(2025, 10, 9)
    try:
        resp = r.http.get(udiff_url(d0, NSE_ARCHIVE_NEW), timeout=25, max_retries=0)
        new_host = f"HTTP {resp.status_code}"
    except Exception as exc:  # noqa: BLE001
        new_host = f"{type(exc).__name__} (no response)"
        r.log_failure("in_bhav_udiff", udiff_url(d0, NSE_ARCHIVE_NEW), new_host)
    results = []
    for d in [date(2024, 7, 8), date(2025, 10, 9), date(2026, 2, 1), date(2026, 11, 16)]:
        url = udiff_url(d)
        resp = r.http.get(url, max_retries=2)
        ok = resp.status_code == 200 and resp.content[:2] == b"PK"
        if ok:
            r.save_raw("in_bhav_udiff", f"{d:%Y%m%d}.csv.zip", resp.content, url=url, http_status=200)
            df = P.parse_nse_bhavcopy(resp.content)
            results.append((d, len(df)))
            if d == date(2025, 10, 9):
                r.save_fixture(
                    "in_bhav_udiff",
                    "BhavCopy_NSE_CM_20251009_trimmed.csv.zip",
                    _trim_bhav_zip(resp.content, FIXTURE_SYMBOLS),
                )
        else:
            r.log_failure("in_bhav_udiff", url, "not available", resp.status_code)
            results.append((d, f"HTTP {resp.status_code}"))
    return [
        ProbeRow(
            "in_bhav_udiff",
            "NSE CM bhavcopy, UDiFF format (from 2024-07-08)",
            "",
            f"{NSE_ARCHIVE}/cm/BhavCopy_NSE_CM_0_0_0_YYYYMMDD_F_0000.csv.zip",
            "file",
            "none",
            "OK" if all(isinstance(x[1], int) for x in results) else "PARTIAL",
            "2024-07-08",
            str(max(d for d, n in results if isinstance(n, int))),
            "",
            "TradDt, ISIN, TckrSymb, SctySrs, OpnPric, HghPric, LwPric, ClsPric, LastPric, PrvsClsgPric, TtlTradgVol, TtlTrfVal, TtlNbOfTxsExctd",
            "n",
            "archives.nseindia.com responds to the project user agent; nsearchives.nseindia.com does not",
            NSE_TOS,
            "Exchange data; research use; no redistribution",
            f"Samples: {results}. New host nsearchives.nseindia.com: {new_host}. Sunday special session 2026-02-01 file exists.",
        )
    ]


@probe("in_bhav_legacy")
def probe_bhav_legacy(r: ProbeRunner) -> list[ProbeRow]:
    results = []
    for d in [
        date(2016, 1, 4),
        date(2020, 3, 19),
        date(2024, 7, 5),
        date(2015, 12, 15),
        date(2013, 8, 27),
        date(2007, 3, 15),
    ]:
        url = legacy_url(d)
        resp = r.http.get(url, max_retries=1)
        if resp.status_code == 200 and resp.content[:2] == b"PK":
            r.save_raw("in_bhav_legacy", f"{d:%Y%m%d}.csv.zip", resp.content, url=url, http_status=200)
            results.append((str(d), len(P.parse_nse_bhavcopy(resp.content))))
            if d == date(2020, 3, 19):
                r.save_fixture(
                    "in_bhav_legacy",
                    "cm19MAR2020bhav_trimmed.csv.zip",
                    _trim_bhav_zip(resp.content, FIXTURE_SYMBOLS),
                )
        else:
            r.log_failure("in_bhav_legacy", url, "forbidden/not found", resp.status_code)
            results.append((str(d), f"HTTP {resp.status_code}"))
    return [
        ProbeRow(
            "in_bhav_legacy",
            "NSE CM bhavcopy, legacy format (to 2024-07-05)",
            "",
            f"{NSE_ARCHIVE}/historical/EQUITIES/YYYY/MON/cmDDMONYYYYbhav.csv.zip",
            "file",
            "none",
            "PARTIAL",
            "2016-01-04",
            "2024-07-05",
            "",
            "SYMBOL, SERIES, OPEN, HIGH, LOW, CLOSE, LAST, PREVCLOSE, TOTTRDQTY, TOTTRDVAL, TIMESTAMP, TOTALTRADES, ISIN",
            "n",
            "",
            NSE_TOS,
            "Exchange data; research use; no redistribution",
            f"Samples: {results}. Files before 2016-01-01 return HTTP 403 to scripts: pre-2016 prices need "
            "a fallback (yfinance .NS from 2009 for some ETFs) or manual download (MI-05).",
        )
    ]


@probe("in_bse_bhav")
def probe_bse(r: ProbeRunner) -> list[ProbeRow]:
    url = "https://www.bseindia.com/download/BhavCopy/Equity/BhavCopy_BSE_CM_0_0_0_20251009_F_0000.CSV"
    resp = r.http.get(url, max_retries=0)
    r.log_failure("in_bse_bhav", url, "blocked", resp.status_code)
    return [
        ProbeRow(
            "in_bse_bhav",
            "BSE equity bhavcopy (fallback)",
            "",
            url,
            "file",
            "none",
            "BLOCKED" if resp.status_code == 403 else "PARTIAL",
            tos_url="https://www.bseindia.com/static/about/termsofuse.aspx",
            notes=f"HTTP {resp.status_code} to the project user agent; NSE archive is sufficient from 2016.",
        )
    ]


def _navall(r: ProbeRunner) -> tuple[pd.DataFrame, bytes]:
    url = "https://portal.amfiindia.com/spages/NAVAll.txt"
    resp = r.http.get(url)
    r.save_raw("in_amfi_navall", "NAVAll.txt", resp.content, url=url, http_status=resp.status_code)
    return P.parse_amfi_navall(resp.content), resp.content


def _india_etfs(navall: pd.DataFrame) -> pd.DataFrame:
    grp = [classify_india(n, c) for n, c in zip(navall["scheme_name"], navall["category"], strict=False)]
    out = navall.assign(group=grp)
    return out[out["group"].notna()].reset_index(drop=True)


def trim_navall(raw: bytes, isins: set[str]) -> bytes:
    """Keep the header line and, for each wanted ISIN, its nearest category and AMC header lines."""
    lines = raw.decode("utf-8", errors="replace").splitlines()
    keep, category, amc = [lines[0]], None, None
    for ln in lines[1:]:
        s = ln.strip()
        if not s:
            continue
        parts = s.split(";")
        if len(parts) >= 6 and parts[0].isdigit():
            if any(i in s for i in isins):
                keep += [x for x in (category, amc) if x] + [s]
                category = amc = None  # already emitted for this block
        elif "Schemes(" in s:
            category, amc = s, None
        else:
            amc = s
    return ("\n".join(keep) + "\n").encode("utf-8")


@probe("in_amfi_navall")
def probe_navall(r: ProbeRunner) -> list[ProbeRow]:
    navall, raw = _navall(r)
    etfs = _india_etfs(navall)
    counts = etfs.groupby("group").size().to_dict()
    r.save_fixture("in_amfi_navall", "NAVAll_trimmed.txt", trim_navall(raw, {"INF769K01KG6", "INF204KB17I5"}))
    return [
        ProbeRow(
            "in_amfi_navall",
            "latest NAV for all schemes",
            "",
            "https://portal.amfiindia.com/spages/NAVAll.txt",
            "file",
            "none",
            "OK",
            str(navall["date"].min().date()),
            str(navall["date"].max().date()),
            len(navall),
            "Scheme Code; ISIN Growth; ISIN Reinvestment; Scheme Name; NAV; Date (+ category/AMC header lines)",
            "n",
            "",
            AMFI_TOS,
            "Public NAV data; research use",
            f"ETF counts by group in latest file: {counts}",
        )
    ]


@probe("in_amfi_hist")
def probe_amfi_hist(r: ProbeRunner) -> list[ProbeRow]:
    rows = []
    for d in ["2010-01-04", "2026-04-01"]:
        resp = r.http.get(AMFI_API, params={"query_type": "all_for_date", "from_date": d}, timeout=120)
        r.save_raw(
            "in_amfi_hist", f"all_for_date_{d}.json", resp.content, url=AMFI_API, http_status=resp.status_code
        )
        df = P.parse_amfi_all_for_date(resp.content)
        rows.append((d, len(df)))
    resp = r.http.get(
        AMFI_API,
        params={
            "query_type": "historical_period",
            "from_date": "2023-06-01",
            "to_date": "2026-11-16",
            "sd_id": "151779",
        },
        timeout=120,
    )
    r.save_raw(
        "in_amfi_hist",
        "hist_151779.json",
        resp.content,
        url=AMFI_API,
        http_status=resp.status_code,
        instrument_id="IN:INF769K01KG6",
    )
    h = P.parse_amfi_historical_period(resp.content)
    d = json.loads(resp.content)
    d["data"]["nav_groups"][0]["historical_records"] = d["data"]["nav_groups"][0]["historical_records"][:30]
    r.save_fixture("in_amfi_hist", "hist_151779_trimmed.json", json.dumps(d).encode())
    a, b, n = P.date_span(h)
    upl = h["uploaded_at_ist"].dt.hour.describe()[["min", "50%", "max"]].to_dict() if n else {}
    return [
        ProbeRow(
            "in_amfi_hist",
            "NAV history (all schemes for a date; one scheme for <= 5 years)",
            "IN:INF769K01KG6",
            f"{AMFI_API}?query_type=historical_period&from_date=YYYY-MM-DD&to_date=YYYY-MM-DD&sd_id=<scheme code>",
            "api",
            "none",
            "OK",
            a,
            b,
            n,
            "date, nav, upload_time (IST wall clock, mislabelled Z), repurchase, reissue",
            "n",
            "Max 5-year window per request; data from 2010-01-01",
            AMFI_TOS,
            "Public NAV data; research use",
            f"all_for_date rows: {rows}. Upload hour (IST) min/median/max for Mirae Silver ETF: {upl}. "
            "Upload timestamps give an exact known_at for each NAV.",
        )
    ]


@probe("in_mfapi")
def probe_mfapi(r: ProbeRunner) -> list[ProbeRow]:
    navall, _ = _navall(r)
    etfs = _india_etfs(navall)
    # Controls: look up by ISIN through the latest bhavcopy symbols
    resp = r.http.get(udiff_url(date(2026, 11, 16)))
    bhav = (
        P.parse_nse_bhavcopy(resp.content)
        if resp.status_code == 200
        else pd.DataFrame(columns=P.BHAV_COLUMNS)
    )
    ctrl_isins = set(bhav.loc[bhav["symbol"].isin(IN_CONTROL_SYMBOLS), "isin"])
    ctrl = navall[navall["isin_growth"].isin(ctrl_isins)].assign(group="IN_CTRL")
    targets = pd.concat([etfs, ctrl], ignore_index=True).drop_duplicates("amfi_scheme_code")
    sym_by_isin = dict(zip(bhav["isin"], bhav["symbol"], strict=False))
    out = []
    for _, row in targets.iterrows():
        code = int(row["amfi_scheme_code"])
        url = f"https://api.mfapi.in/mf/{code}"
        fr = r.http.get(url, timeout=90)
        if fr.status_code != 200:
            out.append(
                ProbeRow(
                    "in_mfapi",
                    row["group"],
                    f"IN:{row['isin_growth']}",
                    url,
                    "api",
                    status="NOT_FOUND",
                    notes=f"HTTP {fr.status_code}; {row['scheme_name']}",
                )
            )
            continue
        r.save_raw(
            "in_mfapi",
            f"{code}.json",
            fr.content,
            url=url,
            http_status=200,
            instrument_id=f"IN:{row['isin_growth']}",
        )
        df = P.parse_mfapi(fr.content)
        a, b, n = P.date_span(df)
        if code == 151779:
            d = json.loads(fr.content)
            d["data"] = d["data"][:40]
            r.save_fixture("in_mfapi", "mfapi_151779_trimmed.json", json.dumps(d).encode())
        sym = sym_by_isin.get(row["isin_growth"], "")
        out.append(
            ProbeRow(
                "in_mfapi",
                row["group"],
                f"IN:{row['isin_growth']}",
                "https://api.mfapi.in/mf/<scheme code>",
                "api",
                "none",
                "OK" if n else "NOT_FOUND",
                a,
                b,
                n,
                "date, nav",
                "n",
                "Unofficial mirror of AMFI data",
                "https://www.mfapi.in/",
                "Free API mirroring AMFI; research use",
                f"code={code}; nse_symbol_now={sym or 'not in 2026-11-16 bhavcopy'}; {row['scheme_name'][:70]}",
            )
        )
    return out


@probe("in_mfapi_vs_amfi")
def probe_mfapi_vs_amfi(r: ProbeRunner) -> list[ProbeRow]:
    """Cross-check mfapi against the official AMFI API for one scheme over its full overlap."""
    a = r.http.get(
        AMFI_API,
        params={
            "query_type": "historical_period",
            "from_date": "2023-06-01",
            "to_date": "2026-11-16",
            "sd_id": "151779",
        },
        timeout=120,
    )
    b = r.http.get("https://api.mfapi.in/mf/151779", timeout=90)
    da, db = P.parse_amfi_historical_period(a.content), P.parse_mfapi(b.content)
    m = da.merge(db, on="date", suffixes=("_amfi", "_mfapi"))
    agree = float((m["nav_amfi"].round(4) == m["nav_mfapi"].round(4)).mean()) if len(m) else 0.0
    return [
        ProbeRow(
            "in_mfapi_vs_amfi",
            "cross-check",
            "IN:INF769K01KG6",
            "",
            "api",
            "none",
            "OK" if agree >= 0.99 else "PARTIAL",
            rows=len(m),
            notes=f"Overlapping dates {len(m)}; exact agreement (4 dp) on {agree:.2%}",
        )
    ]


@probe("in_yf_pre2016")
def probe_yf_india(r: ProbeRunner) -> list[ProbeRow]:
    import yfinance as yf

    rows = []
    for sym in ["GOLDBEES", "NIFTYBEES", "MON100", "HNGSNGBEES", "^INDIAVIX"]:
        t = sym if sym.startswith("^") else f"{sym}.NS"
        df = yf.Ticker(t).history(period="max", auto_adjust=False)
        rows.append(
            ProbeRow(
                "in_yf_pre2016",
                "fallback prices before 2016 / India VIX",
                f"yf:{t}",
                "yfinance",
                "library",
                "none",
                "OK" if len(df) else "NOT_FOUND",
                str(df.index.min().date()) if len(df) else "",
                str(df.index.max().date()) if len(df) else "",
                len(df),
                "OHLCV",
                "split_only",
                "Unofficial",
                "https://legal.yahoo.com/us/en/yahoo/terms/otos/index.html",
                "Unofficial; fallback only",
                "No ISIN in Yahoo data: map by symbol with date validity"
                if not sym.startswith("^")
                else "India VIX daily close (nseindia.com API does not respond to scripts)",
            )
        )
    return rows


@probe("in_spot_mcx")
def probe_mcx(r: ProbeRunner) -> list[ProbeRow]:
    url = "https://www.mcxindia.com/market-data/spot-market-price"
    resp = r.http.get(url, max_retries=0)
    r.log_failure("in_spot_mcx", url, "blocked", resp.status_code)
    return [
        ProbeRow(
            "in_spot_mcx",
            "domestic gold/silver polled spot; futures bhavcopy",
            "",
            url,
            "manual",
            "none",
            "MANUAL_ONLY",
            tos_url="https://www.mcxindia.com/terms-of-use",
            tos_summary="Exchange data; research use",
            notes=f"HTTP {resp.status_code} to the project user agent; manual download (MI-05).",
        )
    ]


@probe("in_spot_ibja")
def probe_ibja(r: ProbeRunner) -> list[ProbeRow]:
    url = "https://www.ibjarates.com/"
    resp = r.http.get(url)
    r.save_raw("in_spot_ibja", "home.html", resp.content, url=url, http_status=resp.status_code)
    return [
        ProbeRow(
            "in_spot_ibja",
            "IBJA gold/silver daily rates",
            "",
            url,
            "manual",
            "none",
            "MANUAL_ONLY",
            tos_url=url,
            tos_summary="Website; history offered as 30-day PDFs; paid API (indiagoldratesapi.com)",
            notes=f"Homepage reachable (HTTP {resp.status_code}) but no downloadable history; manual (MI-05).",
        )
    ]


@probe("in_indiavix")
def probe_indiavix(r: ProbeRunner) -> list[ProbeRow]:
    url = "https://www.nseindia.com/api/historicalOR/vixhistory"
    try:
        resp = r.http.get(url, params={"from": "01-10-2025", "to": "31-10-2025"}, timeout=25, max_retries=0)
        note = f"HTTP {resp.status_code}"
    except Exception as exc:  # noqa: BLE001
        note = f"{type(exc).__name__}: no response to non-browser clients"
        r.log_failure("in_indiavix", url, note)
    return [
        ProbeRow(
            "in_indiavix",
            "India VIX history",
            "",
            url,
            "api",
            "none",
            "BLOCKED",
            tos_url=NSE_TOS,
            notes=f"{note}. Use yfinance ^INDIAVIX (see in_yf_pre2016) or manual NSE download (MI-05).",
        )
    ]


@probe("in_amfi_aum")
def probe_amfi_aum(r: ProbeRunner) -> list[ProbeRow]:
    url = "https://www.amfiindia.com/research-information/aum-data"
    resp = r.http.get(url, max_retries=1)
    r.save_raw("in_amfi_aum", "aum_page.html", resp.content, url=url, http_status=resp.status_code)
    return [
        ProbeRow(
            "in_amfi_aum",
            "monthly scheme-wise AUM",
            "",
            url,
            "scrape",
            "none",
            "PARTIAL" if resp.status_code == 200 else "NOT_FOUND",
            tos_url=AMFI_TOS,
            notes=f"HTTP {resp.status_code}. Page is a JavaScript app; endpoint for scheme-wise monthly AUM to be "
            "located in P05 (used only for the slow-moving flow feature). Not on the critical path.",
        )
    ]

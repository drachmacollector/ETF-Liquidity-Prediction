"""P01 probes for US ETF prices and issuer NAV/shares sources."""

from __future__ import annotations

import io
import json
import os
import re
from html import unescape

import pandas as pd

from esw.ingest import parsers as P
from esw.ingest.candidates import US_CANDIDATES
from esw.ingest.probe import ProbeRow, ProbeRunner, probe

TIINGO_TOS = "https://www.tiingo.com/about/terms"
ISHARES_SCREENER = (
    "https://www.ishares.com/us/product-screener/product-screener-v3.1.jsn?dcrPath=/templatedata/config/"
    "product-screener-v3/data/en/us-ishares/ishares-product-screener-backend-config&siteEntryPassthrough=true"
)
ISHARES_DOWNLOAD = (
    "https://www.blackrock.com/varnish-api/blk-one01-product-data/product-data/api/v1/get-fund-document"
    "?appType=PRODUCT_PAGE&appSubType=ISHARES&targetSite=us-ishares&locale=en_US&portfolioId={pid}"
    "&component=fundDownload&userType=individual"
)
SPDR_GOLD_ARCHIVE = (
    "https://api.spdrgoldshares.com/api/v1/historical-archive?product={p}&exchange=NYSE&lang=en"
)
SSGA_NAVHIST = "https://www.ssga.com/us/en/intermediary/library-content/products/fund-data/etfs/us/navhist-us-en-{t}.xlsx"


def _iid(t: str) -> str:
    return f"US:{t}"


def _tiingo_headers() -> dict:
    key = os.environ.get("TIINGO_API_KEY", "")
    return {"Content-Type": "application/json", "Authorization": f"Token {key}"}


def _previous_rows(r: ProbeRunner, source_id: str) -> dict[str, dict]:
    import csv

    from esw.ingest.probe import matrix_path

    path = matrix_path(r.settings)
    if not path.exists():
        return {}
    with open(path, encoding="utf-8") as fh:
        return {row["instrument_id"]: row for row in csv.DictReader(fh) if row["source_id"] == source_id}


# --------------------------------------------------------------------------- prices
@probe("us_px_tiingo")
def probe_tiingo(r: ProbeRunner) -> list[ProbeRow]:
    rows: list[ProbeRow] = []
    if not os.environ.get("TIINGO_API_KEY"):
        return [
            ProbeRow(
                "us_px_tiingo",
                "all US candidates",
                status="BLOCKED",
                auth="key",
                notes="TIINGO_API_KEY not set",
            )
        ]
    sample = {"GLD", "USO", "LQD", "EGPT", "SPY"}
    # Resume: keep earlier OK rows (the free tier allows ~50 requests/hour) and only re-request the rest.
    previous = _previous_rows(r, "us_px_tiingo")
    for t in US_CANDIDATES:
        if previous.get(_iid(t), {}).get("status") == "OK":
            rows.append(ProbeRow(**{k: v for k, v in previous[_iid(t)].items()}))
            continue
        url = f"https://api.tiingo.com/tiingo/daily/{t.lower()}"
        resp = r.http.get(url, headers=_tiingo_headers())
        if resp.status_code != 200:
            r.log_failure("us_px_tiingo", url, resp.text[:200], resp.status_code)
            rows.append(
                ProbeRow(
                    "us_px_tiingo",
                    "daily EOD",
                    _iid(t),
                    url,
                    "api",
                    "key",
                    "NOT_FOUND",
                    notes=f"HTTP {resp.status_code}",
                )
            )
            continue
        meta = resp.json()
        r.save_raw(
            "us_px_tiingo", f"{t}_meta.json", resp.content, url=url, http_status=200, instrument_id=_iid(t)
        )
        note = f"name={meta.get('name', '')[:60]}"
        if t in sample:
            purl = f"{url}/prices"
            pr = r.http.get(
                purl, params={"startDate": "2020-03-02", "endDate": "2020-05-29"}, headers=_tiingo_headers()
            )
            r.save_raw(
                "us_px_tiingo",
                f"{t}_prices_2020.json",
                pr.content,
                url=purl,
                http_status=pr.status_code,
                instrument_id=_iid(t),
            )
            df = P.parse_tiingo_prices(pr.content)
            note += f"; sample 2020-03..05 rows={len(df)}; split rows={int((df['split_factor'] != 1).sum())}"
            if t == "USO":
                r.save_fixture("us_px_tiingo", "USO_prices_2020.json", pr.content)
        rows.append(
            ProbeRow(
                "us_px_tiingo",
                "daily EOD OHLCV",
                _iid(t),
                "https://api.tiingo.com/tiingo/daily/<ticker>/prices",
                "api",
                "key",
                "OK",
                str(meta.get("startDate", "")),
                str(meta.get("endDate", "")),
                "",
                "open,high,low,close,volume (raw) + adjClose,divCash,splitFactor",
                "n (raw close); adj fields separate",
                "Free tier limits apply (see terms); header Content-Type: application/json required",
                TIINGO_TOS,
                "Personal/research use; no redistribution of raw data",
                note,
            )
        )
    return rows


@probe("us_px_stooq")
def probe_stooq(r: ProbeRunner) -> list[ProbeRow]:
    url = "https://stooq.com/q/d/l/?s=gld.us&i=d"
    resp = r.http.get(url, max_retries=0)
    challenge = b"verify your browser" in resp.content or b"requires JavaScript" in resp.content
    r.save_raw(
        "us_px_stooq",
        "gld.html",
        resp.content,
        url=url,
        http_status=resp.status_code,
        status="failed" if challenge else "ok",
        error="JS challenge" if challenge else None,
    )
    return [
        ProbeRow(
            "us_px_stooq",
            "daily EOD (fallback)",
            "",
            url,
            "file",
            "none",
            "BLOCKED" if challenge else "OK",
            notes="Returns a JavaScript proof-of-work browser check to scripts; not bypassed. Dropped as a fallback."
            if challenge
            else "",
        )
    ]


@probe("us_px_yf")
def probe_yfinance(r: ProbeRunner) -> list[ProbeRow]:
    import yfinance as yf

    rows = []
    for t in ["GLD", "USO", "LQD", "EGPT", "SPY"]:
        df = yf.Ticker(t).history(start="2004-01-01", auto_adjust=False, actions=True)
        note = ""
        if t == "USO" and len(df):
            s = df.loc["2020-04-24":"2020-05-01", "Close"]
            note = f"USO close 2020-04-27={s.iloc[1]:.2f} (split-adjusted; raw was ~2.19)"
        rows.append(
            ProbeRow(
                "us_px_yf",
                "daily EOD (fallback)",
                _iid(t),
                "yfinance Ticker.history(auto_adjust=False)",
                "library",
                "none",
                "OK" if len(df) else "NOT_FOUND",
                str(df.index.min().date()) if len(df) else "",
                str(df.index.max().date()) if len(df) else "",
                len(df),
                "Open,High,Low,Close,Adj Close,Volume,Dividends,Stock Splits",
                "split_only (Close is split-adjusted)",
                "Unofficial Yahoo endpoint; library may change",
                "https://legal.yahoo.com/us/en/yahoo/terms/otos/index.html",
                "Personal use; unofficial access; fallback only",
                note,
            )
        )
    return rows


# --------------------------------------------------------------------------- issuer NAV / shares
@probe("us_iss_spdr_gold")
def probe_spdr_gold(r: ProbeRunner) -> list[ProbeRow]:
    rows = []
    for t in ["GLD", "GLDM"]:
        url = SPDR_GOLD_ARCHIVE.format(p=t.lower())
        resp = r.http.get(url)
        if resp.status_code != 200:
            rows.append(
                ProbeRow(
                    "us_iss_spdr_gold",
                    "NAV history",
                    _iid(t),
                    url,
                    "file",
                    status="NOT_FOUND",
                    notes=f"HTTP {resp.status_code}",
                )
            )
            continue
        r.save_raw(
            "us_iss_spdr_gold",
            f"{t}_archive.xlsx",
            resp.content,
            url=url,
            http_status=200,
            instrument_id=_iid(t),
        )
        df = P.parse_spdr_gold_archive(resp.content)
        a, b, n = P.date_span(df)
        if t == "GLD":
            _fixture_spdr(r, resp.content)
        rows.append(
            ProbeRow(
                "us_iss_spdr_gold",
                "NAV, shares (derived), issuer premium, ounces/share",
                _iid(t),
                SPDR_GOLD_ARCHIVE,
                "file",
                "none",
                "OK",
                a,
                b,
                n,
                "Closing Price, Ounces of Gold per Share, NAV/Share at 10:30am NYT, Indicative Price 4:15pm, "
                "Mid point bid/ask 4:15pm, Premium/Discount (mid vs indicative 4:15pm), Volume, Total Ounces, Tonnes, Total NAV",
                "n",
                "",
                "https://www.spdrgoldshares.com/usa/terms-of-use/",
                "Website terms; research use",
                "Shares outstanding = Total NAV / NAV per share. NAV labelled at 10:30am New York (LBMA PM basis).",
            )
        )
    return rows


def _fixture_spdr(r: ProbeRunner, raw: bytes) -> None:
    xl = pd.ExcelFile(io.BytesIO(raw))
    sheet = next(s for s in xl.sheet_names if "Historical Archive" in s)
    df = pd.read_excel(xl, sheet_name=sheet, nrows=40)
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as w:
        pd.DataFrame({"Disclaimer": ["trimmed fixture"]}).to_excel(w, sheet_name="Disclaimer", index=False)
        df.to_excel(w, sheet_name=sheet, index=False)
    r.save_fixture("us_iss_spdr_gold", "GLD_archive_trimmed.xlsx", buf.getvalue())


@probe("us_iss_ishares")
def probe_ishares(r: ProbeRunner) -> list[ProbeRow]:
    resp = r.http.get(ISHARES_SCREENER)
    r.save_raw(
        "us_iss_ishares",
        "product_screener.json",
        resp.content,
        url=ISHARES_SCREENER,
        http_status=resp.status_code,
    )
    screener = resp.json()
    by_ticker = {v.get("localExchangeTicker"): (pid, v) for pid, v in screener.items()}
    rows = []
    for t, (_, src) in US_CANDIDATES.items():
        if src != "us_iss_ishares":
            continue
        if t not in by_ticker:
            rows.append(
                ProbeRow(
                    "us_iss_ishares",
                    "NAV, shares outstanding",
                    _iid(t),
                    ISHARES_DOWNLOAD,
                    "file",
                    status="NOT_FOUND",
                    notes="Not in current iShares product list (fund liquidated). Wayback captures of the product page "
                    "exist (last 2021) but no archived NAV history file found. Options: CRSP (MI-06) or catalogue-only.",
                )
            )
            continue
        pid, info = by_ticker[t]
        url = ISHARES_DOWNLOAD.format(pid=pid)
        fr = r.http.get(url, timeout=120)
        if fr.status_code != 200:
            rows.append(
                ProbeRow(
                    "us_iss_ishares",
                    "NAV, shares outstanding",
                    _iid(t),
                    url,
                    "file",
                    status="NOT_FOUND",
                    notes=f"HTTP {fr.status_code}",
                )
            )
            continue
        r.save_raw(
            "us_iss_ishares",
            f"{t}_fund_download.xml",
            fr.content,
            url=url,
            http_status=200,
            instrument_id=_iid(t),
        )
        df = P.parse_ishares_fund_download(fr.content)
        a, b, n = P.date_span(df)
        incep = str(info.get("inceptionDate", {}).get("r", ""))
        if t == "SLV":
            _fixture_ishares(r, fr.content)
        rows.append(
            ProbeRow(
                "us_iss_ishares",
                "NAV, shares outstanding, ex-dividends",
                _iid(t),
                "blackrock product-data get-fund-document?portfolioId=<id>&component=fundDownload",
                "file",
                "none",
                "OK",
                a,
                b,
                n,
                "As Of, NAV per Share, Ex-Dividends, Shares Outstanding",
                "split_only (history restated for splits)",
                "",
                "https://www.ishares.com/us/terms-of-use",
                "Website terms; data for internal use",
                f"portfolioId={pid}; inception={incep}; shares_out non-null={int(df['shares_out'].notna().sum())}",
            )
        )
    return rows


def _fixture_ishares(r: ProbeRunner, raw: bytes) -> None:
    text = raw.decode("utf-8", errors="replace")
    m = re.search(r'(<ss:Worksheet ss:Name="Historical">.*?</ss:Worksheet>)', text, flags=re.S)
    assert m
    sheet = m.group(1)
    row_iter = list(re.finditer(r"<ss:Row[^>]*>.*?</ss:Row>", sheet, flags=re.S))
    keep = "".join(x.group(0) for x in row_iter[:45])
    trimmed = (
        '<?xml version="1.0"?>\n<ss:Workbook xmlns:ss="urn:schemas-microsoft-com:office:spreadsheet">\n'
        '<ss:Worksheet ss:Name="Disclaimers"><ss:Table><ss:Row><ss:Cell><ss:Data ss:Type="String">fixture'
        "</ss:Data></ss:Cell></ss:Row></ss:Table></ss:Worksheet>\n"
        f'<ss:Worksheet ss:Name="Historical"><ss:Table>{keep}</ss:Table></ss:Worksheet>\n</ss:Workbook>\n'
    )
    r.save_fixture("us_iss_ishares", "SLV_fund_download_trimmed.xml", trimmed.encode("utf-8"))


@probe("us_iss_ssga")
def probe_ssga(r: ProbeRunner) -> list[ProbeRow]:
    rows = []
    for t, (_, src) in US_CANDIDATES.items():
        if src != "us_iss_ssga":
            continue
        url = SSGA_NAVHIST.format(t=t.lower())
        resp = r.http.get(url)
        if resp.status_code != 200 or not resp.content.startswith(b"PK"):
            rows.append(
                ProbeRow(
                    "us_iss_ssga",
                    "NAV history",
                    _iid(t),
                    SSGA_NAVHIST,
                    "file",
                    status="NOT_FOUND",
                    notes=f"HTTP {resp.status_code}",
                )
            )
            continue
        r.save_raw(
            "us_iss_ssga", f"{t}_navhist.xlsx", resp.content, url=url, http_status=200, instrument_id=_iid(t)
        )
        df = P.parse_ssga_navhist(resp.content)
        a, b, n = P.date_span(df)
        so = df["shares_out"].dropna()
        if t == "JNK":
            _fixture_ssga(r, resp.content)
        rows.append(
            ProbeRow(
                "us_iss_ssga",
                "NAV, shares outstanding, total net assets",
                _iid(t),
                SSGA_NAVHIST,
                "file",
                "none",
                "OK" if a else "PARTIAL",
                a,
                b,
                n,
                "Date, NAV, Shares Outstanding, Total Net Assets",
                "n",
                "",
                "https://www.ssga.com/us/en/intermediary/terms-of-use",
                "Website terms; research use",
                f"shares_out available from {so.index.min() if len(so) else 'n/a'} (row index); first share date "
                f"{df.loc[so.index.min(), 'date'].date() if len(so) else 'n/a'}",
            )
        )
    return rows


def _fixture_ssga(r: ProbeRunner, raw: bytes) -> None:
    x = pd.read_excel(io.BytesIO(raw), header=None, nrows=44)
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as w:
        x.to_excel(w, index=False, header=False)
    r.save_fixture("us_iss_ssga", "JNK_navhist_trimmed.xlsx", buf.getvalue())


@probe("us_iss_uscf")
def probe_uscf(r: ProbeRunner) -> list[ProbeRow]:
    url = "https://www.uscfinvestments.com/uso"
    resp = r.http.get(url)
    r.save_raw("us_iss_uscf", "uso_page.html", resp.content, url=url, http_status=resp.status_code)
    split_note = "reverse share split" in resp.text and "adjusted to reflect" in resp.text
    rows = []
    for t, (_, src) in US_CANDIDATES.items():
        if src == "us_iss_uscf":
            rows.append(
                ProbeRow(
                    "us_iss_uscf",
                    "NAV history (CSV via page button)",
                    _iid(t),
                    f"https://www.uscfinvestments.com/{t.lower()}",
                    "manual",
                    "login",
                    "MANUAL_ONLY",
                    fields="Date, NAV Value (no shares outstanding)",
                    adjusted="split_only" if split_note else "unknown",
                    tos_url="https://www.uscfinvestments.com/terms-of-use",
                    tos_summary="Website terms; research use",
                    notes="'Download Historical NAV Performance' builds a CSV in the browser from an API that requires a "
                    "page-issued bearer token; not scripted (MI-04). Page states NAV and shares history are restated "
                    "for the 1-for-8 reverse split of 28 Apr 2020. Shares outstanding: from SEC filings/other sources.",
                )
            )
    return rows


def _page_probe(
    r: ProbeRunner, source_id: str, url: str, tickers: list[str], tos_url: str, extra: str
) -> list[ProbeRow]:
    try:
        resp = r.http.get(url, max_retries=1)
        code = resp.status_code
        r.save_raw(source_id, "page.html", resp.content, url=url, http_status=code)
        links = sorted(
            set(re.findall(r'href="([^"]*(?:\.csv|\.xlsx?)[^"]*)"', unescape(resp.text), flags=re.I))
        )
    except Exception as exc:  # noqa: BLE001
        code, links = None, []
        r.log_failure(source_id, url, repr(exc))
    note = f"Fund page HTTP {code}; no scriptable NAV-history file link found ({len(links)} csv/xls links). {extra}"
    return [
        ProbeRow(
            source_id,
            "NAV history",
            _iid(t),
            url,
            "manual",
            "none",
            "MANUAL_ONLY",
            tos_url=tos_url,
            tos_summary="Website terms; research use",
            notes=note,
        )
        for t in tickers
    ]


def _tickers(src: str) -> list[str]:
    return [t for t, (_, s) in US_CANDIDATES.items() if s == src]


@probe("us_iss_invesco")
def probe_invesco(r: ProbeRunner) -> list[ProbeRow]:
    return _page_probe(
        r,
        "us_iss_invesco",
        "https://www.invesco.com/us/financial-products/etfs/product-detail?audienceType=Investor&ticker=DBC",
        _tickers("us_iss_invesco"),
        "https://www.invesco.com/corporate/en/terms-of-use.html",
        "Page content is rendered by JavaScript.",
    )


@probe("us_iss_vaneck")
def probe_vaneck(r: ProbeRunner) -> list[ProbeRow]:
    rows = _page_probe(
        r,
        "us_iss_vaneck",
        "https://www.vaneck.com/us/en/investments/egypt-etf-egpt/",
        _tickers("us_iss_vaneck"),
        "https://www.vaneck.com/us/en/terms-of-use/",
        "EGPT (delisted 2024-03-21 per Tiingo) and RSX (liquidated; last price 2023-01-13) pages removed; "
        "Wayback has no archived NAV files. Options: CRSP (MI-06) or catalogue-only.",
    )
    for row in rows:
        row.status = "NOT_FOUND"
    return rows


@probe("us_iss_globalx")
def probe_globalx(r: ProbeRunner) -> list[ProbeRow]:
    return _page_probe(
        r,
        "us_iss_globalx",
        "https://www.globalxetfs.com/funds/grek/",
        ["GREK"],
        "https://www.globalxetfs.com/terms-of-use/",
        "Site answered 429 (rate limited) to a single request.",
    )


@probe("us_iss_xtrackers")
def probe_xtrackers(r: ProbeRunner) -> list[ProbeRow]:
    return _page_probe(
        r,
        "us_iss_xtrackers",
        "https://etf.dws.com/en-us/ASHR-harvest-csi-300-china-a-shares-etf/",
        ["ASHR"],
        "https://etf.dws.com/en-us/terms-of-use/",
        "Page is a JavaScript shell.",
    )


@probe("us_iss_abrdn")
def probe_abrdn(r: ProbeRunner) -> list[ProbeRow]:
    return _page_probe(
        r,
        "us_iss_abrdn",
        "https://www.abrdn.com/en-us/investor/fund-centre/etf/sivr",
        _tickers("us_iss_abrdn"),
        "https://www.abrdn.com/en-us/investor/terms-of-use",
        "Fund page URL changed (404).",
    )


@probe("us_iss_teucrium")
def probe_teucrium(r: ProbeRunner) -> list[ProbeRow]:
    return _page_probe(
        r,
        "us_iss_teucrium",
        "https://teucrium.com/funds/corn",
        _tickers("us_iss_teucrium"),
        "https://teucrium.com/terms-of-use",
        "Fund page URL changed (404).",
    )


@probe("us_iss_vanguard")
def probe_vanguard(r: ProbeRunner) -> list[ProbeRow]:
    return _page_probe(
        r,
        "us_iss_vanguard",
        "https://investor.vanguard.com/investment-products/etfs/profile/bnd",
        _tickers("us_iss_vanguard"),
        "https://investor.vanguard.com/terms-conditions",
        "Page is rendered by JavaScript.",
    )


@probe("us_wayback")
def probe_wayback(r: ProbeRunner) -> list[ProbeRow]:
    url = "https://web.archive.org/cdx/search/cdx"
    found = {}
    for t, q in [
        ("ERUS", "ishares.com/us/products/239677/*"),
        ("RSX", "vaneck.com/us/en/investments/russia-etf-rsx*"),
        ("EGPT", "vaneck.com/us/en/investments/egypt-etf-egpt*"),
    ]:
        resp = r.http.get(
            url,
            params={
                "url": q,
                "output": "json",
                "limit": "2000",
                "collapse": "urlkey",
                "fl": "original,timestamp,mimetype",
            },
            timeout=90,
        )
        r.save_raw(
            "us_wayback",
            f"{t}_cdx.json",
            resp.content,
            url=url,
            http_status=resp.status_code,
            instrument_id=_iid(t),
        )
        try:
            caps = json.loads(resp.content)[1:]
        except ValueError:
            caps = []
        nav_like = [
            c for c in caps if re.search(r"(nav|histor|premium)", c[0], flags=re.I) and "csv" in c[2] + c[0]
        ]
        found[t] = (len(caps), len(nav_like), max((c[1] for c in caps), default=""))
    return [
        ProbeRow(
            "us_wayback",
            "archived NAV history files of delisted funds",
            _iid(t),
            url,
            "api",
            "none",
            "NOT_FOUND" if not v[1] else "PARTIAL",
            rows=v[0],
            notes=f"{v[0]} captures; {v[1]} NAV-history-like files; latest capture {v[2]}",
        )
        for t, v in found.items()
    ]


@probe("us_edgar")
def probe_edgar(r: ProbeRunner) -> list[ProbeRow]:
    url = "https://data.sec.gov/submissions/CIK0001327068.json"
    resp = r.http.get(url)
    r.save_raw(
        "us_edgar",
        "USO_submissions.json",
        resp.content,
        url=url,
        http_status=resp.status_code,
        instrument_id="US:USO",
    )
    ok = resp.status_code == 200
    n = len(resp.json().get("filings", {}).get("recent", {}).get("form", [])) if ok else 0
    return [
        ProbeRow(
            "us_edgar",
            "filing index (8-K, S-3, 10-Q) for capacity/operational events",
            "US:USO",
            url,
            "api",
            "none",
            "OK" if ok else "BLOCKED",
            rows=n,
            fields="form, filingDate, acceptanceDateTime, accessionNumber",
            rate_limit_note="SEC fair access: <= 10 requests/second; declare a user agent",
            tos_url="https://www.sec.gov/os/accessing-edgar-data",
            tos_summary="Public data; automated access allowed within fair-access limits",
            notes="Accepted the generic project user agent (D-004: no personal email). acceptanceDateTime gives known_at.",
        )
    ]

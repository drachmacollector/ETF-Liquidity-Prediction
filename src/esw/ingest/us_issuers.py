"""P04 T04.3: US issuer NAV / shares adapters -> `data/staged/us_nav/<source_id>.parquet`.

| source | instruments | method | history |
|---|---|---|---|
| us_iss_spdr_gold | GLD, GLDM | issuer archive XLSX | since inception; NAV, ounces/share, shares, issuer premium (4:15pm) |
| us_iss_ishares | iShares funds | BlackRock fund-download XML | since inception; NAV and daily shares (split-adjusted) |
| us_iss_ssga | SPY, DIA, JNK | SSGA NAV-history XLSX | from 2003/2007; NAV, shares, TNA |
| us_iss_uscf | USCF funds | ALPS marketing API with the token the fund page issues (D-010) | NAV from 2009 (not split-adjusted, D-014) |
| us_iss_invesco | DBC, DBA, DBO, BKLN, QQQ | Invesco dng-api (curl client; the site rejects Python TLS) | NAV and TNA from 2016-09 |
| us_iss_globalx | GREK | manual drop (MI-04) premium/discount file | from 2015-04; NAV = close - premium |

Staged columns: ticker, instrument_id, date, nav, shares_out, total_net_assets, issuer_close,
issuer_mid, issuer_prem_bps, oz_per_share, extra_json, source_id, raw_path, ingested_at.
"""

from __future__ import annotations

import json
import re
import subprocess

import pandas as pd

from esw.config import Settings, get_settings
from esw.ingest import parsers as P
from esw.ingest.base import Fetcher, FetchTask, stage
from esw.ingest.http import BROWSER_HEADERS, PoliteSession

SPDR_GOLD_ARCHIVE = (
    "https://api.spdrgoldshares.com/api/v1/historical-archive?product={p}&exchange=NYSE&lang=en"
)
ISHARES_DOWNLOAD = (
    "https://www.blackrock.com/varnish-api/blk-one01-product-data/product-data/api/v1/get-fund-document"
    "?appType=PRODUCT_PAGE&appSubType=ISHARES&targetSite=us-ishares&locale=en_US&portfolioId={pid}"
    "&component=fundDownload&userType=individual"
)
SSGA_NAVHIST = "https://www.ssga.com/us/en/intermediary/library-content/products/fund-data/etfs/us/navhist-us-en-{t}.xlsx"
USCF_PAGE = "https://www.uscfinvestments.com/{t}"
USCF_KEY = "https://www.uscfinvestments.com/site-template/assets/javascript/api_key.php"
USCF_NAV = "https://secure.alpsinc.com/MarketingAPI/api/v1/historicalnav/{T}/inception-today"
INVESCO_NAVS = (
    "https://dng-api.invesco.com/cache/v1/accounts/en_US/shareclasses/{T}/navs?idType=ticker&productType=ETF"
)

COLS = [
    "ticker", "instrument_id", "date", "nav", "shares_out", "total_net_assets", "issuer_close", "issuer_mid",
    "issuer_prem_bps", "oz_per_share", "extra_json", "source_id", "raw_path", "ingested_at",
]  # fmt: skip


def _raw(settings: Settings, source: str, name: str):
    return settings.path("raw") / source / name


# ----------------------------------------------------------------------------- fetchers
def fetch_spdr_gold(tickers, settings, fetcher: Fetcher, refresh=False):
    s = PoliteSession(settings)
    return {
        t: fetcher.run(
            FetchTask(
                "us_iss_spdr_gold",
                f"US:{t}",
                SPDR_GOLD_ARCHIVE.format(p=t.lower()),
                _raw(settings, "us_iss_spdr_gold", f"{t}_archive.xlsx"),
            ),
            lambda u, params=None, headers=None: s.get(u),
            refresh,
            validate=lambda b: b[:2] == b"PK",
        ).status
        for t in tickers
    }


def ishares_portfolio_ids(settings: Settings) -> dict[str, str]:
    d = json.loads(
        (settings.path("raw") / "_probes" / "us_iss_ishares" / "product_screener.json").read_text(
            encoding="utf-8"
        )
    )
    return {
        v["localExchangeTicker"]: str(v["portfolioId"]) for v in d.values() if v.get("localExchangeTicker")
    }


def fetch_ishares(tickers, settings, fetcher: Fetcher, refresh=False):
    s = PoliteSession(settings)
    pids = ishares_portfolio_ids(settings)
    out = {}
    for t in tickers:
        if t not in pids:
            out[t] = "failed"
            continue
        task = FetchTask(
            "us_iss_ishares",
            f"US:{t}",
            ISHARES_DOWNLOAD.format(pid=pids[t]),
            _raw(settings, "us_iss_ishares", f"{t}_fund_download.xml"),
        )
        out[t] = fetcher.run(
            task,
            lambda u, params=None, headers=None: s.get(u, timeout=180),
            refresh,
            validate=lambda b: b"<?xml" in b[:200] or b"Workbook" in b[:2000],
        ).status
    return out


def fetch_ssga(tickers, settings, fetcher: Fetcher, refresh=False):
    s = PoliteSession(settings)
    return {
        t: fetcher.run(
            FetchTask(
                "us_iss_ssga",
                f"US:{t}",
                SSGA_NAVHIST.format(t=t.lower()),
                _raw(settings, "us_iss_ssga", f"{t}_navhist.xlsx"),
            ),
            lambda u, params=None, headers=None: s.get(u),
            refresh,
            validate=lambda b: b[:2] == b"PK",
        ).status
        for t in tickers
    }


def _uscf_token(s: PoliteSession, ticker: str) -> str:
    s.get(USCF_PAGE.format(t=ticker.lower()), max_retries=1)
    text = s.get(USCF_KEY, max_retries=1, headers={"Referer": USCF_PAGE.format(t=ticker.lower())}).text
    m = re.search(r"token\s*=\s*'([^']+)'", text)
    if not m:
        raise RuntimeError("USCF page did not issue an API token")
    return m.group(1)


def fetch_uscf(tickers, settings, fetcher: Fetcher, refresh=False):
    s = PoliteSession(settings, browser=True)
    token = None
    out = {}
    for t in tickers:
        task = FetchTask(
            "us_iss_uscf",
            f"US:{t}",
            USCF_NAV.format(T=t.upper()),
            _raw(settings, "us_iss_uscf", f"{t}_historicalnav_api.json"),
        )
        if not task.path.exists() or refresh:
            token = token or _uscf_token(s, t)
        hdr = (
            {
                "Authorization": f"Bearer {token}",
                "Accept": "application/json",
                "Referer": USCF_PAGE.format(t=t.lower()),
            }
            if token
            else None
        )
        out[t] = fetcher.run(
            task,
            lambda u, params=None, headers=None, h=hdr: s.get(u, headers=h),
            refresh,
            validate=lambda b: b[:2] == b"[{",
        ).status
    return out


class _CurlResp:
    def __init__(self, code: int, content: bytes):
        self.status_code, self.content = code, content


def _curl_get(url: str) -> _CurlResp:
    """Plain curl GET (Invesco's CDN rejects Python's TLS fingerprint but accepts curl)."""
    cmd = [
        "curl",
        "-s",
        "--compressed",
        "-A",
        BROWSER_HEADERS["User-Agent"],
        "-H",
        "Referer: https://www.invesco.com/",
        "-w",
        "\n%{http_code}",
        url,
    ]
    res = subprocess.run(cmd, capture_output=True, timeout=180, check=False)
    body, _, code = res.stdout.rpartition(b"\n")
    return _CurlResp(int(code or 0), body)


def fetch_invesco(tickers, settings, fetcher: Fetcher, refresh=False):
    import time

    out = {}
    for t in tickers:
        task = FetchTask(
            "us_iss_invesco",
            f"US:{t}",
            INVESCO_NAVS.format(T=t.upper()),
            _raw(settings, "us_iss_invesco", f"{t}_navs.json"),
        )

        def get(u, params=None, headers=None):
            time.sleep(1.0)
            return _curl_get(u)

        out[t] = fetcher.run(task, get, refresh, validate=lambda b: b.lstrip()[:1] == b"[").status
    return out


# ----------------------------------------------------------------------------- parsers to staged rows
def parse_uscf_api(raw: bytes, ticker: str) -> pd.DataFrame:
    d = json.loads(raw)[0][ticker.upper()]
    df = pd.DataFrame(d)
    return pd.DataFrame(
        {"date": pd.to_datetime(df["date"].str[:10]), "nav": pd.to_numeric(df["value"], errors="coerce")}
    )


def parse_invesco_navs(raw: bytes) -> pd.DataFrame:
    df = pd.DataFrame(json.loads(raw))
    out = pd.DataFrame(
        {
            "date": pd.to_datetime(df["effectiveDate"]),
            "nav": pd.to_numeric(df["netAssetValue"], errors="coerce"),
            "total_net_assets": pd.to_numeric(df["totalNetAssets"], errors="coerce"),
            "issuer_close": pd.to_numeric(df["closingPrice"], errors="coerce"),
            "issuer_mid": pd.to_numeric(df["bidAskMidpoint"], errors="coerce"),
            "issuer_prem_bps": pd.to_numeric(df["bidAskMidpointPremiumDiscountPercentage"], errors="coerce")
            * 100,
        }
    )
    out["shares_out"] = (out["total_net_assets"] / out["nav"]).round()
    return out


def _std(df: pd.DataFrame, t: str, source_id: str, raw_path: str, now) -> pd.DataFrame:
    df = df.copy()
    df["ticker"], df["instrument_id"], df["source_id"], df["raw_path"], df["ingested_at"] = (
        t,
        f"US:{t}",
        source_id,
        raw_path,
        now,
    )
    if "issuer_prem_pct" in df.columns:
        df["issuer_prem_bps"] = df["issuer_prem_pct"] * 100
    out = df.reindex(columns=COLS)
    out = out.dropna(subset=["nav"])
    dup = out.duplicated(subset=["date"], keep="last")
    return out[~dup]


def stage_nav(settings: Settings | None = None) -> dict[str, int]:
    settings = settings or get_settings()
    raw, root = settings.path("raw"), settings.root
    now = pd.Timestamp.now(tz="UTC").floor("s")
    spec = {
        "us_iss_spdr_gold": ("*_archive.xlsx", lambda b, t: P.parse_spdr_gold_archive(b)),
        "us_iss_ishares": ("*_fund_download.xml", lambda b, t: P.parse_ishares_fund_download(b)),
        "us_iss_ssga": ("*_navhist.xlsx", lambda b, t: P.parse_ssga_navhist(b)),
        "us_iss_uscf": ("*_historicalnav_api.json", parse_uscf_api),
        "us_iss_invesco": ("*_navs.json", lambda b, t: parse_invesco_navs(b)),
    }
    counts = {}
    for source_id, (pattern, parser) in spec.items():
        frames = []
        for p in sorted((raw / source_id).glob(pattern)):
            t = p.name.split("_")[0]
            df = parser(p.read_bytes(), t)
            frames.append(_std(df, t, source_id, p.relative_to(root).as_posix(), now))
        if frames:
            counts[source_id] = len(all_ := pd.concat(frames, ignore_index=True))
            stage(all_, "us_nav", source_id, settings)
    # manual drops (MI-04)
    manual = []
    for p in sorted((settings.path("manual_drop") / "us_iss_globalx").glob("*premium-discount*.csv")):
        t = p.name.split("-")[0].upper()
        manual.append(
            _std(
                P.parse_globalx_premium_discount(p.read_bytes()).rename(columns={"close": "issuer_close"}),
                t,
                "us_iss_globalx",
                p.relative_to(root).as_posix(),
                now,
            )
        )
    for p in sorted((settings.path("manual_drop") / "us_iss_uscf").glob("*-historicalnav-*.csv")):
        t = p.name.split("-")[0].upper()
        manual.append(
            _std(
                P.parse_uscf_navhist(p.read_bytes()),
                t,
                "us_iss_uscf_manual",
                p.relative_to(root).as_posix(),
                now,
            )
        )
    if manual:
        m = pd.concat(manual, ignore_index=True)
        for sid, g in m.groupby("source_id"):
            stage(g, "us_nav", sid, settings)
            counts[sid] = len(g)
    return counts

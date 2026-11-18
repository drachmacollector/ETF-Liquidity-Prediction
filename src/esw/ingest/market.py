"""P06: underlying, market-wide and FX series -> `data/staged/series/<series_id>.parquet`.

Adapters by source: FRED CSV (no key), EIA futures XLS, yfinance (continuous futures, single
contracts, FX, indices) and `derived` (GLD NAV / ounces per share). Raw files are written once under
`data/raw/<source_id>/` and logged. `SERIES` below is the acquisition list; the catalogue
(`reference/series_catalogue.csv`) records lags and time zones.

Continuous futures (`=F`) jump at rolls. `flag_rolls()` marks days whose log return is far outside the
recent distribution *and* falls in the vendor's usual roll window; their returns are set to null in the
derived `<series>_ret` column. Downstream features use those returns, never level differences.
"""

from __future__ import annotations

import time

import numpy as np
import pandas as pd

from esw.config import Settings, get_settings
from esw.ingest import parsers as P
from esw.ingest.base import Fetcher, FetchTask, stage
from esw.ingest.http import PoliteSession

FRED = "https://fred.stlouisfed.org/graph/fredgraph.csv?id={code}"
EIA = "https://www.eia.gov/dnav/pet/hist_xls/{code}d.xls"
EIA_NG = "https://www.eia.gov/dnav/ng/hist_xls/{code}d.xls"

# series_id -> (source, code, unit, tz, lag, description)
SERIES: dict[str, tuple[str, str, str, str, int, str]] = {
    # volatility, credit, rates, dollar (FRED)
    "vix": ("mkt_fred", "VIXCLS", "index", "America/New_York", 0, "CBOE VIX close"),
    "ovx": ("mkt_fred", "OVXCLS", "index", "America/New_York", 0, "CBOE crude oil volatility index"),
    "gvz": ("mkt_fred", "GVZCLS", "index", "America/New_York", 0, "CBOE gold volatility index"),
    "baa10y": ("mkt_fred", "BAA10Y", "percent", "America/New_York", 1, "Moody's Baa minus 10y Treasury"),
    "aaa10y": ("mkt_fred", "AAA10Y", "percent", "America/New_York", 1, "Moody's Aaa minus 10y Treasury"),
    "ust10y": ("mkt_fred", "DGS10", "percent", "America/New_York", 1, "10y Treasury CMT"),
    "ust2y": ("mkt_fred", "DGS2", "percent", "America/New_York", 1, "2y Treasury CMT"),
    "tedrate": ("mkt_fred", "TEDRATE", "percent", "America/New_York", 1, "TED spread (discontinued 2022)"),
    "usd_broad": (
        "mkt_fred",
        "DTWEXBGS",
        "index",
        "America/New_York",
        1,
        "Nominal broad dollar index (2006+)",
    ),
    "usd_major_old": (
        "mkt_fred",
        "DTWEXM",
        "index",
        "America/New_York",
        1,
        "Major-currencies dollar index (to 2019)",
    ),
    # FX (FRED H.10 noon NY)
    "usdinr": ("mkt_fred", "DEXINUS", "INR/USD", "America/New_York", 1, "INR per USD"),
    "usdjpy": ("mkt_fred", "DEXJPUS", "JPY/USD", "America/New_York", 1, "JPY per USD"),
    "usdhkd": ("mkt_fred", "DEXHKUS", "HKD/USD", "America/New_York", 1, "HKD per USD"),
    "usdcny": ("mkt_fred", "DEXCHUS", "CNY/USD", "America/New_York", 1, "CNY per USD"),
    "usdmxn": ("mkt_fred", "DEXMXUS", "MXN/USD", "America/New_York", 1, "MXN per USD"),
    "usdbrl": ("mkt_fred", "DEXBZUS", "BRL/USD", "America/New_York", 1, "BRL per USD"),
    "eurusd": ("mkt_fred", "DEXUSEU", "USD/EUR", "America/New_York", 1, "USD per EUR"),
    # FX not on FRED daily (yfinance)
    "usdtry": ("mkt_yf", "TRY=X", "TRY/USD", "Europe/London", 0, "TRY per USD"),
    "usdrub": ("mkt_yf", "RUB=X", "RUB/USD", "Europe/London", 0, "RUB per USD"),
    "usdegp": ("mkt_yf", "EGP=X", "EGP/USD", "Europe/London", 0, "EGP per USD"),
    "usdinr_yf": ("mkt_yf", "INR=X", "INR/USD", "Europe/London", 0, "INR per USD (yfinance, London close)"),
    # metals and energy continuous futures
    "gold_usd_fut": ("mkt_yf", "GC=F", "USD/oz", "America/New_York", 0, "COMEX gold front continuous"),
    "silver_usd_fut": ("mkt_yf", "SI=F", "USD/oz", "America/New_York", 0, "COMEX silver front continuous"),
    "platinum_usd_fut": (
        "mkt_yf",
        "PL=F",
        "USD/oz",
        "America/New_York",
        0,
        "NYMEX platinum front continuous",
    ),
    "palladium_usd_fut": (
        "mkt_yf",
        "PA=F",
        "USD/oz",
        "America/New_York",
        0,
        "NYMEX palladium front continuous",
    ),
    "copper_usd_fut": ("mkt_yf", "HG=F", "USD/lb", "America/New_York", 0, "COMEX copper front continuous"),
    "wti_fut": ("mkt_yf", "CL=F", "USD/bbl", "America/New_York", 0, "NYMEX WTI front continuous"),
    "brent_fut": ("mkt_yf", "BZ=F", "USD/bbl", "America/New_York", 0, "ICE Brent front continuous"),
    "hh_fut": ("mkt_yf", "NG=F", "USD/MMBtu", "America/New_York", 0, "NYMEX natural gas front continuous"),
    "rbob_fut": ("mkt_yf", "RB=F", "USD/gal", "America/New_York", 0, "NYMEX RBOB front continuous"),
    # EIA curves (to 2024-04-05)
    **{
        f"wti_c{i}": (
            "mkt_eia",
            f"RCLC{i}",
            "USD/bbl",
            "America/New_York",
            1,
            f"NYMEX WTI contract {i} (EIA)",
        )
        for i in range(1, 5)
    },
    **{
        f"hh_c{i}": (
            "mkt_eia",
            f"RNGC{i}",
            "USD/MMBtu",
            "America/New_York",
            1,
            f"NYMEX natural gas contract {i} (EIA)",
        )
        for i in range(1, 5)
    },
    # equity indices (closure detection, market stress)
    "idx_spx": ("mkt_yf", "^GSPC", "index", "America/New_York", 0, "S&P 500"),
    "idx_ndx": ("mkt_yf", "^NDX", "index", "America/New_York", 0, "Nasdaq-100"),
    "idx_nyfang": ("mkt_yf", "^NYFANG", "index", "America/New_York", 0, "NYSE FANG+"),
    "idx_n225": ("mkt_yf", "^N225", "index", "Asia/Tokyo", 0, "Nikkei 225"),
    "idx_hsi": ("mkt_yf", "^HSI", "index", "Asia/Hong_Kong", 0, "Hang Seng"),
    "idx_bvsp": ("mkt_yf", "^BVSP", "index", "America/Sao_Paulo", 0, "Bovespa"),
    "idx_mxx": ("mkt_yf", "^MXX", "index", "America/Mexico_City", 0, "Mexico IPC"),
    "idx_xu100": ("mkt_yf", "XU100.IS", "index", "Europe/Istanbul", 0, "BIST 100"),
    "idx_athex": ("mkt_yf", "GD.AT", "index", "Europe/Athens", 0, "Athens General Composite"),
    "idx_nifty50": ("mkt_yf", "^NSEI", "index", "Asia/Kolkata", 0, "Nifty 50"),
}

# foreign market -> (calendar code, index series) for closure diagnostics (T06.3)
MARKET_OPEN = {
    "XTKS": ("XTKS", "idx_n225"),
    "XHKG": ("XHKG", "idx_hsi"),
    "BVMF": ("BVMF", "idx_bvsp"),
    "XMEX": ("XMEX", "idx_mxx"),
    "XIST": ("XIST", "idx_xu100"),
    "XATH": ("XATH", "idx_athex"),
    "XNSE": ("XNSE", "idx_nifty50"),
    "XNYS": ("XNYS", "idx_spx"),
}


def _fetch_one(
    sid: str, spec, settings: Settings, fetcher: Fetcher, sess: PoliteSession, refresh: bool
) -> str:
    source, code, *_ = spec
    if source == "mkt_fred":
        path = settings.path("raw") / "mkt_fred" / f"{code}.csv"
        task = FetchTask(source, f"SERIES:{sid}", FRED.format(code=code), path)
        return fetcher.run(
            task,
            lambda u, params=None, headers=None: sess.get(u),
            refresh,
            validate=lambda b: b"," in b[:200],
        ).status
    if source == "mkt_eia":
        url = (EIA_NG if code.startswith("RNG") else EIA).format(code=code)
        path = settings.path("raw") / "mkt_eia" / f"{code}.xls"
        task = FetchTask(source, f"SERIES:{sid}", url, path)
        return fetcher.run(
            task, lambda u, params=None, headers=None: sess.get(u), refresh, validate=lambda b: len(b) > 1000
        ).status
    if source == "mkt_yf":
        import yfinance as yf

        path = settings.path("raw") / "mkt_yf" / f"{code.replace('^', '').replace('=', '_')}.csv"
        task = FetchTask(source, f"SERIES:{sid}", f"yfinance:{code}", path)
        if path.exists() and not refresh:
            fetcher.log(task, "skipped_cached")
            return "skipped_cached"
        try:
            h = yf.Ticker(code).history(period="max", auto_adjust=False)
            if h.empty:
                raise ValueError("empty history")
            path.parent.mkdir(parents=True, exist_ok=True)
            h.to_csv(path)
            fetcher.log(task, "ok", rows=len(h))
            time.sleep(0.4)
            return "ok"
        except Exception as exc:  # noqa: BLE001
            fetcher.log(task, "failed", error=str(exc)[:200])
            return "failed"
    raise ValueError(source)


def fetch_series(
    series: list[str] | None = None, settings: Settings | None = None, run_id: str = "", refresh: bool = False
) -> dict:
    settings = settings or get_settings()
    fetcher = Fetcher(settings, run_id)
    sess = PoliteSession(
        settings
    )  # FRED/EIA answer the declared project agent; FRED stalls on browser agents
    return {
        sid: _fetch_one(sid, SERIES[sid], settings, fetcher, sess, refresh)
        for sid in (series or list(SERIES))
    }


def _parse(sid: str, settings: Settings) -> pd.DataFrame | None:
    source, code, unit, *_ = SERIES[sid]
    raw = settings.path("raw")
    if source == "mkt_fred":
        p = raw / "mkt_fred" / f"{code}.csv"
        df = P.parse_fred_csv(p.read_bytes()) if p.exists() else None
    elif source == "mkt_eia":
        p = raw / "mkt_eia" / f"{code}.xls"
        df = P.parse_eia_xls(p.read_bytes()) if p.exists() else None
    else:
        p = raw / "mkt_yf" / f"{code.replace('^', '').replace('=', '_')}.csv"
        if not p.exists():
            return None
        h = pd.read_csv(p)
        df = pd.DataFrame({"date": pd.to_datetime(h["Date"].str[:10]), "value": h["Close"]})
    if df is None:
        return None
    df = df.dropna(subset=["value"])
    df = df[df["value"] != 0] if source == "mkt_yf" else df
    df["series_id"], df["unit"], df["source_id"] = sid, unit, source
    df["raw_path"] = p.relative_to(settings.root).as_posix()
    return df[["series_id", "date", "value", "unit", "source_id", "raw_path"]].drop_duplicates(
        "date", keep="last"
    )


def flag_rolls(df: pd.DataFrame, z: float = 6.0, window: int = 60) -> pd.DataFrame:
    """Add `ret` (log return) and `roll_flag`; flagged returns are set to null.

    A day is flagged when |ret| exceeds `z` robust standard deviations (MAD over the trailing window,
    known only up to the previous day) — continuous front-month series jump at contract rolls.
    """
    df = df.sort_values("date").copy()
    ret = np.log(df["value"].where(df["value"] > 0)).diff()
    med = ret.rolling(window, min_periods=20).median().shift()
    mad = (ret - med).abs().rolling(window, min_periods=20).median().shift() * 1.4826
    df["roll_flag"] = ((ret - med).abs() > z * mad) & mad.gt(0)
    df["ret"] = ret.where(~df["roll_flag"])
    return df


def nav_implied_gold(settings: Settings) -> pd.DataFrame | None:
    p = settings.path("staged") / "us_nav" / "us_iss_spdr_gold.parquet"
    if not p.exists():
        return None
    g = pd.read_parquet(p)
    g = g[(g["ticker"] == "GLD") & g["oz_per_share"].gt(0)]
    out = pd.DataFrame(
        {
            "series_id": "gold_usd_navimpl",
            "date": g["date"],
            "value": g["nav"] / g["oz_per_share"],
            "unit": "USD/oz",
            "source_id": "derived",
            "raw_path": g["raw_path"],
        }
    )
    return out


def stage_series(settings: Settings | None = None) -> dict[str, int]:
    settings = settings or get_settings()
    now = pd.Timestamp.now(tz="UTC").floor("s")
    counts = {}
    frames = {sid: _parse(sid, settings) for sid in SERIES}
    frames["gold_usd_navimpl"] = nav_implied_gold(settings)
    # Single-contract curves after the EIA series end (2024-04-05) are NOT built: yfinance drops expired
    # contracts, so only still-live contracts exist and they are not the front month in the past (D-017).
    for sid, df in frames.items():
        if df is None or df.empty:
            continue
        if sid.endswith("_fut"):
            df = flag_rolls(df)
        df["ingested_at"] = now
        stage(df, "series", sid, settings)
        counts[sid] = len(df)
    return counts


def stage_market_open(settings: Settings | None = None) -> dict[str, int]:
    """Scheduled (calendar) vs observed (index printed a new value) open days per foreign market."""
    from esw.reference.calendars import load_calendar

    settings = settings or get_settings()
    cal = load_calendar(settings)
    out = {}
    for mkt, (code, sid) in MARKET_OPEN.items():
        p = settings.path("staged") / "series" / f"{sid}.parquet"
        if not p.exists():
            continue
        s = pd.read_parquet(p)
        s = s.sort_values("date")
        new_val = s["value"].ne(s["value"].shift())
        observed = set(s.loc[new_val, "date"])
        c = cal[cal["market"] == code][["date", "is_trading"]].rename(
            columns={"is_trading": "scheduled_open"}
        )
        c = c[(c["date"] >= s["date"].min()) & (c["date"] <= s["date"].max())].copy()
        c["observed_open"] = c["date"].isin(observed)
        c["market"] = mkt
        stage(c, "market_open", mkt, settings)
        out[mkt] = int((c["scheduled_open"] & ~c["observed_open"]).sum())
    return out


def series_coverage(settings: Settings | None = None) -> pd.DataFrame:
    settings = settings or get_settings()
    rows = []
    for p in sorted((settings.path("staged") / "series").glob("*.parquet")):
        s = pd.read_parquet(p).sort_values("date")
        bd = pd.bdate_range(s["date"].min(), s["date"].max())
        have = set(s["date"])
        gaps, cur = 0, 0
        for d in bd:
            cur = 0 if d in have else cur + 1
            gaps += cur == 6  # count runs reaching > 5 business days
        rows.append(
            {
                "series_id": p.stem,
                "first": s["date"].min().date(),
                "last": s["date"].max().date(),
                "obs": len(s),
                "gaps_gt5bd": gaps,
                "unit": s["unit"].iloc[0],
                "source_id": s["source_id"].iloc[0],
                "roll_flags": int(s["roll_flag"].sum()) if "roll_flag" in s else None,
            }
        )
    return pd.DataFrame(rows)


MONTH_CODES = "FGHJKMNQUVXZ"


def _last_trade(root: str, year: int, month: int) -> pd.Timestamp:
    """Approximate last trading day (business days; exchange holidays ignored).

    CL: 3 business days before the 25th of the month before delivery (4 if the 25th is not a business day).
    NG: 3 business days before the first calendar day of the delivery month.
    """
    if root == "CL":
        prev = pd.Timestamp(year, month, 1) - pd.offsets.MonthBegin(1)
        d25 = pd.Timestamp(prev.year, prev.month, 25)
        n = 3 if d25.dayofweek < 5 else 4
        return d25 - pd.offsets.BDay(n)
    return pd.Timestamp(year, month, 1) - pd.offsets.BDay(3)


def fetch_contracts(
    root: str,
    start: str = "2024-01",
    end: str = "2027-12",
    settings: Settings | None = None,
    run_id: str = "",
) -> dict:
    """Single NYMEX contracts from yfinance (e.g. CLZ26.NYM) to continue the curve after EIA stops."""
    import yfinance as yf

    settings = settings or get_settings()
    fetcher = Fetcher(settings, run_id)
    out = {}
    for m in pd.period_range(start, end, freq="M"):
        tk = f"{root}{MONTH_CODES[m.month - 1]}{m.year % 100:02d}.NYM"
        path = settings.path("raw") / "mkt_yf" / "contracts" / f"{tk}.csv"
        task = FetchTask("mkt_yf", f"SERIES:{root}", f"yfinance:{tk}", path)
        if path.exists():
            out[tk] = "skipped_cached"
            continue
        try:
            h = yf.Ticker(tk).history(period="max", auto_adjust=False)
            if h.empty:
                raise ValueError("empty")
            path.parent.mkdir(parents=True, exist_ok=True)
            h.to_csv(path)
            fetcher.log(task, "ok", rows=len(h))
            out[tk] = "ok"
        except Exception as exc:  # noqa: BLE001
            fetcher.log(task, "failed", error=str(exc)[:200])
            out[tk] = "failed"
        time.sleep(0.4)
    return out


def contract_curve(root: str, settings: Settings | None = None, n: int = 2) -> pd.DataFrame:
    """Rank live contracts by expiry each day: c1 = nearest unexpired, c2 = next."""
    settings = settings or get_settings()
    rows = []
    for p in sorted((settings.path("raw") / "mkt_yf" / "contracts").glob(f"{root}*.NYM.csv")):
        code = p.name[len(root)]
        yy = int(p.name[len(root) + 1 : len(root) + 3])
        month = MONTH_CODES.index(code) + 1
        expiry = _last_trade(root, 2000 + yy, month)
        h = pd.read_csv(p)
        d = pd.DataFrame(
            {
                "date": pd.to_datetime(h["Date"].str[:10]),
                "value": h["Close"],
                "expiry": expiry,
                "contract": p.stem,
            }
        )
        rows.append(d[d["date"] <= expiry])
    if not rows:
        return pd.DataFrame()
    allc = pd.concat(rows).sort_values(["date", "expiry"])
    allc["rank"] = allc.groupby("date").cumcount() + 1
    sid = {"CL": "wti", "NG": "hh"}[root]
    out = allc[allc["rank"] <= n].copy()
    out["series_id"] = sid + "_ct" + out["rank"].astype(str)
    out["unit"] = "USD/bbl" if root == "CL" else "USD/MMBtu"
    out["source_id"] = "mkt_yf"
    out["raw_path"] = "data/raw/mkt_yf/contracts/" + out["contract"] + ".csv"
    return out[["series_id", "date", "value", "unit", "source_id", "raw_path", "contract", "expiry"]]

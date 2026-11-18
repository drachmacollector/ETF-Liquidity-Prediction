"""P05: Indian ETF data -> `data/staged/in_*`.

* Bhavcopies (`esw.ingest.nse_bhav.BhavStore`, 2007+): `stage_bhav()` keeps rows whose ISIN or (pre-2011,
  ISIN-less) symbol maps to an instrument lineage in `symbol_history`, plus a per-day row count for
  the bhavcopy-derived calendar.
* NAV: AMFI `nav-history` API in <= 5-year windows (gives the **upload timestamp** used as `known_at`,
  D-008), mfapi.in full history as fallback and cross-check.
* Domestic spot: MCX polled spot (MI-05 manual file).
* India VIX: yfinance `^INDIAVIX`.
"""

from __future__ import annotations

import datetime as dt
import json

import pandas as pd

from esw.config import Settings, get_settings
from esw.ingest import parsers as P
from esw.ingest.base import Fetcher, FetchTask, stage
from esw.ingest.http import PoliteSession
from esw.reference import load

AMFI_API = "https://www.amfiindia.com/api/nav-history"
MFAPI = "https://api.mfapi.in/mf/{code}"


# ----------------------------------------------------------------------------- bhavcopy staging
def stage_bhav(settings: Settings | None = None) -> tuple[pd.DataFrame, pd.DataFrame]:
    settings = settings or get_settings()
    sh = load("symbol_history", settings)
    nse = sh[(sh["exchange"] == "NSE") & sh["instrument_id"].str.startswith("IN:")].copy()
    isin_map = (
        nse.dropna(subset=["isin"]).drop_duplicates("isin").set_index("isin")["instrument_id"].to_dict()
    )
    sym = nse.assign(
        vf=nse["valid_from"].fillna(pd.Timestamp("1900-01-01")),
        vt=nse["valid_to"].fillna(pd.Timestamp("2100-01-01")),
    )
    rows, summary = [], []
    root = settings.root
    for p in sorted((settings.path("raw") / "in_bhav").rglob("*.zip")):
        df = P.parse_nse_bhavcopy(p.read_bytes())
        if df.empty:
            continue
        d = df["date"].iloc[0]
        summary.append(
            {
                "date": d,
                "rows": len(df),
                "schema": df["source_schema"].iloc[0],
                "raw_path": p.relative_to(root).as_posix(),
            }
        )
        hit = df[df["isin"].isin(isin_map)].copy()
        hit["instrument_id"] = hit["isin"].map(isin_map)
        hit["mapped_by"] = "isin"
        if df["isin"].isna().all():  # early legacy files: map by symbol valid on that date
            s = sym[(sym["vf"] <= d) & (sym["vt"] >= d)]
            m = df.merge(s[["symbol", "instrument_id"]], on="symbol", how="inner")
            m["mapped_by"] = "symbol"
            hit = m
        hit["raw_path"] = p.relative_to(root).as_posix()
        rows.append(hit)
    px = pd.concat(rows, ignore_index=True)
    px = px[px["series"].isin(["EQ", "BE"]) | px["series"].isna()]
    px = px.sort_values(["instrument_id", "date", "series"]).drop_duplicates(
        ["instrument_id", "date"], keep="first"
    )
    px["source_id"] = "in_bhav_nse"
    px["ingested_at"] = pd.Timestamp.now(tz="UTC").floor("s")
    stage(px, "in_bhav", "in_bhav_nse", settings)
    summ = pd.DataFrame(summary).sort_values("date")
    stage(summ, "in_bhav", "bhav_day_summary", settings)
    return px, summ


# ----------------------------------------------------------------------------- NAV
def _windows(start: dt.date, end: dt.date, years: int = 4) -> list[tuple[dt.date, dt.date]]:
    out, a = [], start
    while a <= end:
        b = min(dt.date(a.year + years, a.month, 1) - dt.timedelta(days=1), end)
        out.append((a, b))
        a = b + dt.timedelta(days=1)
    return out


def fetch_amfi_nav(
    codes: dict[int, str],
    settings: Settings | None = None,
    run_id: str = "",
    start_default: dt.date = dt.date(2010, 1, 1),
) -> dict:
    """codes: AMFI code -> instrument_id. AMFI history starts 2010-01-01 (P01)."""
    settings = settings or get_settings()
    s = PoliteSession(settings, browser=True, min_seconds=1.0)
    f = Fetcher(settings, run_id)
    out = {}
    end = dt.date.today()
    for code, iid in codes.items():
        st = []
        for a, b in _windows(start_default, end):
            path = settings.path("raw") / "in_amfi_hist" / str(code) / f"{a:%Y%m%d}_{b:%Y%m%d}.json"
            # the last (open) window is re-fetched when stale: name carries today's end date
            task = FetchTask(
                "in_amfi_hist",
                iid,
                AMFI_API,
                path,
                params={
                    "query_type": "historical_period",
                    "from_date": a.isoformat(),
                    "to_date": b.isoformat(),
                    "sd_id": str(code),
                },
            )
            res = f.run(
                task,
                lambda u, params=None, headers=None: s.get(u, params=params, timeout=120),
                validate=lambda c: c[:1] == b"{",
            )
            st.append(res.status)
        out[code] = st
    return out


def fetch_mfapi(codes: dict[int, str], settings: Settings | None = None, run_id: str = "") -> dict:
    settings = settings or get_settings()
    s = PoliteSession(settings, min_seconds=0.5)
    f = Fetcher(settings, run_id)
    out = {}
    for code, iid in codes.items():
        path = settings.path("raw") / "in_mfapi" / f"{code}.json"
        out[code] = f.run(
            FetchTask("in_mfapi", iid, MFAPI.format(code=code), path),
            lambda u, params=None, headers=None: s.get(u),
            validate=lambda c: b'"data"' in c[:4000],
        ).status
    return out


def stage_nav(codes: dict[int, str], settings: Settings | None = None) -> pd.DataFrame:
    settings = settings or get_settings()
    raw, root = settings.path("raw"), settings.root
    now = pd.Timestamp.now(tz="UTC").floor("s")
    amfi, mf = [], []
    for code, iid in codes.items():
        for p in sorted((raw / "in_amfi_hist" / str(code)).glob("*.json")):
            df = P.parse_amfi_historical_period(p.read_bytes())
            if df.empty:
                continue
            df["amfi_scheme_code"], df["instrument_id"], df["raw_path"] = (
                code,
                iid,
                p.relative_to(root).as_posix(),
            )
            amfi.append(df)
        for p in (raw / "in_mfapi" / f"{code}.json", raw / "_probes" / "in_mfapi" / f"{code}.json"):
            if p.exists():
                df = P.parse_mfapi(p.read_bytes())
                df["amfi_scheme_code"], df["instrument_id"], df["raw_path"] = (
                    code,
                    iid,
                    p.relative_to(root).as_posix(),
                )
                mf.append(df)
                break
    a = pd.concat(amfi, ignore_index=True) if amfi else pd.DataFrame()
    if len(a):
        a = a.sort_values(["instrument_id", "date", "uploaded_at_ist"]).drop_duplicates(
            ["instrument_id", "date"], keep="last"
        )
        a["source_id"], a["ingested_at"] = "in_amfi_hist", now
        stage(a, "in_nav", "in_amfi_hist", settings)
    m = pd.concat(mf, ignore_index=True) if mf else pd.DataFrame()
    if len(m):
        m = m.drop_duplicates(["instrument_id", "date"], keep="last")
        m["source_id"], m["ingested_at"] = "in_mfapi", now
        stage(m, "in_nav", "in_mfapi", settings)
    return a


def crosscheck_nav(settings: Settings | None = None, n: int = 50, seed: int = 20261117) -> pd.DataFrame:
    """AMFI vs mfapi on up to n random common dates per scheme (P05 T05.3)."""
    settings = settings or get_settings()
    d = settings.path("staged") / "in_nav"
    a = pd.read_parquet(d / "in_amfi_hist.parquet")[["instrument_id", "date", "nav"]]
    m = pd.read_parquet(d / "in_mfapi.parquet")[["instrument_id", "date", "nav"]]
    j = a.merge(m, on=["instrument_id", "date"], suffixes=("_amfi", "_mfapi"))
    rows = []
    for iid, g in j.groupby("instrument_id"):
        s = g.sample(min(n, len(g)), random_state=seed)
        agree = (s["nav_amfi"].round(4) == s["nav_mfapi"].round(4)).mean()
        rows.append({"instrument_id": iid, "sampled": len(s), "exact_agreement": round(float(agree), 4)})
    return pd.DataFrame(rows)


# ----------------------------------------------------------------------------- spot, VIX
def stage_spot(settings: Settings | None = None) -> pd.DataFrame:
    settings = settings or get_settings()
    frames = []
    for p in sorted((settings.path("manual_drop") / "in_spot").glob("MCX_*_SPOT*.xls")):
        df = P.parse_mcx_spot(p.read_bytes())
        df["metal"] = df["commodity"].str.lower()
        df["unit"] = df["unit"].map({"10 GRMS": "per_10g", "1 KGS": "per_kg"}).fillna(df["unit"])
        df["series_type"], df["source_id"], df["raw_path"] = (
            "mcx_polled_spot",
            "in_spot_mcx",
            p.relative_to(settings.root).as_posix(),
        )
        frames.append(df.rename(columns={"spot_price": "price_inr"}))
    out = pd.concat(frames, ignore_index=True)
    # the MCX export repeats some polls; conflicting prices at the same timestamp are averaged (median)
    keys = ["metal", "polled_at_ist"]
    n = out.groupby(keys)["price_inr"].transform("size")
    conflict = out.groupby(keys)["price_inr"].transform("nunique") > 1
    out["price_inr"] = out.groupby(keys)["price_inr"].transform("median")
    out["dup_polls"], out["conflicting_polls"] = n, conflict
    out = out.drop_duplicates(keys).reset_index(drop=True)
    out["purity"] = None  # not stated in the file (OQ-24)
    out["spot_time_local"] = out["time"]
    out["ingested_at"] = pd.Timestamp.now(tz="UTC").floor("s")
    stage(
        out[
            [
                "metal",
                "date",
                "polled_at_ist",
                "spot_time_local",
                "price_inr",
                "unit",
                "purity",
                "location",
                "dup_polls",
                "conflicting_polls",
                "series_type",
                "source_id",
                "raw_path",
                "ingested_at",
            ]
        ],
        "in_spot",
        "in_spot_mcx",
        settings,
    )
    return out


def fetch_stage_vix(settings: Settings | None = None, run_id: str = "") -> pd.DataFrame:
    import yfinance as yf

    settings = settings or get_settings()
    p = settings.path("raw") / "in_indiavix" / f"INDIAVIX_{dt.date.today():%Y%m%d}.csv"
    f = Fetcher(settings, run_id)
    task = FetchTask("in_indiavix", "SERIES:india_vix", "yfinance:^INDIAVIX", p)
    if not any(p.parent.glob("INDIAVIX_*.csv")) if p.parent.exists() else True:
        h = yf.Ticker("^INDIAVIX").history(period="max", auto_adjust=False)
        p.parent.mkdir(parents=True, exist_ok=True)
        h.to_csv(p)
        f.log(task, "ok", rows=len(h))
    p = sorted(p.parent.glob("INDIAVIX_*.csv"))[-1]
    h = pd.read_csv(p)
    out = pd.DataFrame(
        {
            "series_id": "india_vix",
            "date": pd.to_datetime(h["Date"].str[:10]),
            "value": h["Close"],
            "unit": "index",
            "source_id": "in_indiavix",
            "raw_path": p.relative_to(settings.root).as_posix(),
        }
    )
    stage(out, "in_misc", "in_indiavix", settings)
    return out


def amfi_codes(settings: Settings | None = None, include_only: bool = False) -> dict[int, str]:
    ind = load("instruments_in", settings)
    if include_only:
        ind = ind[ind["include"]]
    ind = ind.dropna(subset=["amfi_scheme_code"])
    return {int(c): i for c, i in zip(ind["amfi_scheme_code"], ind["instrument_id"], strict=True)}


def save_json(obj, path) -> None:
    path.write_text(json.dumps(obj, indent=1, default=str), encoding="utf-8")

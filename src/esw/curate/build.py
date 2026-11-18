"""P07: build the curated, point-in-time-stamped store in `data/curated/` (System Specification §6.3, §7).

Reads only `data/staged/`, `reference/` and the ingest manifest. Deterministic: rows sorted by primary
key, fixed column order, and `ingested_at` taken from the manifest (first successful log line of the
row's raw file), never from the wall clock. Run with `esw curate` (or `esw rebuild --curated`).
"""

from __future__ import annotations

import json
import shutil
from pathlib import Path

import numpy as np
import pandas as pd

from esw.config import Settings, get_settings
from esw.curate import pit
from esw.curate.splits import apply_actions, detect_candidates
from esw.reference import load
from esw.reference.calendars import build_calendar_frame

PX_COLS = [
    "instrument_id", "date", "open", "high", "low", "close", "volume", "traded_value", "n_trades",
    "split_factor_applied", "price_source", "mapped_by_symbol", "known_at", "source", "ingested_at",
]  # fmt: skip
NAV_COLS = [
    "instrument_id", "date", "nav", "shares_out", "total_net_assets", "nav_source", "known_at",
    "split_factor_applied", "source", "ingested_at",
]  # fmt: skip


# ----------------------------------------------------------------------------- helpers
def manifest_times(settings: Settings) -> dict[str, pd.Timestamp]:
    """raw path (posix) -> first successful ingest time (UTC)."""
    out: dict[str, pd.Timestamp] = {}
    with open(settings.path("manifests") / "ingest_log.jsonl", encoding="utf-8") as fh:
        for line in fh:
            try:
                r = json.loads(line)
            except json.JSONDecodeError:
                continue
            if r.get("status") not in {"ok", "manual"}:
                continue
            p = str(r.get("path", "")).replace("\\", "/")
            if p and p not in out:
                out[p] = pd.Timestamp(r["ts_utc"])
    return out


def _ingested(raw_paths: pd.Series, times: dict) -> pd.Series:
    rp = raw_paths.astype(str).str.replace("\\", "/", regex=False)
    uniq = {p: times.get(p, pd.NaT) for p in rp.unique()}
    return pd.to_datetime(rp.map(uniq), utc=True)


def _write(df: pd.DataFrame, name: str, keys: list[str], settings: Settings) -> Path:
    out = settings.path("curated") / f"{name}.parquet"
    out.parent.mkdir(parents=True, exist_ok=True)
    df = df.sort_values(keys, kind="mergesort").reset_index(drop=True)
    dup = df.duplicated(subset=keys)
    if dup.any():
        raise ValueError(f"{name}: {int(dup.sum())} duplicate primary keys {keys}")
    df.to_parquet(out, index=False)
    return out


# ----------------------------------------------------------------------------- instruments
def build_instrument(settings: Settings) -> pd.DataFrame:
    us, ind = load("instruments_us", settings), load("instruments_in", settings)
    nc = load("nav_clock", settings)
    first_basis = nc.sort_values("effective_from").groupby("instrument_id")["nav_basis"].first()
    a = us.assign(is_mirae=False)[
        [
            "instrument_id",
            "market",
            "ticker",
            "isin",
            "name",
            "issuer",
            "group",
            "subgroup",
            "underlying",
            "legal_form",
            "listing_date",
            "delisting_date",
            "currency",
            "is_mirae",
            "rule_6c11",
            "include",
            "exclude_reason",
        ]
    ]
    b = ind.assign(
        ticker=ind["nse_symbol_current"],
        legal_form="open_end",
        currency="INR",
        rule_6c11="n",
        delisting_date=pd.NaT,
    )
    b["listing_date"] = b["listing_date"].fillna(b["inception_date"])
    b = b[a.columns]
    out = pd.concat([a, b], ignore_index=True)
    out["nav_basis_default"] = out["instrument_id"].map(first_basis)
    out["source"] = "reference"
    return out


# ----------------------------------------------------------------------------- calendar
def reconcile_india_calendar(settings: Settings) -> tuple[pd.DataFrame, pd.DataFrame]:
    """NSE bhavcopy presence (>= 500 rows) is authoritative for past dates (P05 T05.6)."""
    cal = build_calendar_frame(settings)
    summ = pd.read_parquet(settings.path("staged") / "in_bhav" / "bhav_day_summary.parquet")
    traded = set(summ.loc[summ["rows"] >= 500, "date"])
    last = summ["date"].max()
    india = cal[cal["market"] == "XNSE"].copy()
    past = india["date"] <= last
    lib = india["is_trading"].copy()
    obs = india["date"].isin(traded)
    diff = india[past & (lib != obs)].copy()
    diff["library"] = lib[past & (lib != obs)]
    diff["bhavcopy"] = obs[past & (lib != obs)]
    india.loc[past, "is_trading"] = obs[past]
    wkend = india["date"].dt.dayofweek >= 5
    india.loc[past & obs & (wkend | ~lib), "session_type"] = "special"
    india.loc[past & obs & lib & ~wkend & india["session_type"].isna(), "session_type"] = "regular"
    india.loc[past & ~obs, "session_type"] = None
    india.loc[past, "source"] = "NSE bhavcopy presence (>= 500 rows)"
    cal = pd.concat([cal[cal["market"] != "XNSE"], india], ignore_index=True)
    return cal, diff[["date", "library", "bhavcopy"]]


# ----------------------------------------------------------------------------- prices
def build_px(settings: Settings, times: dict, actions: pd.DataFrame, inst: pd.DataFrame) -> pd.DataFrame:
    st = settings.path("staged")
    us = pd.read_parquet(st / "us_px" / "us_px_tiingo.parquet")
    us["price_source"] = "us_px_tiingo"
    yfp = st / "us_px" / "us_px_yf.parquet"
    if yfp.exists():  # fallback only for instruments Tiingo lacks
        yf = pd.read_parquet(yfp)
        yf = yf[~yf["instrument_id"].isin(us["instrument_id"])]
        yf["price_source"] = "us_px_yf"
        us = pd.concat([us, yf], ignore_index=True)
    us["traded_value"], us["n_trades"], us["mapped_by_symbol"] = np.nan, np.nan, False
    us["known_at"] = pit.us_price_known_at(us["date"])
    india = pd.read_parquet(st / "in_bhav" / "in_bhav_nse.parquet")
    india["price_source"] = "in_bhav_nse"
    india["mapped_by_symbol"] = india["mapped_by"].eq("symbol")
    india["known_at"] = pit.india_bhav_known_at(india["date"])
    px = pd.concat([us, india], ignore_index=True)
    px = px[px["instrument_id"].isin(inst["instrument_id"])]
    px["ingested_at"] = _ingested(px["raw_path"], times)
    px["source"] = px["price_source"]
    parts = []
    for iid, g in px.groupby("instrument_id", sort=True):
        g = apply_actions(
            g, actions[actions["instrument_id"] == iid], ["open", "high", "low", "close"], "price"
        )
        g["volume"] = g["volume"] / g["split_factor_applied"]
        parts.append(g)
    px = pd.concat(parts, ignore_index=True)
    return px.reindex(columns=PX_COLS)


# ----------------------------------------------------------------------------- NAV
def build_nav(
    settings: Settings, times: dict, actions: pd.DataFrame, inst_us: pd.DataFrame
) -> tuple[pd.DataFrame, pd.DataFrame]:
    st = settings.path("staged") / "us_nav"
    frames, prem = [], []
    for r in inst_us.itertuples(index=False):
        src = r.nav_source_id
        p = st / f"{src}.parquet"
        if not p.exists():
            continue
        d = pd.read_parquet(p)
        d = d[d["ticker"] == r.ticker].copy()
        if d.empty:
            continue
        d["nav_source"] = src
        frames.append(d)
        if d["issuer_prem_bps"].notna().any():
            prem.append(
                d.dropna(subset=["issuer_prem_bps"])[
                    [
                        "instrument_id",
                        "date",
                        "issuer_prem_bps",
                        "issuer_mid",
                        "issuer_close",
                        "nav_source",
                        "raw_path",
                    ]
                ]
            )
    us = pd.concat(frames, ignore_index=True)
    us["known_at"] = pit.us_nav_known_at(us["date"])
    ins = settings.path("staged") / "in_nav"
    amfi = pd.read_parquet(ins / "in_amfi_hist.parquet")
    amfi["nav_source"] = "in_amfi_hist"
    amfi["known_at"] = pit.amfi_nav_known_at(amfi["date"], amfi["uploaded_at_ist"])
    mf = pd.read_parquet(ins / "in_mfapi.parquet")
    mf = mf.merge(amfi[["instrument_id", "date"]], on=["instrument_id", "date"], how="left", indicator=True)
    mf = mf[mf["_merge"] == "left_only"].drop(columns="_merge")  # fallback rows only
    mf["nav_source"] = "in_mfapi"
    mf["known_at"] = pit.amfi_nav_known_at(mf["date"])
    nav = pd.concat([us, amfi, mf], ignore_index=True)
    nav["ingested_at"] = _ingested(nav["raw_path"], times)
    nav["source"] = nav["nav_source"]
    parts = []
    for iid, g in nav.groupby("instrument_id", sort=True):
        g = g.sort_values("date").drop_duplicates("date", keep="first")
        parts.append(apply_actions(g, actions[actions["instrument_id"] == iid], ["nav"], "nav"))
    nav = pd.concat(parts, ignore_index=True).reindex(columns=NAV_COLS)
    ip = pd.concat(prem, ignore_index=True) if prem else pd.DataFrame()
    if len(ip):
        ip["known_at"] = pit.us_nav_known_at(ip["date"])
        ip["ingested_at"] = _ingested(ip["raw_path"], times)
        ip = ip.rename(columns={"nav_source": "source"}).drop(columns="raw_path")
    return nav, ip


# ----------------------------------------------------------------------------- series
def build_series(settings: Settings, times: dict) -> pd.DataFrame:
    cat = load("series_catalogue", settings).set_index("series_id")
    frames = []
    paths = sorted((settings.path("staged") / "series").glob("*.parquet")) + sorted(
        (settings.path("staged") / "in_misc").glob("*.parquet")
    )
    for p in paths:
        d = pd.read_parquet(p)
        sid = str(d["series_id"].iloc[0])
        lag, tz = (
            (int(cat.at[sid, "publication_lag_days"]), cat.at[sid, "tz"])
            if sid in cat.index
            else (1, "America/New_York")
        )
        d["known_at"] = pit.series_known_at(d["date"], lag, tz)
        d["ingested_at"] = _ingested(d["raw_path"], times)
        d["source"] = d["source_id"]
        frames.append(
            d[
                ["series_id", "date", "value", "unit", "known_at", "source", "ingested_at"]
                + (["ret", "roll_flag"] if "ret" in d else [])
            ]
        )
    return pd.concat(frames, ignore_index=True)


# ----------------------------------------------------------------------------- checks
def quality_checks(
    px: pd.DataFrame, nav: pd.DataFrame, inst: pd.DataFrame, annotations: pd.DataFrame
) -> pd.DataFrame:
    flags = []
    detected = pd.Timestamp("2026-01-01", tz="UTC")  # fixed for determinism; real time in the run log

    def add(table, iid, date, check, severity, detail):
        flags.append(
            {
                "table": table,
                "key": f"{iid}|{pd.Timestamp(date).date()}",
                "instrument_id": iid,
                "date": pd.Timestamp(date),
                "check_id": check,
                "severity": severity,
                "detail": detail,
                "detected_at": detected,
            }
        )

    bad = px[
        (px["high"] < px[["open", "close"]].max(axis=1) - 1e-9)
        | (px["low"] > px[["open", "close"]].min(axis=1) + 1e-9)
    ]
    for r in bad.itertuples(index=False):
        add(
            "px_daily", r.instrument_id, r.date, "ohlc_order", "warn", "high/low inconsistent with open/close"
        )
    for r in px[px["close"] <= 0].itertuples(index=False):
        add("px_daily", r.instrument_id, r.date, "nonpositive_close", "error", "close <= 0")
    m = px[["instrument_id", "date", "close"]].merge(
        nav[["instrument_id", "date", "nav"]], on=["instrument_id", "date"]
    )
    m["gap"] = m["close"] / m["nav"] - 1
    ann = annotations.set_index("instrument_id") if len(annotations) else pd.DataFrame()
    for r in m[m["gap"].abs() > 0.25].itertuples(index=False):
        note = ""
        if r.instrument_id in getattr(ann, "index", []):
            a = ann.loc[[r.instrument_id]]
            hit = a[(a["start"] <= r.date) & (a["end"] >= r.date)]
            note = "; ".join(hit["note"]) if len(hit) else ""
        add(
            "px_daily",
            r.instrument_id,
            r.date,
            "gap_gt_25pct",
            "warn",
            f"close/NAV-1 = {r.gap:.1%}" + (f"; annotated: {note}" if note else "; not annotated"),
        )
    for iid, g in m.groupby("instrument_id"):
        c = detect_candidates(g)
        for r in c.itertuples(index=False):
            add(
                "px_daily",
                iid,
                r.date,
                "split_candidate",
                "error",
                f"price ratio {r.price_ratio:.4f}, NAV ratio {r.nav_ratio:.4f}, leg {r.leg}, fraction {r.fraction:g}",
            )
    for iid, g in nav.groupby("instrument_id"):
        g = g.sort_values("date")
        ret = np.log(g["nav"]).diff()
        mad = (ret - ret.median()).abs().median() * 1.4826
        if mad and mad > 0:
            z = ret / mad
            spike = (z.abs() > 5) & (z.shift(-1).abs() > 5) & (np.sign(z) != np.sign(z.shift(-1)))
            for d in g.loc[spike, "date"]:
                add("nav_daily", iid, d, "nav_spike", "warn", "jump-and-reverse > 5 robust sd")
        same = g["nav"].eq(g["nav"].shift())
        run = same.groupby((~same).cumsum()).cumsum()
        for d in g.loc[run == 3, "date"]:
            add("nav_daily", iid, d, "nav_stale_run", "info", "NAV unchanged 3+ days")
    return pd.DataFrame(flags)


def _annotations(settings: Settings) -> pd.DataFrame:
    """Known incident windows used to annotate large gaps (from the catalogue)."""
    inc = pd.read_csv(settings.path("reference") / "incidents.csv", dtype=str, keep_default_na=False)
    rows = []
    for r in inc.itertuples(index=False):
        end = pd.Timestamp(r.approx_end) if r.approx_end else pd.Timestamp("2100-01-01")
        for iid in r.instrument_ids.split(";"):
            rows.append(
                {
                    "instrument_id": iid,
                    "start": pd.Timestamp(r.approx_onset) - pd.Timedelta(days=30),
                    "end": end + pd.Timedelta(days=30),
                    "note": r.incident_id,
                }
            )
    extra = settings.path("reference") / "gap_annotations.csv"
    if extra.exists():
        e = pd.read_csv(extra, dtype=str, keep_default_na=False)
        for r in e.itertuples(index=False):
            rows.append(
                {
                    "instrument_id": r.instrument_id,
                    "start": pd.Timestamp(r.start),
                    "end": pd.Timestamp(r.end) if r.end else pd.Timestamp("2100-01-01"),
                    "note": r.note,
                }
            )
    return pd.DataFrame(rows)


# ----------------------------------------------------------------------------- data cutoff
def data_cutoff(px: pd.DataFrame, nav: pd.DataFrame, inst: pd.DataFrame, share: float = 0.9) -> pd.Timestamp:
    inc = inst[inst["include"]]
    both = px[["instrument_id", "date"]].merge(nav[["instrument_id", "date"]], on=["instrument_id", "date"])
    both = both[both["instrument_id"].isin(inc["instrument_id"])]
    both["market"] = both["instrument_id"].str[:2]
    n = inc.assign(market=inc["instrument_id"].str[:2]).groupby("market").size()
    per = both.groupby(["market", "date"]).size().unstack(0).fillna(0)
    ok = (per["US"] >= share * n["US"]) & (per["IN"] >= share * n["IN"])
    return ok[ok].index.max()


# ----------------------------------------------------------------------------- main
def build_all(settings: Settings | None = None, clean: bool = True) -> dict:
    settings = settings or get_settings()
    cur = settings.path("curated")
    if clean and cur.exists():
        for p in cur.glob("*.parquet"):
            p.unlink()
    times = manifest_times(settings)
    inst = build_instrument(settings)
    actions = load("corporate_actions_manual", settings)
    actions["ex_date"] = pd.to_datetime(actions["ex_date"])
    cal, cal_diff = reconcile_india_calendar(settings)
    px = build_px(settings, times, actions, inst)
    nav, iprem = build_nav(settings, times, actions, load("instruments_us", settings))
    series = build_series(settings, times)
    flags = quality_checks(px, nav, inst, _annotations(settings))
    cutoff = data_cutoff(px, nav, inst)
    out = {}
    out["instrument"] = _write(inst, "instrument", ["instrument_id"], settings)
    out["calendar"] = _write(
        cal.drop(columns=["ingested_at"], errors="ignore"), "calendar", ["market", "date"], settings
    )
    out["px_daily"] = _write(px, "px_daily", ["instrument_id", "date"], settings)
    out["nav_daily"] = _write(nav, "nav_daily", ["instrument_id", "date"], settings)
    if len(iprem):
        out["issuer_premium"] = _write(iprem, "issuer_premium", ["instrument_id", "date"], settings)
    out["series_daily"] = _write(series, "series_daily", ["series_id", "date"], settings)
    ref = settings.path("reference")
    sh = load("symbol_history", settings)
    out["symbol_history"] = _write(
        sh.assign(source="reference"),
        "symbol_history",
        ["instrument_id", "exchange", "symbol", "isin", "valid_from"],
        settings,
    )
    ca = actions.copy()
    out["corporate_action"] = _write(
        ca.assign(source="reference"),
        "corporate_action",
        ["instrument_id", "ex_date", "type", "applies_to"],
        settings,
    )
    ev = pd.read_csv(ref / "operational_events.csv", dtype=str, keep_default_na=False)
    ev["effective_at"] = pd.to_datetime(ev["effective_at"])
    ev["known_at"] = pd.to_datetime(ev["known_at"].replace("", None), utc=True)
    ev["ended_known_at"] = pd.to_datetime(ev["ended_known_at"].replace("", None), utc=True)
    out["operational_event"] = _write(
        ev.assign(source="reference"), "operational_event", ["event_id"], settings
    )
    inc = pd.read_csv(ref / "incidents.csv", dtype=str, keep_default_na=False)
    out["incident"] = _write(inc.assign(source="reference"), "incident", ["incident_id"], settings)
    cap = pd.read_csv(ref / "capacity_us.csv", dtype=str, keep_default_na=False)
    cap["known_at"] = pd.to_datetime(cap["known_at"], utc=True)
    out["capacity"] = _write(
        cap.assign(source="reference"),
        "capacity",
        ["instrument_id", "as_of", "metric", "known_at", "value"],
        settings,
    )
    for name, keys in (
        ("duty_india", ["metal", "effective_from"]),
        ("band_regimes_india", ["market", "exchange", "group", "effective_from"]),
        ("nav_clock", ["instrument_id", "effective_from"]),
    ):
        out[name] = _write(
            load(name, settings).assign(source="reference"),
            {"duty_india": "duty", "band_regimes_india": "band_regime"}.get(name, name),
            keys,
            settings,
        )
    sp = settings.path("staged") / "in_spot" / "in_spot_mcx.parquet"
    if sp.exists():
        spot = pd.read_parquet(sp)
        spot["known_at"] = spot["polled_at_ist"].dt.tz_convert("UTC")  # a poll is public when published
        spot["ingested_at"] = _ingested(spot["raw_path"], times)
        spot["source"] = spot["source_id"]
        out["in_spot_polls"] = _write(
            spot.drop(columns=["raw_path", "source_id"]),
            "in_spot_polls",
            ["metal", "polled_at_ist"],
            settings,
        )
    if len(flags):
        out["quality_flag"] = _write(flags, "quality_flag", ["table", "key", "check_id"], settings)
    (cur / "DATA_CUTOFF.txt").write_text(f"{cutoff.date()}\n", encoding="utf-8")
    cal_diff.to_csv(settings.path("reports") / "data" / "india_calendar_reconciliation.csv", index=False)
    return {"cutoff": cutoff, "flags": flags, "cal_diff": cal_diff, "px": px, "nav": nav, "paths": out}


def rebuild(settings: Settings | None = None) -> dict:
    settings = settings or get_settings()
    cur = settings.path("curated")
    if cur.exists():
        shutil.rmtree(cur)
    return build_all(settings)

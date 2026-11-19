"""P08 T08.1: the pricing panel -> `data/derived/pricing/pricing_panel.parquet`.

One row per (instrument, date) on the instrument's listing calendar from its first price to
min(delisting, DATA_CUTOFF). Reads only `data/curated/` and `reference/`.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from esw.config import Settings, get_settings
from esw.pricing.band import baseline_scale, empirical_band
from esw.pricing.layer1 import daily_spot, layer1, total_gap
from esw.pricing.locks import classify


def _cur(settings: Settings, name: str) -> pd.DataFrame:
    return pd.read_parquet(settings.path("curated") / f"{name}.parquet")


def cutoff(settings: Settings) -> pd.Timestamp:
    return pd.Timestamp((settings.path("curated") / "DATA_CUTOFF.txt").read_text().strip())


def infer_lock(df: pd.DataFrame, band: float = 0.20, tol: float = 0.0025) -> pd.Series:
    """Where the regime is unknown, infer a lock from the data: close = high = low (or close at the
    high/low) at +/-20% of T-1 or T-2 NAV. Reported alongside the spec's `lock_class`; not used for `valid`."""
    out = df["lock_class"].copy()
    unk = out == "unknown"
    for k in (1, 2):
        ref = df["nav"].shift(k)
        dn = (df["close"] / (ref * (1 - band)) - 1).abs() < tol
        up = (df["close"] / (ref * (1 + band)) - 1).abs() < tol
        at_extreme = (dn & (df["close"] <= df["low"] * (1 + 1e-9))) | (
            up & (df["close"] >= df["high"] * (1 - 1e-9))
        )
        out[unk & at_extreme] = "inferred_locked"
    return out


def nav_basis_on(nc: pd.DataFrame, iid: str, dates: pd.Series) -> pd.Series:
    g = nc[nc["instrument_id"] == iid].sort_values("effective_from")
    out = pd.Series(None, index=dates.index, dtype="object")
    for r in g.itertuples(index=False):
        end = r.effective_to if pd.notna(r.effective_to) else pd.Timestamp("2100-01-01")
        out[(dates >= r.effective_from) & (dates <= end)] = r.nav_basis
    return out


def build_panel(settings: Settings | None = None, instruments: list[str] | None = None) -> pd.DataFrame:
    settings = settings or get_settings()
    p = settings.params
    inst = _cur(settings, "instrument")
    inst = inst[inst["include"]] if instruments is None else inst[inst["instrument_id"].isin(instruments)]
    px, nav, cal = _cur(settings, "px_daily"), _cur(settings, "nav_daily"), _cur(settings, "calendar")
    nc, bands, duty = _cur(settings, "nav_clock"), _cur(settings, "band_regime"), _cur(settings, "duty")
    flags = (
        _cur(settings, "quality_flag")
        if (settings.path("curated") / "quality_flag.parquet").exists()
        else pd.DataFrame(columns=["instrument_id", "date", "check_id"])
    )
    spikes = flags[flags["check_id"] == "nav_spike"][["instrument_id", "date"]].assign(nav_spike=True)
    iprem_path = settings.path("curated") / "issuer_premium.parquet"
    iprem = (
        pd.read_parquet(iprem_path)[["instrument_id", "date", "issuer_prem_bps"]]
        if iprem_path.exists()
        else None
    )
    series = _cur(settings, "series_daily")
    gold_g = series[series["series_id"] == "gold_usd_fut"].set_index("date")["value"]
    silver_g = series[series["series_id"] == "silver_usd_fut"].set_index("date")["value"]
    fx = series[series["series_id"] == "usdinr_yf"].set_index("date")["value"]
    spot_p = settings.path("curated") / "in_spot_polls.parquet"
    spot = daily_spot(pd.read_parquet(spot_p)) if spot_p.exists() else None
    navimpl = series[series["series_id"] == "gold_usd_navimpl"].set_index("date")["value"]
    cut = cutoff(settings)
    frames = []
    for r in inst.itertuples(index=False):
        iid = r.instrument_id
        mkt = "XNYS" if r.market == "US" else "XNSE"
        P = px[px["instrument_id"] == iid]
        if P.empty:
            continue
        start = P["date"].min()
        end = min(r.delisting_date if pd.notna(r.delisting_date) else cut, cut)
        days = cal[
            (cal["market"] == mkt) & cal["is_trading"] & (cal["date"] >= start) & (cal["date"] <= end)
        ][["date"]]
        df = days.merge(
            P[["date", "open", "high", "low", "close", "volume", "traded_value", "n_trades"]],
            on="date",
            how="left",
        )
        df = df.merge(nav[nav["instrument_id"] == iid][["date", "nav", "shares_out"]], on="date", how="left")
        df = df.merge(spikes[spikes["instrument_id"] == iid][["date", "nav_spike"]], on="date", how="left")
        df["nav_spike"] = df["nav_spike"].fillna(False).astype(bool)
        df.insert(0, "instrument_id", iid)
        df["market"], df["group"] = r.market, r.group
        if r.market == "IN":
            lk = classify(df[["date", "close", "high", "low", "nav"]], bands, r.group)
            df = pd.concat([df.reset_index(drop=True), lk], axis=1)
            df["lock_class_inferred"] = infer_lock(df)
        else:
            df["lock_class_inferred"] = "unconstrained"
            df["lock_class"], df["band_ref_price"], df["band_limit_up"], df["band_limit_down"] = (
                "unconstrained",
                np.nan,
                np.nan,
                np.nan,
            )
        df["valid"] = (
            (df["close"] > 0) & (df["nav"] > 0) & ~df["nav_spike"] & (df["lock_class"] != "confirmed_locked")
        )
        df["prem_bps"] = (1e4 * (df["close"] / df["nav"] - 1)).where(df["valid"])
        df["ret_px"] = df["close"] / df["close"].shift() - 1
        df["ret_nav"] = df["nav"] / df["nav"].shift() - 1
        df["div_bps"] = 1e4 * (df["ret_px"] - df["ret_nav"])
        bs = baseline_scale(
            df["prem_bps"], df["valid"], p.BASE_WIN, p.BASE_MIN, p.SCALE_WIN, p.SCALE_MIN, p.SCALE_FLOOR_BPS
        )
        bd = empirical_band(df["prem_bps"], df["valid"], p.SCALE_WIN, p.SCALE_MIN)
        df = pd.concat([df, bs, bd], axis=1)
        df["nav_basis"] = nav_basis_on(nc, iid, df["date"])
        df["post_strike_move_bps"] = np.nan
        if iid in ("US:GLD", "US:IAU", "US:GLDM"):
            gf = gold_g.reindex(df["date"]).values
            ni = navimpl.reindex(df["date"]).values
            df["post_strike_move_bps"] = 1e4 * (gf / ni - 1)
        for c in ("lp_bps", "lp_bps_med5", "tg_bps", "parity_inr", "domestic_spot_inr", "duty_total_pct"):
            df[c] = np.nan
        df["lp_null_reason"] = "not_applicable"
        if r.group in ("IN_GOLD", "IN_SILVER") and spot is not None:
            metal = "gold" if r.group == "IN_GOLD" else "silver"
            l1 = layer1(metal, df["date"], spot, gold_g if metal == "gold" else silver_g, fx, duty)
            for c in (
                "lp_bps",
                "lp_bps_med5",
                "parity_inr",
                "domestic_spot_inr",
                "duty_total_pct",
                "lp_null_reason",
            ):
                df[c] = l1[c].values
            post = df["nav_basis"] == "in_domestic_spot"
            df.loc[post, "tg_bps"] = total_gap(df.loc[post, "prem_bps"], df.loc[post, "lp_bps"])
        df["issuer_prem_bps"] = np.nan
        if iprem is not None:
            ip = iprem[iprem["instrument_id"] == iid].set_index("date")["issuer_prem_bps"]
            df["issuer_prem_bps"] = ip.reindex(df["date"]).values
        df["issuer_prem_diff_bps"] = df["prem_bps"] - df["issuer_prem_bps"]
        frames.append(df)
    panel = pd.concat(frames, ignore_index=True)
    out = settings.path("derived") / "pricing" / "pricing_panel.parquet"
    out.parent.mkdir(parents=True, exist_ok=True)
    panel.sort_values(["instrument_id", "date"]).reset_index(drop=True).to_parquet(out, index=False)
    return panel

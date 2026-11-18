"""India Layer 1 (Spec §4.4): domestic spot vs import parity, and the total investor gap.

parity(t) = G(t-1 US close) x FX(t-1) x (1 + duty(t)) converted to the domestic quote unit:
gold per 10 g of 995 purity, silver per kg of 999 purity (MCX spot units; purity assumed, OQ-24).
D(t) = MCX polled spot nearest to (and preferably not after) the 15:30 IST close.
Inputs dated t-1 are known before the Indian close; the timing mismatch is acknowledged and dampened
by the 5-day median `lp_bps_med5`.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

TROY_OZ_G = 31.1034768
UNIT = {"gold": (10.0, 0.995), "silver": (1000.0, 0.999)}  # grams per quote unit, purity


def daily_spot(polls: pd.DataFrame, close_hhmm: str = "15:30") -> pd.DataFrame:
    """One domestic price per metal and day: last poll at or before the close, else the first after."""
    p = polls.copy()
    p["t"] = p["polled_at_ist"].dt.strftime("%H:%M")
    p["before"] = p["t"] <= close_hhmm
    p["key"] = np.where(p["before"], p["t"], "99:" + p["t"])  # prefer the latest poll before the close
    best = p.sort_values(["metal", "date", "before", "key"], ascending=[True, True, False, False])
    best = best.groupby(["metal", "date"], as_index=False).first()
    return best[["metal", "date", "price_inr", "unit", "t"]].rename(
        columns={"price_inr": "domestic_spot_inr", "t": "spot_time_local"}
    )


def duty_on(dates: pd.Series, duty: pd.DataFrame, metal: str) -> pd.DataFrame:
    d = duty[duty["metal"] == metal].sort_values("effective_from")
    out = pd.DataFrame({"date": dates.values, "duty_total_pct": np.nan, "duty_verified": False})
    for r in d.itertuples(index=False):
        end = r.effective_to if pd.notna(r.effective_to) else pd.Timestamp("2100-01-01")
        m = (out["date"] >= r.effective_from) & (out["date"] <= end)
        out.loc[m, "duty_total_pct"] = r.total_pct
        out.loc[m, "duty_verified"] = r.verified == "y"
    return out


def layer1(
    metal: str, dates: pd.Series, spot: pd.DataFrame, g_usd: pd.Series, fx: pd.Series, duty: pd.DataFrame
) -> pd.DataFrame:
    """g_usd and fx: series indexed by date (US/London dates); the previous available value is used."""
    df = pd.DataFrame({"date": pd.to_datetime(dates.values)})
    s = spot[spot["metal"] == metal][["date", "domestic_spot_inr"]]
    df = df.merge(s, on="date", how="left")
    prev = df["date"] - pd.Timedelta(days=1)
    gi = g_usd.sort_index()
    fi = fx.sort_index()
    df["g_usd"] = gi.reindex(gi.index.union(prev)).ffill().reindex(prev).values
    df["fx"] = fi.reindex(fi.index.union(prev)).ffill().reindex(prev).values
    du = duty_on(df["date"], duty, metal)
    df["duty_total_pct"] = du["duty_total_pct"].values
    grams, purity = UNIT[metal]
    df["parity_inr"] = df["g_usd"] * df["fx"] / TROY_OZ_G * grams * purity * (1 + df["duty_total_pct"] / 100)
    df["lp_bps"] = 1e4 * (df["domestic_spot_inr"] / df["parity_inr"] - 1)
    reason = np.select(
        [
            df["domestic_spot_inr"].isna(),
            df["g_usd"].isna() | df["fx"].isna(),
            ~du["duty_verified"].values,
            df["duty_total_pct"].isna(),
        ],
        ["no_domestic_spot", "no_global_or_fx", "duty_unverified", "duty_not_ad_valorem"],
        default="",
    )
    df["lp_null_reason"] = reason
    df.loc[reason != "", "lp_bps"] = np.nan
    df["lp_bps_med5"] = df["lp_bps"].rolling(5, min_periods=3).median()
    return df


def total_gap(prem_bps: pd.Series, lp_nav_bps: pd.Series) -> pd.Series:
    return 1e4 * ((1 + prem_bps / 1e4) * (1 + lp_nav_bps / 1e4) - 1)

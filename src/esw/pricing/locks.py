"""India lock classification (Spec §4.11) from `band_regime` rows in force per exchange, group and date."""

from __future__ import annotations

import numpy as np
import pandas as pd

GROUP_MAP = {
    "IN_GOLD": "gold_silver",
    "IN_SILVER": "gold_silver",
    "IN_INTL": "international",
    "IN_CTRL": "equity_debt",
    "IN_DEBT": "equity_debt",
}


def regime_rows(bands: pd.DataFrame, exchange: str, group: str, dates: pd.Series) -> pd.DataFrame:
    b = bands[(bands["exchange"] == exchange) & (bands["group"] == group)].sort_values("effective_from")
    out = pd.DataFrame({"date": dates.values})
    out["base_rule"], out["band_pct"], out["verified"] = None, np.nan, None
    for r in b.itertuples(index=False):
        end = r.effective_to if pd.notna(r.effective_to) else pd.Timestamp("2100-01-01")
        m = (out["date"] >= r.effective_from) & (out["date"] <= end)
        out.loc[m, "base_rule"] = r.base_rule
        out.loc[m, "band_pct"] = r.band_init_pct
        out.loc[m, "verified"] = r.verified
    return out


def classify(df: pd.DataFrame, bands: pd.DataFrame, group: str, exchange: str = "NSE") -> pd.DataFrame:
    """df: one Indian instrument sorted by date with close, high, low, nav. Returns lock columns."""
    df = df.reset_index(drop=True)
    g = GROUP_MAP.get(group, "equity_debt")
    reg = regime_rows(bands, exchange, g, df["date"])
    ref = pd.Series(np.nan, index=df.index)
    ref[reg["base_rule"] == "t2_nav"] = df["nav"].shift(2)
    ref[reg["base_rule"] == "t1_nav"] = df["nav"].shift(1)
    ref[reg["base_rule"] == "t1_vwap30"] = df["close"].shift(1)  # NSE close = last-30-minute VWAP (OQ-02)
    pct = reg["band_pct"] / 100.0
    up, down = ref * (1 + pct), ref * (1 - pct)
    near_up = (df["close"] >= up * (1 - 0.01)) & up.notna()
    near_dn = (df["close"] <= down * (1 + 0.01)) & down.notna()
    lock_up = (df["close"] >= up * (1 - 0.0025)) & up.notna()
    lock_dn = (df["close"] <= down * (1 + 0.0025)) & down.notna()
    flat = (df["high"] == df["low"]) & (df["low"] == df["close"])
    cls = np.where(
        (lock_up | lock_dn) & flat,
        "confirmed_locked",
        np.where(near_up | near_dn, "near_band", "unconstrained"),
    )
    cls = pd.Series(cls, index=df.index).where((reg["verified"] == "y") & ref.notna(), "unknown")
    return pd.DataFrame(
        {
            "lock_class": cls.values,
            "band_ref_price": ref.values,
            "band_limit_up": up.values,
            "band_limit_down": down.values,
        }
    )

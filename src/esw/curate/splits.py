"""Split and unit consistency (System Specification §6.5; P07 T07.4).

`apply_actions` puts a raw series on the **current unit basis**: for each verified corporate action
with ratio r (new units per old unit) on ex-date d that applies to this series, values dated before d
are divided by r. `detect_candidates` flags day pairs where price and NAV change by different
amounts close to a simple fraction (k or 1/k, k = 2..20, or 25/50/100 for Indian unit splits).
"""

from __future__ import annotations

import numpy as np
import pandas as pd

FRACTIONS = sorted({float(k) for k in range(2, 21)} | {25.0, 50.0, 100.0})


def apply_actions(df: pd.DataFrame, actions: pd.DataFrame, value_cols: list[str], leg: str) -> pd.DataFrame:
    """df: one instrument, columns date + value_cols. leg: 'price' or 'nav'. Adds split_factor_applied."""
    df = df.sort_values("date").copy()
    factor = pd.Series(1.0, index=df.index)
    act = actions[(actions["applies_to"].isin([leg, "both"])) & (actions["verified"] == "y")]
    for a in act.itertuples(index=False):
        before = df["date"] < pd.Timestamp(a.ex_date)
        factor[before] = factor[before] / float(a.ratio)
    for c in value_cols:
        if c in df.columns:
            df[c] = df[c] * factor
    if "shares_out" in df.columns and leg == "nav":
        df["shares_out"] = df["shares_out"] / factor  # shares scale inversely
    df["split_factor_applied"] = factor
    return df


def _near_fraction(x: float, tol: float = 0.02) -> float | None:
    for k in FRACTIONS:
        for v in (k, 1.0 / k):
            if abs(x / v - 1) < tol:
                return v
    return None


def detect_candidates(merged: pd.DataFrame, min_gap: float = np.log(1.5)) -> pd.DataFrame:
    """merged: one instrument with date, close, nav (both on the basis already applied).

    Flags dates where |log r_p - log r_n| > log 1.5 and either ratio is within 2% of a simple fraction.
    """
    m = merged.sort_values("date").dropna(subset=["close", "nav"]).copy()
    rp = m["close"] / m["close"].shift()
    rn = m["nav"] / m["nav"].shift()
    gap = (np.log(rp) - np.log(rn)).abs()
    out = []
    for i in m.index[gap > min_gap]:
        fp, fn = _near_fraction(rp[i]), _near_fraction(rn[i])
        if fp is None and fn is None:
            continue
        out.append(
            {
                "date": m.at[i, "date"],
                "price_ratio": float(rp[i]),
                "nav_ratio": float(rn[i]),
                "leg": "price"
                if fp is not None and fn is None
                else ("nav" if fn is not None and fp is None else "both"),
                "fraction": fp if fp is not None else fn,
            }
        )
    return pd.DataFrame(out)

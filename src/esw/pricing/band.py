"""Robust baseline/scale (Spec §4.5) and empirical no-arbitrage band (§4.9), strictly backward-looking.

All statistics for row t use only *valid* rows strictly before t. The panel versions here are not
episode-frozen (that is a label-module concept, P09).
"""

from __future__ import annotations

import numpy as np
import pandas as pd


def _prior_valid(stat_on_valid: pd.Series, index: pd.Index) -> pd.Series:
    """Map a statistic computed on the valid sub-series (inclusive of each valid obs) to every row t as
    the value at the last valid observation strictly before t."""
    full = stat_on_valid.reindex(index)
    return full.ffill().shift(1)


def _mad(x: np.ndarray) -> float:
    return float(np.median(np.abs(x - np.median(x))))


def baseline_scale(
    prem: pd.Series,
    valid: pd.Series,
    base_win: int,
    base_min: int,
    scale_win: int,
    scale_min: int,
    floor_bps: float,
) -> pd.DataFrame:
    """prem and valid share a positional index ordered by date (one instrument)."""
    v = prem[valid & prem.notna()]
    med = v.rolling(base_win, min_periods=base_min).median()
    mad = v.rolling(scale_win, min_periods=scale_min).apply(_mad, raw=True)
    b = _prior_valid(med, prem.index)
    s = _prior_valid(1.4826 * mad, prem.index)
    s = s.where(s.isna(), np.maximum(s, floor_bps))
    dev = prem - b
    return pd.DataFrame({"b_bps": b, "s_bps": s, "dev_bps": dev, "z": dev / s})


def empirical_band(prem: pd.Series, valid: pd.Series, win: int, min_obs: int) -> pd.DataFrame:
    v = prem[valid & prem.notna()]
    lo = _prior_valid(v.rolling(win, min_periods=min_obs).quantile(0.025), prem.index)
    hi = _prior_valid(v.rolling(win, min_periods=min_obs).quantile(0.975), prem.index)
    excess = np.where(prem > hi, prem - hi, np.where(prem < lo, prem - lo, 0.0))
    excess = pd.Series(excess, index=prem.index).where(lo.notna() & hi.notna() & prem.notna())
    return pd.DataFrame(
        {"band_lo_bps": lo, "band_hi_bps": hi, "band_width_bps": hi - lo, "excess_bps": excess}
    )

"""Primary target y (H trading days ahead), sensitivity horizons and eligibility (Spec §4.7)."""

from __future__ import annotations

import numpy as np
import pandas as pd

from esw.labels.episodes import LabelParams


def targets(
    daily: pd.DataFrame, episodes: list[dict], valid: np.ndarray, p: LabelParams, horizons=(1, 3, 5)
) -> pd.DataFrame:
    n = len(daily)
    onset = np.zeros(n, bool)
    cool = np.zeros(n, bool)
    for e in episodes:
        onset[e["onset"]] = True
        cool[e["end"] + 1 : e["end"] + 1 + p.COOLDOWN] = True
    in_ep = daily["in_episode"].to_numpy()
    eligible = daily["s_lab_bps"].notna().to_numpy() & ~in_ep & ~cool & valid
    out = pd.DataFrame({"eligible": eligible, "cooldown": cool, "onset": onset})
    valid_cum = np.concatenate([[0], np.cumsum(valid.astype(int))])
    for h in horizons:
        look = h + p.PERSIST_MIN + p.GAP_BRIDGE
        y = np.full(n, np.nan)
        on_cum = np.concatenate([[0], np.cumsum(onset.astype(int))])
        for t in range(n):
            if not eligible[t]:
                continue
            a, b = t + 1, min(t + h, n - 1)
            hit = a <= b and on_cum[b + 1] - on_cum[a] > 0
            if hit:
                y[t] = 1
                continue
            end = t + look
            complete = end <= n - 1 and (valid_cum[end + 1] - valid_cum[t + 1]) == look
            if complete:
                y[t] = 0
        out[f"y_h{h}"] = y
        if h == p.HORIZON:
            out["y"] = y
            out["label_window_complete"] = ~np.isnan(y)
    return out


def fprem_timing(
    prem_close: np.ndarray, nav: np.ndarray, b: np.ndarray, thr: np.ndarray, dd_idx: list[int]
) -> bool:
    """Timing-suspect (Spec §4.10): for >= half of DD days |fprem - b| < thr, fprem against next-day NAV."""
    hits, tot = 0, 0
    for t in dd_idx:
        if t + 1 >= len(nav) or not np.isfinite(nav[t + 1]) or nav[t + 1] <= 0:
            continue
        fprem = 1e4 * (prem_close[t] / nav[t + 1] - 1)
        tot += 1
        hits += abs(fprem - b[t]) < thr[t]
    return tot > 0 and hits >= 0.5 * tot

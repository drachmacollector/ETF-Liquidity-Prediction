"""Dislocation days and episodes with baseline freeze and structural absorption (Spec §4.5-4.6; P09 T09.2).

Deliberately independent of `esw.pricing` (no shared baseline code; the formulas are re-implemented).
One chronological pass per instrument:

* history = eligible premiums so far (valid rows not inside a non-structural episode); the rows of a
  candidate run are held back ("pending") until the run either becomes an episode (they are then
  episode rows) or dies (they join history). Hence rows inside a run are judged against the pre-run
  baseline, which equals freezing the baseline at the onset retroactively.
* an episode freezes b and s at their onset values for up to FREEZE_MAX trading days; after that it is
  `structural`, its rows are absorbed into history and the baseline rolls again; it ends when DD stops
  (gap longer than GAP_BRIDGE, or a sign flip).
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
import pandas as pd


@dataclass
class LabelParams:
    ABS_FLOOR_BPS: float = 200
    K_MULT: float = 3.0
    PERSIST_MIN: int = 3
    GAP_BRIDGE: int = 1
    BASE_WIN: int = 60
    BASE_MIN: int = 40
    SCALE_WIN: int = 250
    SCALE_MIN: int = 120
    SCALE_FLOOR_BPS: float = 5
    FREEZE_MAX: int = 60
    COOLDOWN: int = 5
    HORIZON: int = 5

    @classmethod
    def from_settings(cls, p) -> LabelParams:
        return cls(**{k: getattr(p, k) for k in cls.__dataclass_fields__})


@dataclass
class _Run:
    onset: int
    sign: int
    dd_idx: list[int] = field(default_factory=list)
    rows: list[int] = field(default_factory=list)  # all rows from onset (DD and bridged)
    gap: int = 0
    confirmed: bool = False
    b: float = np.nan
    s: float = np.nan
    structural: bool = False
    release_at: int | None = None


def _stats(hist: list[float], p: LabelParams) -> tuple[float, float]:
    n = len(hist)
    b = float(np.median(hist[-p.BASE_WIN :])) if n >= p.BASE_MIN else np.nan
    if n >= p.SCALE_MIN:
        w = np.asarray(hist[-p.SCALE_WIN :])
        s = max(p.SCALE_FLOOR_BPS, 1.4826 * float(np.median(np.abs(w - np.median(w)))))
    else:
        s = np.nan
    return b, s


def label_instrument(prem: np.ndarray, valid: np.ndarray, p: LabelParams) -> tuple[pd.DataFrame, list[dict]]:
    """prem, valid: arrays in date order for one instrument. Returns (daily frame, episodes)."""
    n = len(prem)
    b_out, s_out, dd, sign, ep_id = (
        np.full(n, np.nan),
        np.full(n, np.nan),
        np.zeros(n, bool),
        np.zeros(n, int),
        np.full(n, -1),
    )
    hist: list[float] = []
    pending: list[int] = []  # rows of an unconfirmed run, held back from history
    run: _Run | None = None
    episodes: list[dict] = []

    def close_run(r: _Run) -> None:
        nonlocal pending
        if r.confirmed:
            last = r.dd_idx[-1]
            episodes.append(
                {
                    "onset": r.onset,
                    "end": last,
                    "dd_idx": list(r.dd_idx),
                    "sign": r.sign,
                    "structural": r.structural,
                }
            )
            k = len(episodes) - 1
            ep_id[r.onset : last + 1] = k
            # trailing bridged rows after the last DD day are not episode rows: they rejoin history
            for j in r.rows:
                if j > last and valid[j] and not r.structural:
                    hist.append(float(prem[j]))
        else:
            for j in r.rows:
                if valid[j]:
                    hist.append(float(prem[j]))
        pending = []

    for t in range(n):
        # structural release: absorb the episode rows into history and roll again
        if run is not None and run.confirmed and not run.structural and t - run.onset >= p.FREEZE_MAX:
            run.structural = True
            for j in run.rows:
                if valid[j]:
                    hist.append(float(prem[j]))
        if run is not None and run.confirmed and not run.structural:
            b, s = run.b, run.s
        else:
            b, s = _stats(hist, p)
        b_out[t], s_out[t] = b, s
        if not valid[t] or np.isnan(prem[t]) or np.isnan(s) or np.isnan(b):
            if run is not None:
                run.gap += 1
                run.rows.append(t)
                if run.gap > p.GAP_BRIDGE:
                    close_run(run)
                    run = None
            elif valid[t] and not np.isnan(prem[t]):
                hist.append(float(prem[t]))
            continue
        dev = prem[t] - b
        thr = max(p.ABS_FLOOR_BPS, p.K_MULT * s)
        is_dd = abs(dev) >= thr
        sg = int(np.sign(dev))
        if is_dd:
            dd[t], sign[t] = True, sg
            if run is not None and run.sign != sg:
                close_run(run)
                run = None
            if run is None:
                run = _Run(onset=t, sign=sg, b=b, s=s)
            run.dd_idx.append(t)
            run.rows.append(t)
            run.gap = 0
            if not run.confirmed and len(run.dd_idx) >= p.PERSIST_MIN:
                run.confirmed = True  # b, s already hold the onset (pre-run) values
            if run.structural:
                hist.append(float(prem[t]))
        else:
            if run is not None:
                run.gap += 1
                run.rows.append(t)
                if run.structural:
                    hist.append(float(prem[t]))
                if run.gap > p.GAP_BRIDGE:
                    close_run(run)
                    run = None
            else:
                hist.append(float(prem[t]))
    if run is not None:
        if run.confirmed:
            close_run(run)
        else:
            close_run(run)
    daily = pd.DataFrame(
        {"b_lab_bps": b_out, "s_lab_bps": s_out, "DD": dd, "sign": sign, "episode_idx": ep_id}
    )
    daily["dev_lab_bps"] = prem - daily["b_lab_bps"].to_numpy()
    daily["thr_bps"] = np.maximum(p.ABS_FLOOR_BPS, p.K_MULT * daily["s_lab_bps"].to_numpy())
    daily["in_episode"] = daily["episode_idx"] >= 0
    return daily, episodes

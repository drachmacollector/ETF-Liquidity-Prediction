"""P09: build daily labels, episodes, secondary triggers, sensitivity variants, catalogue links, event counts.

Reads `pricing_panel.parquet` (only instrument_id, date, valid, prem_bps, close, nav, volume, market,
group) and the curated catalogue tables. Never imports `esw.features` or `esw.pricing`.
"""

from __future__ import annotations

import itertools
from dataclasses import replace

import numpy as np
import pandas as pd

from esw.config import Settings, get_settings
from esw.labels.episodes import LabelParams, label_instrument
from esw.labels.targets import fprem_timing, targets

PANEL_COLS = ["instrument_id", "date", "valid", "prem_bps", "close", "nav", "volume", "market", "group"]


def _panel(settings: Settings) -> pd.DataFrame:
    return pd.read_parquet(settings.path("derived") / "pricing" / "pricing_panel.parquet", columns=PANEL_COLS)


def label_panel(
    panel: pd.DataFrame, p: LabelParams, with_secondary: bool = True
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    days, eps_rows, trig = [], [], []
    for iid, g in panel.groupby("instrument_id", sort=True):
        g = g.sort_values("date").reset_index(drop=True)
        prem = g["prem_bps"].to_numpy(dtype=float)
        valid = g["valid"].to_numpy(dtype=bool) & np.isfinite(prem)
        daily, eps = label_instrument(prem, valid, p)
        tg = targets(daily, eps, valid, p)
        d = pd.concat([g[["instrument_id", "date"]], g[["valid"]], daily, tg], axis=1)
        d["episode_id"] = np.where(d["episode_idx"] >= 0, iid + "#" + d["episode_idx"].astype(str), None)
        days.append(d.drop(columns=["episode_idx"]))
        for k, e in enumerate(eps):
            seg = slice(e["onset"], e["end"] + 1)
            dev = daily["dev_lab_bps"].to_numpy()[seg]
            pk = int(np.nanargmax(np.abs(dev)))
            eps_rows.append(
                {
                    "episode_id": f"{iid}#{k}",
                    "instrument_id": iid,
                    "group": g["group"].iloc[0],
                    "market": g["market"].iloc[0],
                    "onset": g["date"].iloc[e["onset"]],
                    "end": g["date"].iloc[e["end"]],
                    "n_days": e["end"] - e["onset"] + 1,
                    "n_dd_days": len(e["dd_idx"]),
                    "direction": "PREMIUM" if e["sign"] > 0 else "DISCOUNT",
                    "peak_dev_bps": float(dev[pk]),
                    "peak_prem_bps": float(prem[e["onset"] + pk]),
                    "peak_date": g["date"].iloc[e["onset"] + pk],
                    "structural": e["structural"],
                    "timing_suspect": fprem_timing(
                        g["close"].to_numpy(float),
                        g["nav"].to_numpy(float),
                        daily["b_lab_bps"].to_numpy(),
                        daily["thr_bps"].to_numpy(),
                        e["dd_idx"],
                    ),
                }
            )
        if with_secondary:
            trig += secondary(g, p_sec=None)
    return pd.concat(days, ignore_index=True), pd.DataFrame(eps_rows), pd.DataFrame(trig)


def _first_runs(mask: np.ndarray, run: int) -> list[int]:
    """Indices where a run of True reaches length `run` (first day of qualification)."""
    out, c = [], 0
    for i, m in enumerate(mask):
        c = c + 1 if m else 0
        if c == run:
            out.append(i)
    return out


def secondary(g: pd.DataFrame, p_sec=None) -> list[dict]:
    s = get_settings().params
    prem = g["prem_bps"].to_numpy(float)
    iid = g["instrument_id"].iloc[0]
    out = []
    for i in _first_runs(np.abs(np.nan_to_num(prem)) > s.SEC_ABS_BPS, s.SEC_RUN):
        out.append({"instrument_id": iid, "trigger_type": "sec", "trigger_date": g["date"].iloc[i]})
    for i in _first_runs(np.nan_to_num(prem) < -s.SEBI_ABS_BPS, s.SEBI_RUN):
        out.append({"instrument_id": iid, "trigger_type": "sebi", "trigger_date": g["date"].iloc[i]})
    if g["market"].iloc[0] == "IN":
        noq = (g["volume"].fillna(0) == 0).to_numpy()
        for i in _first_runs(noq, 3):
            out.append({"instrument_id": iid, "trigger_type": "noquote", "trigger_date": g["date"].iloc[i]})
    return out


def op_event_triggers(settings: Settings, panel: pd.DataFrame) -> pd.DataFrame:
    ev = pd.read_parquet(settings.path("curated") / "operational_event.parquet")
    types = {
        "creation_suspended",
        "creation_limited",
        "subscription_halt_fof",
        "subscription_halt_etf_direct",
        "industry_cap_stop",
        "trading_halt",
        "market_closure_unscheduled",
    }
    ev = ev[ev["type"].isin(types) & (ev["date_precision"] == "day")]
    ids = set(panel["instrument_id"])
    rows = []
    for r in ev.itertuples(index=False):
        for iid in r.instrument_ids.split(";"):
            if iid in ids:
                rows.append(
                    {
                        "instrument_id": iid,
                        "trigger_type": "op_event",
                        "trigger_date": pd.Timestamp(r.effective_at),
                        "event_id": r.event_id,
                    }
                )
    return pd.DataFrame(rows)


def link(
    episodes: pd.DataFrame, triggers: pd.DataFrame, settings: Settings, cal_days: dict[str, pd.DatetimeIndex]
) -> tuple[pd.DataFrame, pd.DataFrame]:
    inc = pd.read_parquet(settings.path("curated") / "incident.parquet")
    ev = pd.read_parquet(settings.path("curated") / "operational_event.parquet")

    def shift(mkt, d, k):
        days = cal_days[mkt]
        i = days.searchsorted(pd.Timestamp(d))
        return days[min(max(i + k, 0), len(days) - 1)]

    eps = episodes.copy()
    eps["incident_id"], eps["op_event_ids"] = None, None
    for i, e in eps.iterrows():
        mkt = "XNYS" if e["market"] == "US" else "XNSE"
        hits = []
        for r in inc.itertuples(index=False):
            if e["instrument_id"] not in r.instrument_ids.split(";"):
                continue
            lo = shift(mkt, r.approx_onset, -10)
            hi = shift(mkt, r.approx_end if r.approx_end else "2100-01-01", 10)
            if lo <= e["onset"] <= hi:
                hits.append(r.incident_id)
        eps.at[i, "incident_id"] = ";".join(hits) or None
        lo, hi = shift(mkt, e["onset"], -20), shift(mkt, e["end"], 5)
        evs = ev[
            (ev["effective_at"] >= lo)
            & (ev["effective_at"] <= hi)
            & ev["instrument_ids"].str.contains(e["instrument_id"], regex=False)
        ]
        eps.at[i, "op_event_ids"] = ";".join(evs["event_id"]) or None
    for col, typ in (("sec_trigger_date", "sec"), ("sebi_trigger_date", "sebi")):
        eps[col] = pd.NaT
        t = triggers[triggers["trigger_type"] == typ] if len(triggers) else triggers
        for i, e in eps.iterrows():
            x = t[
                (t["instrument_id"] == e["instrument_id"])
                & (t["trigger_date"] >= e["onset"])
                & (t["trigger_date"] <= e["end"])
            ]
            if len(x):
                eps.at[i, col] = x["trigger_date"].min()
    # incident coverage report
    rep = []
    for r in inc.itertuples(index=False):
        m = eps[eps["incident_id"].fillna("").str.contains(r.incident_id, regex=False)]
        rep.append(
            {
                "incident_id": r.incident_id,
                "near_miss": r.near_miss,
                "include_in_validation": r.include_in_validation,
                "matched_episodes": len(m),
                "first_onset": m["onset"].min() if len(m) else pd.NaT,
                "instruments": ";".join(sorted(m["instrument_id"].unique())),
            }
        )
    return eps, pd.DataFrame(rep)


def event_counts(eps: pd.DataFrame, daily: pd.DataFrame, settings: Settings) -> pd.DataFrame:
    s = settings.params
    e = eps.copy()
    e["period"] = np.where(
        e["market"] == "IN", "India", np.where(e["onset"] <= pd.Timestamp(s.DEV_END), "US dev", "US lockbox")
    )
    e["month"] = e["onset"].dt.to_period("M")
    out = (
        e.groupby("period")
        .agg(
            onsets=("episode_id", "size"),
            groups=("group", "nunique"),
            years=("onset", lambda x: x.dt.year.nunique()),
            clusters=("month", "nunique"),
            structural=("structural", "sum"),
            timing_suspect=("timing_suspect", "sum"),
        )
        .reset_index()
    )
    d = daily[daily["instrument_id"].str.startswith("US:") & (daily["date"] <= pd.Timestamp(s.DEV_END))]
    y = d["y"].dropna()
    out["us_dev_positive_rate"] = float(y.mean()) if len(y) else np.nan
    return out


def variant_grid(settings: Settings) -> list[tuple[str, LabelParams]]:
    base = LabelParams.from_settings(settings.params)
    g = settings.sensitivity_grid
    out = []
    for floor, k, pm in itertools.product(g.ABS_FLOOR_BPS, g.K_MULT, g.PERSIST_MIN):
        vid = f"floor{int(floor)}_k{k:g}_pm{pm}"
        out.append((vid, replace(base, ABS_FLOOR_BPS=floor, K_MULT=k, PERSIST_MIN=pm)))
    return out

"""P02 T02.5: trading calendars -> `data/curated/calendar.parquet`.

Markets (System Specification §4.1, §6.3 `calendar`):

* `XNYS` (US, canonical): `exchange_calendars`, 2004-01-01 to today + 30 days; early closes are `half`.
* `XNSE` (India, **preliminary**): `exchange_calendars` `XBOM` sessions (NSE and BSE share holidays),
  corrected by `reference/calendar_overrides_in.csv` (special sessions and holiday corrections,
  each checked against NSE bhavcopy presence). P05/P07 replace it with the bhavcopy-derived calendar.
* Foreign markets used for staleness features: XLON, XHKG, XTKS, XSHG, BVMF, XMEX, XIST from
  `exchange_calendars`; `XATH` (Athens; not in the library) from days with Athens General Index data
  (`reference/calendar_xath_sessions.csv`). Cairo and Moscow are not built (no feasible instrument).

One row per calendar day and market: `market, date, is_trading, session_type, source, ingested_at`.
`session_type` is `regular`, `half` or `special` on trading days and empty otherwise.
"""

from __future__ import annotations

import datetime as dt
from pathlib import Path

import exchange_calendars as xc
import pandas as pd

from esw.config import Settings, get_settings

LIBRARY_MARKETS = {
    # market code -> (exchange_calendars code, start)
    "XNYS": ("XNYS", "2004-01-01"),
    "XLON": ("XLON", "2004-01-01"),
    "XHKG": ("XHKG", "2004-01-01"),
    "XTKS": ("XTKS", "2004-01-05"),
    "XSHG": ("XSHG", "2004-01-01"),
    "BVMF": ("BVMF", "2004-01-01"),
    "XMEX": ("XMEX", "2004-01-01"),
    "XIST": ("XIST", "2004-01-01"),
}
INDIA_START = "2007-01-01"
MISSING_MARKETS = {
    "XATH": "Athens: not in exchange_calendars; sessions from Athens General Index data (GREK)",
    "XCAI": "Cairo: not in exchange_calendars; not built (EGPT infeasible, I-005)",
    "MISX": "Moscow: not in exchange_calendars; not built (RSX/ERUS infeasible, I-005)",
}


def _end_date(today: dt.date | None = None) -> pd.Timestamp:
    return pd.Timestamp(today or dt.date.today()) + pd.Timedelta(days=30)


def _library_calendar(market: str, code: str, start: str, end: pd.Timestamp) -> pd.DataFrame:
    cal = xc.get_calendar(code, start=start, end=end.strftime("%Y-%m-%d"))
    days = pd.date_range(start, end, freq="D")
    sessions = set(cal.sessions)
    early = set(cal.early_closes)
    is_trading = days.isin(list(sessions))
    session_type = [
        ("half" if d in early else "regular") if t else None for d, t in zip(days, is_trading, strict=True)
    ]
    return pd.DataFrame(
        {
            "market": market,
            "date": days,
            "is_trading": is_trading,
            "session_type": session_type,
            "source": f"exchange_calendars {xc.__version__ if hasattr(xc, '__version__') else ''} {code}".strip(),
        }
    )


def india_calendar(reference_dir: Path, end: pd.Timestamp) -> pd.DataFrame:
    """XBOM sessions plus the hand-checked overrides in `calendar_overrides_in.csv`."""
    df = _library_calendar("XNSE", "XBOM", INDIA_START, end)
    df["source"] = "exchange_calendars XBOM (preliminary)"
    ov_path = reference_dir / "calendar_overrides_in.csv"
    if ov_path.exists():
        ov = pd.read_csv(ov_path, dtype=str).fillna("")
        ov = ov[ov["apply"].str.lower() == "y"]
        idx = df.set_index("date").index
        for _, r in ov.iterrows():
            d = pd.Timestamp(r["date"])
            if d not in idx:
                continue
            i = idx.get_loc(d)
            trading = r["is_trading"].lower() == "y"
            df.loc[df.index[i], "is_trading"] = trading
            df.loc[df.index[i], "session_type"] = r["session_type"] if trading else None
            df.loc[df.index[i], "source"] = f"override: {r['reason']}"
    return df


def athens_calendar(reference_dir: Path) -> pd.DataFrame | None:
    p = reference_dir / "calendar_xath_sessions.csv"
    if not p.exists():
        return None
    s = pd.read_csv(p, parse_dates=["date"])
    days = pd.date_range(s["date"].min(), s["date"].max(), freq="D")
    trading = days.isin(s["date"])
    return pd.DataFrame(
        {
            "market": "XATH",
            "date": days,
            "is_trading": trading,
            "session_type": ["regular" if t else None for t in trading],
            "source": "Athens General Index (yfinance GD.AT) data days (preliminary)",
        }
    )


def build_calendar_frame(settings: Settings | None = None, today: dt.date | None = None) -> pd.DataFrame:
    settings = settings or get_settings()
    end = _end_date(today)
    ref = settings.path("reference")
    parts = [_library_calendar(m, c, s, end) for m, (c, s) in LIBRARY_MARKETS.items()]
    parts.append(india_calendar(ref, end))
    ath = athens_calendar(ref)
    if ath is not None:
        parts.append(ath)
    cal = pd.concat(parts, ignore_index=True)
    cal["date"] = pd.to_datetime(cal["date"]).dt.tz_localize(None).astype("datetime64[ns]")
    cal["is_trading"] = cal["is_trading"].astype(bool)
    cal["session_type"] = cal["session_type"].astype("string")
    cal["ingested_at"] = pd.Timestamp.now(tz="UTC").floor("s")
    return cal.sort_values(["market", "date"]).reset_index(drop=True)


def build_calendars(
    settings: Settings | None = None, today: dt.date | None = None
) -> tuple[pd.DataFrame, Path]:
    settings = settings or get_settings()
    cal = build_calendar_frame(settings, today)
    out = settings.path("curated") / "calendar.parquet"
    out.parent.mkdir(parents=True, exist_ok=True)
    cal.to_parquet(out, index=False)
    return cal, out


def load_calendar(settings: Settings | None = None) -> pd.DataFrame:
    settings = settings or get_settings()
    return pd.read_parquet(settings.path("curated") / "calendar.parquet")

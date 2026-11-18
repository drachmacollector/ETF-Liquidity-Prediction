"""Point-in-time stamping (System Specification §7). One function per rule; all return UTC timestamps.

| Data | `known_at` |
|---|---|
| US close/OHLCV for date t | t 16:15 America/New_York |
| US NAV, shares outstanding for t | t 20:00 America/New_York |
| India bhavcopy for t | t 18:00 Asia/Kolkata |
| AMFI NAV for t | AMFI upload timestamp (IST) when available, else t 23:59 Asia/Kolkata |
| AMFI monthly AUM | publication date, else the 10th of the next month 18:00 IST |
| FRED and other series | t + publication lag (business days), 18:00 local of the source |
| Events, capacity, corporate actions | their own `known_at` (never `effective_at`) |
"""

from __future__ import annotations

import pandas as pd


def _at(dates: pd.Series, hhmm: str, tz: str) -> pd.Series:
    d = pd.to_datetime(dates).dt.normalize()
    h, m = (int(x) for x in hhmm.split(":"))
    local = (d + pd.Timedelta(hours=h, minutes=m)).dt.tz_localize(
        tz, nonexistent="shift_forward", ambiguous=False
    )
    return local.dt.tz_convert("UTC")


def us_price_known_at(dates: pd.Series) -> pd.Series:
    return _at(dates, "16:15", "America/New_York")


def us_nav_known_at(dates: pd.Series) -> pd.Series:
    return _at(dates, "20:00", "America/New_York")


def india_bhav_known_at(dates: pd.Series) -> pd.Series:
    return _at(dates, "18:00", "Asia/Kolkata")


def amfi_nav_known_at(dates: pd.Series, uploaded_at_ist: pd.Series | None = None) -> pd.Series:
    fallback = _at(dates, "23:59", "Asia/Kolkata")
    if uploaded_at_ist is None:
        return fallback
    up = pd.to_datetime(uploaded_at_ist)
    if getattr(up.dt, "tz", None) is None:
        up = up.dt.tz_localize("Asia/Kolkata")
    up = up.dt.tz_convert("UTC")
    # an upload stamped before the NAV date is a data error: use the fallback
    bad = up < _at(dates, "00:00", "Asia/Kolkata")
    return up.where(up.notna() & ~bad, fallback)


def amfi_aum_known_at(month_end: pd.Series, published: pd.Series | None = None) -> pd.Series:
    default = _at(
        pd.to_datetime(month_end) + pd.offsets.MonthBegin(1) + pd.Timedelta(days=9), "18:00", "Asia/Kolkata"
    )
    if published is None:
        return default
    pub = _at(published, "18:00", "Asia/Kolkata")
    return pub.where(pd.to_datetime(published).notna(), default)


def series_known_at(dates: pd.Series, lag_days: int, tz: str) -> pd.Series:
    """t + lag business days, 18:00 local time of the source."""
    d = pd.to_datetime(dates) + pd.offsets.BDay(int(lag_days)) if lag_days else pd.to_datetime(dates)
    return _at(pd.Series(d), "18:00", tz)


def event_known_at(values: pd.Series) -> pd.Series:
    t = pd.to_datetime(values, utc=True)
    return t

"""P07: one test per System Specification §7 row."""

import pandas as pd

from esw.curate import pit

D = pd.Series(pd.to_datetime(["2024-01-10", "2024-07-10"]))


def test_us_price_16_15_new_york():
    k = pit.us_price_known_at(D)
    assert str(k.iloc[0]) == "2024-01-10 21:15:00+00:00" and str(k.iloc[1]) == "2024-07-10 20:15:00+00:00"


def test_us_nav_20_00_new_york():
    assert str(pit.us_nav_known_at(D).iloc[0]) == "2024-01-11 01:00:00+00:00"


def test_india_bhav_18_00_ist():
    assert str(pit.india_bhav_known_at(D).iloc[0]) == "2024-01-10 12:30:00+00:00"


def test_amfi_upload_time_and_fallback():
    up = pd.Series([pd.Timestamp("2024-01-11 02:05", tz="Asia/Kolkata"), pd.NaT])
    k = pit.amfi_nav_known_at(D, up)
    assert str(k.iloc[0]) == "2024-01-10 20:35:00+00:00"  # after-midnight upload kept
    assert str(k.iloc[1]) == "2024-07-10 18:29:00+00:00"  # 23:59 IST fallback


def test_amfi_upload_before_date_is_rejected():
    up = pd.Series([pd.Timestamp("2024-01-09 22:00", tz="Asia/Kolkata"), pd.NaT])
    assert str(pit.amfi_nav_known_at(D, up).iloc[0]) == "2024-01-10 18:29:00+00:00"


def test_series_lag_business_days():
    fri = pd.Series(pd.to_datetime(["2024-01-12"]))
    assert str(pit.series_known_at(fri, 1, "America/New_York").iloc[0]) == "2024-01-15 23:00:00+00:00"
    assert str(pit.series_known_at(fri, 0, "America/New_York").iloc[0]) == "2024-01-12 23:00:00+00:00"


def test_aum_default_10th_next_month():
    assert (
        str(pit.amfi_aum_known_at(pd.Series(pd.to_datetime(["2024-03-31"]))).iloc[0])
        == "2024-04-10 12:30:00+00:00"
    )


def test_events_use_their_own_known_at():
    k = pit.event_known_at(pd.Series(["2020-04-21T13:00:37Z"]))
    assert str(k.iloc[0]) == "2020-04-21 13:00:37+00:00"

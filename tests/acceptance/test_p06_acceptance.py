"""P06 acceptance: every catalogue series staged or marked unavailable; lags/tz recorded; coverage; roll handling."""

import pandas as pd
import pytest

from esw.config import find_repo_root, get_settings

pytestmark = pytest.mark.acceptance
ROOT = find_repo_root()
ST = get_settings()


def _cat():
    return pd.read_csv(ROOT / "reference" / "series_catalogue.csv", dtype=str, keep_default_na=False)


def test_ac_06_1_staged_or_unavailable():
    cat = _cat()
    staged = {p.stem for p in (ST.path("staged") / "series").glob("*.parquet")} | {
        "india_vix",
        "in_gold_spot",
        "in_silver_spot",
    }
    missing = cat[~cat.series_id.isin(staged) & ~cat.notes.str.contains("UNAVAILABLE|NOT STAGED")]
    assert missing.empty, missing.series_id.tolist()


def test_ac_06_2_lag_and_tz():
    cat = _cat()
    assert (cat.publication_lag_days != "").all() and (cat.tz != "").all()


def test_ac_06_3_coverage_span():
    cov = pd.read_csv(ST.path("manifests") / "coverage_series.csv")
    us = cov[
        cov.series_id.isin(["vix", "baa10y", "ust10y", "gold_usd_fut", "silver_usd_fut", "wti_fut", "usdjpy"])
    ]
    assert (pd.to_datetime(us["first"]) <= "2004-01-02").all()
    assert (ROOT / "reports" / "data" / "coverage_series.md").exists()


def test_ac_06_4_roll_flags_present():
    s = pd.read_parquet(ST.path("staged") / "series" / "wti_fut.parquet")
    assert {"roll_flag", "ret"} <= set(s.columns)


def test_ac_06_5_fx_home_markets():
    staged = {p.stem for p in (ST.path("staged") / "series").glob("*.parquet")}
    assert {"usdjpy", "usdhkd", "usdbrl", "usdmxn", "usdinr", "usdtry", "eurusd", "usd_broad"} <= staged

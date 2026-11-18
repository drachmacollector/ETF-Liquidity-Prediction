"""P06: market-series parsing, roll flags and the NAV-implied gold check (offline)."""

from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from esw.config import get_settings
from esw.ingest import parsers as P
from esw.ingest.market import flag_rolls

FX = Path(__file__).resolve().parents[1] / "fixtures"


def test_fred_missing_dot_is_null():
    raw = b"observation_date,VIXCLS\n2020-03-13,57.83\n2020-03-16,.\n2020-03-17,75.91\n"
    df = P.parse_fred_csv(raw)
    assert df["value"].isna().sum() == 1 and len(df) == 3


def test_fred_fixture():
    df = P.parse_fred_csv((FX / "mkt_fred" / "VIXCLS_trimmed.csv").read_bytes())
    assert {"date", "value"} <= set(df.columns) and df["date"].is_monotonic_increasing


def test_roll_jump_is_nulled():
    rng = np.random.default_rng(0)
    v = 100 * np.exp(np.cumsum(rng.normal(0, 0.01, 300)))
    v[200:] *= 0.85  # a roll gap
    df = flag_rolls(pd.DataFrame({"date": pd.bdate_range("2020-01-01", periods=300), "value": v}))
    assert bool(df["roll_flag"].iloc[200]) and pd.isna(df["ret"].iloc[200])
    assert df["roll_flag"].sum() <= 3


def test_nav_implied_gold_close_to_futures():
    st = get_settings().path("staged") / "series"
    if not (st / "gold_usd_navimpl.parquet").exists():
        pytest.skip("series not staged")
    g = pd.read_parquet(st / "gold_usd_navimpl.parquet")[["date", "value"]].merge(
        pd.read_parquet(st / "gold_usd_fut.parquet")[["date", "value"]], on="date", suffixes=("_nav", "_fut")
    )
    s = g.sample(200, random_state=1)
    rel = (s["value_nav"] / s["value_fut"] - 1).abs()
    assert rel.median() < 0.01 and (rel < 0.03).mean() > 0.95

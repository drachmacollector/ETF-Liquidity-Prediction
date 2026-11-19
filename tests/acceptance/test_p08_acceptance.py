"""P08 acceptance: panel for every included instrument; no premium on invalid rows; Layer 1; locks; reports."""

import pandas as pd
import pytest

from esw.config import find_repo_root, get_settings

pytestmark = pytest.mark.acceptance
ROOT = find_repo_root()
ST = get_settings()


@pytest.fixture(scope="module")
def panel():
    return pd.read_parquet(ST.path("derived") / "pricing" / "pricing_panel.parquet")


def test_ac_08_1_panel(panel):
    inst = pd.read_parquet(ST.path("curated") / "instrument.parquet")
    assert set(inst.loc[inst["include"], "instrument_id"]) <= set(panel["instrument_id"])
    assert panel.loc[~panel["valid"], "prem_bps"].isna().all()
    assert not panel.duplicated(["instrument_id", "date"]).any()


def test_ac_08_4_layer1(panel):
    m = panel[panel["group"].isin(["IN_GOLD", "IN_SILVER"])]
    assert m["lp_bps"].notna().sum() > 10_000
    assert (m.loc[m["lp_bps"].isna(), "lp_null_reason"] != "").all()


def test_ac_08_5_locks(panel):
    i = panel[panel["market"] == "IN"]
    assert {"unknown", "unconstrained"} <= set(i["lock_class"])
    feb = i[(i["date"] == "2026-02-01") & (i["group"] == "IN_SILVER")]
    assert (feb["lock_class_inferred"] == "inferred_locked").sum() >= 10


def test_ac_08_6_reports():
    for f in (
        "premium_eda.md",
        "india_nav_basis_break.md",
        "arbitrage_cost_crosscheck.md",
        "known_facts.csv",
    ):
        assert (ROOT / "reports" / "pricing" / f).exists()

"""P05 acceptance: staged Indian prices/NAV, symbol joins, special session, cross-check, reports."""

import pandas as pd
import pytest

from esw.config import find_repo_root, get_settings

pytestmark = pytest.mark.acceptance
ROOT = find_repo_root()
ST = get_settings().path("staged")


@pytest.fixture(scope="module")
def px():
    return pd.read_parquet(ST / "in_bhav" / "in_bhav_nse.parquet")


def test_ac_05_1_every_included_has_px_and_nav():
    cov = pd.read_csv(get_settings().path("manifests") / "coverage_in.csv")
    inc = cov[cov["include"]]
    assert (inc["px_days"] > 0).all() and (inc["nav_days"] > 0).all()


def test_symbol_change_joined_to_one_instrument(px):
    s = px[px["instrument_id"] == "IN:INF769K01KG6"]
    before = s[(s["date"] >= "2025-09-01") & (s["date"] < "2025-09-15")]
    after = s[(s["date"] >= "2025-09-15") & (s["date"] < "2025-10-01")]
    assert set(before["symbol"]) == {"SILVRETF"} and set(after["symbol"]) == {"SILVERAG"}


def test_special_session_2026_02_01(px):
    assert (px["date"] == pd.Timestamp("2026-02-01")).any()


def test_ac_05_3_nav_crosscheck():
    cc = pd.read_csv(ROOT / "reports" / "data" / "in_nav_crosscheck.csv")
    assert (cc["exact_agreement"] >= 0.99).all()


def test_ac_05_4_5_reports():
    for f in ("coverage_in.md", "india_calendar_reconciliation.md"):
        assert (ROOT / "reports" / "data" / f).exists()


def test_ac_05_6_mirae_metals_complete(px):
    nav = pd.read_parquet(ST / "in_nav" / "in_amfi_hist.parquet")
    for iid in ("IN:INF769K01JP9", "IN:INF769K01KG6"):
        for lo, hi in (("2025-10-01", "2025-10-20"), ("2026-01-28", "2026-02-10")):
            p = px[(px["instrument_id"] == iid) & px["date"].between(lo, hi)]
            n = nav[(nav["instrument_id"] == iid) & nav["date"].between(lo, hi)]
            assert len(p) >= 9 and len(n) >= len(p) - 1

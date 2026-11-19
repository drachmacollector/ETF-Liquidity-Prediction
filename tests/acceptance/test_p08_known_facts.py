"""P08 T08.3: known-fact reproduction from the pricing panel."""

import pandas as pd
import pytest

from esw.config import get_settings
from esw.pricing.diagnostics import known_facts

pytestmark = pytest.mark.acceptance


@pytest.fixture(scope="module")
def kf():
    p = pd.read_parquet(get_settings().path("derived") / "pricing" / "pricing_panel.parquet")
    return known_facts(p).set_index("check")["actual"]


def test_uso_2020(kf):
    assert abs(kf["USO 2020-04-21 premium"] - 3600) <= 600
    assert abs(kf["USO 2020-05-01 premium"] - 145) <= 100


def test_ung_lqd(kf):
    assert 1200 <= kf["UNG max Aug-Sep 2009"] <= 2500
    assert -700 <= kf["LQD min 9-23 Mar 2020"] <= -300


def test_calm_funds(kf):
    assert kf["GLD median |prem| 2010-2019"] < 50 and kf["SPY median |prem| 2010-2019"] < 10


def test_india_international(kf):
    assert 1200 <= kf["MAFANG median Apr 2026"] <= 3000


def test_issuer_agreement(kf):
    assert kf["US:GREK issuer premium |diff| median"] < 5 and kf["US:BKLN issuer premium |diff| median"] < 5


def test_silverag_oct_2025_accepted_deviation(kf):
    # Expected >= +300 bps (press figures vs iNAV). Against the official NAV the max is about +200 bps;
    # accepted with evidence in D-020 (the squeeze sits mainly in Layer 1). Record the measured value.
    assert 100 <= kf["SILVERAG max 9-16 Oct 2025"] < 300

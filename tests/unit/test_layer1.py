"""P08: Layer-1 unit conversion against a hand calculation."""

import pandas as pd
import pytest

from esw.pricing.layer1 import TROY_OZ_G, layer1


def test_gold_parity_hand_calc():
    dates = pd.Series(pd.to_datetime(["2024-08-01"]))
    spot = pd.DataFrame(
        {"metal": ["gold"], "date": pd.to_datetime(["2024-08-01"]), "domestic_spot_inr": [70000.0]}
    )
    g = pd.Series([2400.0], index=pd.to_datetime(["2024-07-31"]))
    fx = pd.Series([83.5], index=pd.to_datetime(["2024-07-31"]))
    duty = pd.DataFrame(
        {
            "metal": ["gold"],
            "effective_from": pd.to_datetime(["2024-07-24"]),
            "effective_to": [pd.NaT],
            "total_pct": [6.0],
            "verified": ["y"],
        }
    )
    out = layer1("gold", dates, spot, g, fx, duty)
    parity = 2400 * 83.5 / TROY_OZ_G * 10 * 0.995 * 1.06
    assert out.loc[0, "parity_inr"] == pytest.approx(parity)
    assert out.loc[0, "lp_bps"] == pytest.approx(1e4 * (70000 / parity - 1))


def test_unverified_duty_gives_null():
    dates = pd.Series(pd.to_datetime(["2013-09-02"]))
    spot = pd.DataFrame({"metal": ["gold"], "date": dates, "domestic_spot_inr": [30000.0]})
    g = pd.Series([1400.0], index=pd.to_datetime(["2013-08-30"]))
    fx = pd.Series([66.0], index=pd.to_datetime(["2013-08-30"]))
    duty = pd.DataFrame(
        {
            "metal": ["gold"],
            "effective_from": pd.to_datetime(["2013-08-13"]),
            "effective_to": [pd.Timestamp("2019-07-05")],
            "total_pct": [10.0],
            "verified": ["n"],
        }
    )
    out = layer1("gold", dates, spot, g, fx, duty)
    assert pd.isna(out.loc[0, "lp_bps"]) and out.loc[0, "lp_null_reason"] == "duty_unverified"

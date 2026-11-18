"""P08: baseline/scale/band are strictly backward-looking; premium sign and scale (synthetic)."""

import numpy as np
import pandas as pd
import pytest

from esw.pricing.band import baseline_scale, empirical_band


def _series(n=400, seed=0):
    rng = np.random.default_rng(seed)
    prem = pd.Series(rng.normal(10, 20, n))
    valid = pd.Series(True, index=prem.index)
    return prem, valid


def test_premium_sign_and_scale():
    close, nav = 101.0, 100.0
    assert 1e4 * (close / nav - 1) == pytest.approx(100.0)


def test_baseline_uses_only_prior_rows():
    prem, valid = _series()
    a = baseline_scale(prem, valid, 60, 40, 250, 120, 5)
    t = 300
    prem2 = prem.copy()
    prem2[t] = 1e6  # change today's premium
    b = baseline_scale(prem2, valid, 60, 40, 250, 120, 5)
    assert a.loc[t, "b_bps"] == b.loc[t, "b_bps"] and a.loc[t, "s_bps"] == b.loc[t, "s_bps"]
    assert a.loc[t, "b_bps"] == pytest.approx(prem.iloc[t - 60 : t].median())
    assert b.loc[t + 1, "b_bps"] == pytest.approx(prem2.iloc[t - 59 : t + 1].median())  # it enters tomorrow


def test_invalid_rows_are_skipped_and_scale_floored():
    prem = pd.Series([0.0] * 200)
    valid = pd.Series(True, index=prem.index)
    valid[150] = False
    prem[150] = 9999
    out = baseline_scale(prem, valid, 60, 40, 120, 120, 5)
    assert out.loc[199, "s_bps"] == 5 and out.loc[199, "b_bps"] == 0


def test_band_percentiles_backward():
    prem, valid = _series(600)
    out = empirical_band(prem, valid, 250, 120)
    t = 500
    window = prem.iloc[t - 250 : t]
    assert out.loc[t, "band_lo_bps"] == pytest.approx(window.quantile(0.025))
    assert out.loc[t, "band_hi_bps"] == pytest.approx(window.quantile(0.975))

"""P08: lock classification on synthetic band paths for each regime type."""

import pandas as pd

from esw.pricing.locks import classify


def _bands():
    return pd.DataFrame(
        {
            "market": "IN", "exchange": "NSE", "group": ["gold_silver", "gold_silver"],
            "effective_from": pd.to_datetime(["2007-01-01", "2026-09-07"]), "effective_to": [pd.Timestamp("2026-09-06"), pd.NaT],
            "base_rule": ["t2_nav", "t1_vwap30"], "band_init_pct": [20.0, 6.0], "verified": ["y", "y"],
        }
    )  # fmt: skip


def test_locked_near_unconstrained_t2():
    d = pd.DataFrame({"date": pd.bdate_range("2026-01-26", periods=5), "nav": [100.0] * 5})
    d["close"] = [100, 100, 80.0, 80.5, 99]  # day 3: at -20% limit; day 4: within 1%
    d["high"] = [101, 101, 80.0, 82, 100]
    d["low"] = [99, 99, 80.0, 80, 98]
    out = classify(d, _bands(), "IN_SILVER")
    assert list(out["lock_class"]) == ["unknown", "unknown", "confirmed_locked", "near_band", "unconstrained"]


def test_new_regime_uses_prior_close():
    d = pd.DataFrame(
        {
            "date": pd.bdate_range("2026-09-07", periods=3),
            "nav": [100.0] * 3,
            "close": [100.0, 94.0, 94.0],
            "high": [101, 94, 95],
            "low": [99, 94, 93],
        }
    )
    out = classify(d, _bands(), "IN_GOLD")
    assert out.loc[1, "lock_class"] == "confirmed_locked" and out.loc[1, "band_limit_down"] == 94.0


def test_unverified_regime_is_unknown():
    b = _bands().assign(verified="n")
    d = pd.DataFrame(
        {
            "date": pd.bdate_range("2025-01-06", periods=4),
            "nav": [100.0] * 4,
            "close": [100.0] * 4,
            "high": [100.0] * 4,
            "low": [100.0] * 4,
        }
    )
    assert set(classify(d, b, "IN_GOLD")["lock_class"]) == {"unknown"}

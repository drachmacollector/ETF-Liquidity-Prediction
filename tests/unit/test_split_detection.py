"""P07: a 1:8 reverse split applied only to price is detected; after the corporate action, no flag."""

import numpy as np
import pandas as pd

from esw.curate.splits import apply_actions, detect_candidates


def test_detect_and_resolve_reverse_split():
    d = pd.bdate_range("2020-04-01", periods=40)
    nav = pd.Series(np.linspace(10, 12, 40))
    close = nav * 1.001
    close[d >= "2020-04-29"] *= 8  # price on the new basis, NAV restated already
    df = pd.DataFrame({"date": d, "close": close.values, "nav": nav.values})
    c = detect_candidates(df)
    assert len(c) == 1 and c["date"].iloc[0] == pd.Timestamp("2020-04-29") and c["leg"].iloc[0] == "price"
    act = pd.DataFrame(
        {
            "ex_date": [pd.Timestamp("2020-04-29")],
            "ratio": [0.125],
            "applies_to": ["price"],
            "verified": ["y"],
        }
    )
    fixed = apply_actions(df[["date", "close"]], act, ["close"], "price")
    assert detect_candidates(fixed.merge(df[["date", "nav"]], on="date")).empty
    assert fixed["split_factor_applied"].iloc[0] == 8.0

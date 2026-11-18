"""P09: synthetic-path tests of the episode and target rules (Spec §4.5-4.7, §4.10)."""

import numpy as np
import pytest

from esw.labels.episodes import LabelParams, label_instrument
from esw.labels.targets import fprem_timing, targets

P = LabelParams()


def _calm(n=300, sd=2.0, seed=0):
    return np.random.default_rng(seed).normal(0, sd, n)


def _run(prem, valid=None):
    valid = np.ones(len(prem), bool) if valid is None else valid
    return label_instrument(prem, valid, P)


def test_single_spike_no_episode():
    x = _calm()
    x[200] = 900
    _, eps = _run(x)
    assert eps == []


def test_three_days_one_episode():
    x = _calm()
    x[200:203] = 900
    _, eps = _run(x)
    assert len(eps) == 1 and eps[0]["onset"] == 200 and eps[0]["end"] == 202


def test_gap_bridged():
    x = _calm()
    x[200:202] = 900
    x[203:205] = 900
    _, eps = _run(x)
    assert len(eps) == 1 and eps[0]["onset"] == 200 and eps[0]["end"] == 204


def test_sign_flip_not_merged():
    x = _calm()
    x[200:202] = 900
    x[203:205] = -900
    _, eps = _run(x)
    assert eps == []  # neither side reaches PERSIST_MIN on its own


def test_level_shift_structural_then_absorbed():
    x = _calm(500)
    x[200:] += 800  # persistent new level
    daily, eps = _run(x)
    assert len(eps) == 1 and eps[0]["structural"]
    assert eps[0]["onset"] == 200
    assert eps[0]["end"] < 300  # absorbed: DD stops once the baseline has rolled to the new level
    # after absorption and the end, rows are eligible again
    tg = targets(daily, eps, np.ones(len(x), bool), P)
    assert tg["eligible"].iloc[eps[0]["end"] + P.COOLDOWN + 2]


def test_y_before_onset_null_inside_and_cooldown():
    x = _calm()
    x[200:204] = 900
    daily, eps = _run(x)
    tg = targets(daily, eps, np.ones(len(x), bool), P)
    assert (tg["y"].iloc[195:200] == 1).all()
    assert tg["y"].iloc[200:204].isna().all()
    assert tg["y"].iloc[204 : 204 + P.COOLDOWN].isna().all()
    assert tg["y"].iloc[150] == 0
    assert tg["y"].iloc[194] == 0


def test_calm_spy_like_floor():
    x = _calm(1000, sd=1.4)
    daily, eps = _run(x)
    assert eps == [] and daily["thr_bps"].dropna().eq(200).all()


def test_volatile_threshold():
    rng = np.random.default_rng(3)
    x = rng.normal(0, 120 / 1.0, 400)  # MAD*1.4826 ~ sd for normal data
    daily, _ = _run(x)
    assert daily["thr_bps"].iloc[-1] == pytest.approx(3 * daily["s_lab_bps"].iloc[-1])
    assert 300 < daily["thr_bps"].iloc[-1] < 420


def test_timing_suspect():
    n = 10
    nav = np.full(n, 100.0)
    close = np.full(n, 100.0)
    close[3:6] = 105  # 500 bps premium vs same-day NAV ...
    nav[4:7] = 105  # ... fully explained by the next day's NAV
    b, thr = np.zeros(n), np.full(n, 200.0)
    assert fprem_timing(close, nav, b, thr, [3, 4, 5])
    assert not fprem_timing(close, np.full(n, 100.0), b, thr, [3, 4, 5])

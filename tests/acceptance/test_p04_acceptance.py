"""P04 acceptance: staged prices and NAV for included US instruments; coverage; checksums; manual logs."""

import hashlib
import json

import pandas as pd
import pytest

from esw.config import find_repo_root, get_settings
from esw.reference import load

pytestmark = pytest.mark.acceptance
ROOT = find_repo_root()
ST = get_settings()


def _cov():
    return pd.read_csv(ST.path("manifests") / "coverage_us.csv")


def test_ac_04_1_every_included_has_px_and_nav():
    inst = load("instruments_us")
    cov = _cov().set_index("ticker")
    for t in inst.loc[inst["include"], "ticker"]:
        assert cov.loc[t, "px_days"] > 500 and cov.loc[t, "nav_days"] > 500, t


def test_ac_04_2_coverage():
    cov = _cov()
    inc = cov[cov["include"]]
    assert (inc["px_coverage_pct"] >= 98).all() and (inc["nav_coverage_pct"] >= 95).all()


def test_ac_04_3_nav_start_near_listing():
    cov = _cov().set_index("ticker")
    for t in ("GLD", "SLV", "LQD"):
        assert cov.loc[t, "nav_start_lag_days"] <= 30
    # USO/UNG: NAV from 2009-01-02, accepted by decision D-015 (covers UNG 2009 and USO 2020)
    for t in ("USO", "UNG"):
        assert cov.loc[t, "nav_first"] <= "2009-01-02"


def test_ac_04_4_raw_checksums_unchanged():
    seen, bad = set(), []
    with open(ST.path("manifests") / "ingest_log.jsonl", encoding="utf-8") as fh:
        for line in fh:
            r = json.loads(line)
            if (
                r.get("status") != "ok"
                or not r.get("sha256")
                or not str(r.get("source", "")).startswith("us_")
            ):
                continue
            p = ROOT / str(r["path"]).replace("\\", "/")
            if p in seen or not p.exists():
                continue
            seen.add(p)
            if hashlib.sha256(p.read_bytes()).hexdigest() != r["sha256"]:
                bad.append(str(p))
    assert seen and not bad, bad[:5]


def test_ac_04_6_manual_drops_logged():
    lines = (ST.path("manifests") / "ingest_log.jsonl").read_text(encoding="utf-8").splitlines()
    manual = [json.loads(x) for x in lines if '"manual"' in x]
    paths = {str(m["path"]).replace("\\", "/") for m in manual}
    assert any("us_iss_uscf/uso-historicalnav" in p for p in paths) and any(
        "GREK-premium-discount" in p for p in paths
    )

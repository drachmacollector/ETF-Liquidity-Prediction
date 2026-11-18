"""P07 acceptance: curated tables validate; no unresolved errors; USO continuity; known_at; DATA_CUTOFF; reports."""

import pandas as pd
import pytest

from esw.config import find_repo_root, get_settings
from esw.curate.schemas import validate_curated

pytestmark = pytest.mark.acceptance
ROOT = find_repo_root()
CUR = get_settings().path("curated")


def test_ac_07_1_schemas():
    n = validate_curated(CUR)
    assert n["px_daily"] > 300_000 and n["nav_daily"] > 300_000


def test_ac_07_2_no_unresolved_errors():
    f = pd.read_parquet(CUR / "quality_flag.parquet")
    inst = pd.read_parquet(CUR / "instrument.parquet")
    inc = set(inst.loc[inst["include"], "instrument_id"])
    assert f[(f["severity"] == "error") & f["instrument_id"].isin(inc)].empty
    g = f[f["check_id"] == "gap_gt_25pct"]
    assert not g["detail"].str.contains("not annotated").any()


def test_ac_07_3_uso_continuity():
    px = pd.read_parquet(CUR / "px_daily.parquet")
    nav = pd.read_parquet(CUR / "nav_daily.parquet")
    m = px[px.instrument_id == "US:USO"].merge(
        nav[nav.instrument_id == "US:USO"], on=["instrument_id", "date"]
    )
    m = m.set_index("date")
    prem = 1e4 * (m["close"] / m["nav"] - 1)
    assert abs(prem["2020-04-21"] - 3600) < 600 and abs(prem["2020-05-01"] - 145) < 100
    assert abs(prem["2020-04-28"]) < 1000 and abs(prem["2020-04-29"]) < 1000  # no ×8 jump at the split


def test_ac_07_4_known_at_everywhere():
    for t in ("px_daily", "nav_daily", "series_daily", "capacity"):
        df = pd.read_parquet(CUR / f"{t}.parquet", columns=["known_at"])
        assert df["known_at"].notna().all(), t


def test_ac_07_5_cutoff():
    c = (CUR / "DATA_CUTOFF.txt").read_text().strip()
    assert c == str(get_settings().params.DATA_CUTOFF)


def test_ac_07_7_reports_and_india_calendar():
    for f in ("quality_report.md", "data_dictionary.md", "quality_flags.csv"):
        assert (ROOT / "reports" / "data" / f).exists()
    cal = pd.read_parquet(CUR / "calendar.parquet")
    r = cal[(cal.market == "XNSE") & (cal.date == "2026-02-01")].iloc[0]
    assert bool(r.is_trading) and r.session_type == "special"

"""P02 acceptance: reference tables validate with zero errors; required rows and MI-09 listing present."""

import re

import pandas as pd
import pytest

from esw.config import find_repo_root, get_settings
from esw.reference import load
from esw.reference.validate import run_validation

pytestmark = pytest.mark.acceptance
ROOT = find_repo_root()
TABLES = [
    "instruments_us",
    "instruments_in",
    "symbol_history",
    "nav_clock",
    "corporate_actions_manual",
    "duty_india",
    "band_regimes_india",
    "series_catalogue",
]


def test_ac_02_1_tables_exist_and_validate():
    for t in TABLES:
        assert (ROOT / "reference" / f"{t}.csv").exists(), t
    assert (ROOT / "reference" / "README.md").exists()
    rep = run_validation(get_settings(), write=False)
    assert rep.errors == [], rep.errors[:10]


def test_ac_02_3_mirae_instruments():
    ind = load("instruments_in")
    m = ind[ind["is_mirae"] & ind["include"]]
    for sym in ["GOLDETF", "SILVERAG", "MAFANG", "MASPTOP50", "MAHKTECH"]:
        assert sym in set(m["nse_symbol_current"]), sym


def test_ac_02_4_silverag_symbol_change():
    sh = load("symbol_history")
    new = sh[(sh["exchange"] == "NSE") & (sh["symbol"] == "SILVERAG")]
    assert len(new) == 1 and pd.notna(new["valid_from"].iloc[0]) and new["source_url"].iloc[0]


def test_ac_02_5_nav_clock_basis_change():
    nc = load("nav_clock")
    ind = load("instruments_in")
    metals = ind[ind["group"].isin(["IN_GOLD", "IN_SILVER"]) & ind["include"]]["instrument_id"]
    spot = nc[(nc["nav_basis"] == "in_domestic_spot")]
    assert set(metals) <= set(spot["instrument_id"])
    assert (spot["effective_from"] >= pd.Timestamp("2026-04-01")).all()


def test_ac_02_6_unverified_rows_listed_in_mi09():
    text = (ROOT / "records" / "MANUAL_ACTIONS.md").read_text(encoding="utf-8")
    listed = set(re.findall(r"\b([DB]\d+)\b", text.split("### MI-09", 1)[-1]))
    for name in ("duty_india", "band_regimes_india"):
        df = load(name)
        for note in df.loc[df["verified"] == "n", "notes"].fillna(""):
            ids = re.findall(r"MI-09 ([DB]\d+)", note)
            assert ids, f"{name}: unverified row without an MI-09 item id: {note[:60]}"
            assert set(ids) <= listed, ids


def test_ac_02_7_calendar_file():
    p = ROOT / "data" / "curated" / "calendar.parquet"
    if not p.exists():
        pytest.skip("run `esw reference build-calendars` first")
    cal = pd.read_parquet(p)
    assert {"XNYS", "XNSE"} <= set(cal["market"])

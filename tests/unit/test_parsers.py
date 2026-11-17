"""Golden-file tests: every source format confirmed in P01 parses to the expected shape (offline)."""

from pathlib import Path

import pandas as pd
import pytest

from esw.ingest import parsers as P
from esw.ingest.parsers import BHAV_COLUMNS

FX = Path(__file__).resolve().parents[1] / "fixtures"


def _read(rel: str) -> bytes:
    p = FX / rel
    if not p.exists():
        pytest.skip(f"fixture {rel} not generated yet (run `esw probe`)")
    return p.read_bytes()


def test_spdr_gold_archive():
    df = P.parse_spdr_gold_archive(_read("us_iss_spdr_gold/GLD_archive_trimmed.xlsx"))
    assert df["date"].iloc[0] == pd.Timestamp("2004-11-18")
    assert {"nav", "oz_per_share", "issuer_prem_bps", "shares_out", "total_net_assets"} <= set(df.columns)
    assert df["date"].is_monotonic_increasing
    # holiday rows ("US Holiday") are dropped
    assert df["nav"].notna().all()
    assert df.loc[0, "shares_out"] == pytest.approx(2_600_000, rel=1e-6)


def test_ishares_fund_download():
    df = P.parse_ishares_fund_download(_read("us_iss_ishares/SLV_fund_download_trimmed.xml"))
    assert list(df.columns) == ["date", "nav", "ex_dividend", "shares_out"]
    assert len(df) >= 30 and df["date"].is_monotonic_increasing
    assert df["shares_out"].notna().all() and (df["nav"] > 0).all()


def test_ssga_navhist():
    df = P.parse_ssga_navhist(_read("us_iss_ssga/JNK_navhist_trimmed.xlsx"))
    assert list(df.columns) == ["date", "nav", "shares_out", "total_net_assets"]
    assert len(df) >= 30


def test_tiingo_prices_are_raw_with_split_factor():
    df = P.parse_tiingo_prices(_read("us_px_tiingo/USO_prices_2020.json"))
    assert {"open", "high", "low", "close", "volume", "adj_close", "split_factor"} <= set(df.columns)
    row = df.loc[df["date"] == pd.Timestamp("2020-04-27")].iloc[0]
    assert row["close"] == pytest.approx(2.19)  # raw (pre-split) close
    assert row["adj_close"] == pytest.approx(17.52)  # split-adjusted
    assert (df["split_factor"] != 1).sum() == 1  # the 1-for-8 reverse split


@pytest.mark.parametrize(
    "rel,schema",
    [
        ("in_bhav_udiff/BhavCopy_NSE_CM_20251009_trimmed.csv.zip", "udiff"),
        ("in_bhav_legacy/cm19MAR2020bhav_trimmed.csv.zip", "legacy"),
    ],
)
def test_nse_bhavcopy_both_schemas(rel, schema):
    df = P.parse_nse_bhavcopy(_read(rel))
    assert list(df.columns) == BHAV_COLUMNS
    assert (df["source_schema"] == schema).all()
    gold = df[df["symbol"] == "GOLDBEES"].iloc[0]
    assert gold["isin"] == "INF204KB17I5" and gold["close"] > 0 and gold["n_trades"] > 0


def test_nse_udiff_has_mirae_silver_under_new_symbol():
    df = P.parse_nse_bhavcopy(_read("in_bhav_udiff/BhavCopy_NSE_CM_20251009_trimmed.csv.zip"))
    row = df[df["isin"] == "INF769K01KG6"].iloc[0]
    assert row["symbol"] == "SILVERAG"


def test_amfi_navall():
    df = P.parse_amfi_navall(_read("in_amfi_navall/NAVAll_trimmed.txt"))
    row = df[df["isin_growth"] == "INF769K01KG6"].iloc[0]
    assert row["amfi_scheme_code"] == 151779 and row["nav"] > 0
    assert "Silver ETF" in row["category"]


def test_amfi_historical_period_upload_time_is_ist():
    df = P.parse_amfi_historical_period(_read("in_amfi_hist/hist_151779_trimmed.json"))
    assert df["date"].iloc[0] == pd.Timestamp("2023-06-12")
    assert str(df["uploaded_at_ist"].dt.tz) == "Asia/Kolkata"
    assert (df["uploaded_at_ist"].dt.hour >= 18).all()  # NAVs are uploaded in the evening IST


def test_mfapi():
    df = P.parse_mfapi(_read("in_mfapi/mfapi_151779_trimmed.json"))
    assert list(df.columns) == ["amfi_scheme_code", "isin_growth", "date", "nav"]
    assert (df["amfi_scheme_code"] == 151779).all()


def test_fred_missing_values():
    df = P.parse_fred_csv(_read("mkt_fred/VIXCLS_trimmed.csv"))
    assert df["value"].isna().sum() == 1  # the "." row
    assert df["series_code"].iloc[0] == "VIXCLS"


def test_eia_xls():
    df = P.parse_eia_xls(_read("mkt_eia/RCLC1_trimmed.xlsx"))
    assert df["date"].iloc[0] == pd.Timestamp("1983-04-04")
    assert df["value"].iloc[0] == pytest.approx(29.44)

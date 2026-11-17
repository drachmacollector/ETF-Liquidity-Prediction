"""P02: reference schemas reject broken rows; calendars have the required properties (offline)."""

from __future__ import annotations

import datetime as dt

import pandas as pd
import pandera.errors as pe
import pytest

from esw.reference import load
from esw.reference.bootstrap_us import isin_from_cusip
from esw.reference.loaders import read_raw, validate_frame
from esw.reference.validate import Report, _periods_ok


def _broken(name: str, mutate) -> pd.DataFrame:
    df = read_raw(name)
    return mutate(df.copy())


def _fails(name: str, df: pd.DataFrame) -> None:
    with pytest.raises((pe.SchemaErrors, ValueError)):
        validate_frame(name, df)


@pytest.mark.parametrize(
    "name",
    [
        "instruments_us",
        "instruments_in",
        "symbol_history",
        "nav_clock",
        "corporate_actions_manual",
        "duty_india",
        "band_regimes_india",
        "series_catalogue",
        "calendar_overrides_in",
    ],
)
def test_tables_validate(name):
    df = load(name)
    assert len(df) > 0


def test_duplicate_isin_rejected():
    def mut(df):
        df.loc[1, "isin"] = df.loc[0, "isin"]
        return df

    _fails("instruments_in", _broken("instruments_in", mut))


def test_duplicate_instrument_id_rejected():
    def mut(df):
        return pd.concat([df, df.iloc[[0]]], ignore_index=True)

    _fails("instruments_us", _broken("instruments_us", mut))


def test_missing_source_for_included_row_rejected():
    def mut(df):
        i = df.index[df["include"] == "true"][0]
        df.loc[i, "source_url"] = ""
        return df

    _fails("instruments_us", _broken("instruments_us", mut))


def test_missing_source_for_verified_duty_rejected():
    def mut(df):
        i = df.index[df["verified"] == "y"][0]
        df.loc[i, "source_url"] = ""
        return df

    _fails("duty_india", _broken("duty_india", mut))


def test_excluded_without_reason_rejected():
    def mut(df):
        i = df.index[df["include"] == "false"][0]
        df.loc[i, "exclude_reason"] = ""
        return df

    _fails("instruments_in", _broken("instruments_in", mut))


def test_bad_codes_rejected():
    _fails(
        "instruments_us",
        _broken("instruments_us", lambda d: d.assign(group=d["group"].where(d.index != 0, "US_FOO"))),
    )
    _fails(
        "nav_clock",
        _broken("nav_clock", lambda d: d.assign(nav_basis=d["nav_basis"].where(d.index != 0, "noon"))),
    )


def test_reversed_dates_rejected():
    def mut(df):
        df.loc[0, "effective_to"] = "2000-01-01"
        return df

    _fails("duty_india", _broken("duty_india", mut))


def test_overlapping_periods_detected():
    d = pd.DataFrame(
        {
            "metal": ["gold", "gold"],
            "effective_from": pd.to_datetime(["2020-01-01", "2020-06-01"]),
            "effective_to": pd.to_datetime(["2020-12-31", pd.NaT]),
        }
    )
    rep = Report()
    _periods_ok(d, ["metal"], "duty_india", rep)
    assert any("overlap" in e for e in rep.errors)


def test_gap_detected():
    d = pd.DataFrame(
        {
            "metal": ["gold", "gold"],
            "effective_from": pd.to_datetime(["2020-01-01", "2021-02-01"]),
            "effective_to": pd.to_datetime(["2020-12-31", pd.NaT]),
        }
    )
    rep = Report()
    _periods_ok(d, ["metal"], "duty_india", rep)
    assert any("gap" in e for e in rep.errors)


def test_isin_check_digit():
    assert isin_from_cusip("464287234") == "US4642872349"  # EEM (iShares screener)
    assert isin_from_cusip("46428Q109") == "US46428Q1094"  # SLV


def test_required_rows_present():
    us = load("instruments_us").set_index("ticker")
    assert us.loc["GLD", "legal_form"] == "grantor_trust" and us.loc["GLD", "rule_6c11"] == "n"
    assert not us.loc["RSX", "include"]
    ind = load("instruments_in")
    mirae = ind[ind["is_mirae"]]
    for sym in ["GOLDETF", "SILVERAG", "MAFANG", "MASPTOP50", "MAHKTECH"]:
        assert sym in set(mirae["nse_symbol_current"]), sym
    sh = load("symbol_history")
    row = sh[(sh["symbol"] == "SILVERAG") & (sh["exchange"] == "NSE")]
    assert row["valid_from"].iloc[0] == pd.Timestamp("2025-09-15")
    old = sh[(sh["symbol"] == "SILVRETF") & (sh["exchange"] == "NSE")]
    assert old["valid_to"].iloc[0] == pd.Timestamp("2025-09-14")
    nc = load("nav_clock")
    silver = nc[nc["instrument_id"] == "IN:INF769K01KG6"].set_index("nav_basis")
    assert silver.loc["in_import_parity", "effective_to"] == pd.Timestamp("2026-03-31")
    assert silver.loc["in_domestic_spot", "effective_from"] == pd.Timestamp("2026-04-01")
    ca = load("corporate_actions_manual")
    uso = ca[(ca["instrument_id"] == "US:USO")]
    assert uso["ex_date"].iloc[0] == pd.Timestamp("2020-04-29") and uso["ratio"].iloc[0] == pytest.approx(
        0.125
    )


# --------------------------------------------------------------------------- calendars
@pytest.fixture(scope="module")
def cal():
    from esw.reference.calendars import build_calendar_frame

    return build_calendar_frame(today=dt.date(2026, 11, 17)).set_index(["market", "date"])


def test_india_special_session(cal):
    r = cal.loc[("XNSE", pd.Timestamp("2026-02-01"))]
    assert bool(r["is_trading"]) and r["session_type"] == "special"


def test_us_good_friday_closed(cal):
    assert not bool(cal.loc[("XNYS", pd.Timestamp("2020-04-10")), "is_trading"])


def test_us_day_after_thanksgiving_half(cal):
    for d in ["2019-11-29", "2025-11-28"]:
        r = cal.loc[("XNYS", pd.Timestamp(d))]
        assert bool(r["is_trading"]) and r["session_type"] == "half"


def test_athens_2015_closure(cal):
    assert not bool(cal.loc[("XATH", pd.Timestamp("2015-07-15")), "is_trading"])
    assert bool(cal.loc[("XATH", pd.Timestamp("2015-08-03")), "is_trading"])


def test_calendar_span(cal):
    us = cal.loc["XNYS"]
    assert us.index.min() == pd.Timestamp("2004-01-01")
    assert us.index.max() >= pd.Timestamp("2026-12-17")
    assert cal.loc["XNSE"].index.min() == pd.Timestamp("2007-01-01")

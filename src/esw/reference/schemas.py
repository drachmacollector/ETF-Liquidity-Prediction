"""Pandera schemas for the hand-built reference tables (P02 T02.10).

Tables are stored as UTF-8 CSV in `reference/`. `esw.reference.loaders.load()` reads them as strings,
converts types with `TYPES`, and validates them with `SCHEMAS`. Row-level rules that pandera's
column checks cannot express (e.g., `source_url` required when `include` is true) are wide checks.
"""

from __future__ import annotations

import pandas as pd
import pandera.pandas as pa
from pandera.pandas import Check, Column, DataFrameSchema

US_GROUPS = ["US_COMM_PHYS", "US_COMM_FUT", "US_BOND", "US_INTL", "US_CTRL"]
IN_GROUPS = ["IN_GOLD", "IN_SILVER", "IN_INTL", "IN_DEBT", "IN_CTRL"]
LEGAL_FORMS = ["open_end", "uit", "grantor_trust", "commodity_pool", "etn"]
YNU = ["y", "n", "unknown"]
YN = ["y", "n"]
NAV_BASES = [
    "us_close_16et",
    "lbma_pm",
    "lbma_silver_noon",
    "futures_settle",
    "foreign_close",
    "evaluated_bond",
    "in_import_parity",
    "in_domestic_spot",
    "in_close",
]
EXCHANGES = ["NSE", "BSE", "NYSEARCA", "NYSE", "NASDAQ", "CBOE"]
CA_TYPES = ["split", "reverse_split", "consolidation", "unit_split", "bonus"]
APPLIES_TO = ["price", "nav", "both"]
BAND_GROUPS = ["gold_silver", "equity_debt", "overnight", "liquid", "international"]
BASE_RULES = ["t2_nav", "t1_nav", "t1_vwap30"]
SESSION_TYPES = ["regular", "special", "half"]

# column -> kind, used by loaders to convert the string CSV
TYPES: dict[str, dict[str, str]] = {
    "instruments_us": {
        "listing_date": "date",
        "delisting_date": "date",
        "include": "bool",
        "verified_on": "date",
    },
    "instruments_in": {
        "amfi_scheme_code": "Int64",
        "is_mirae": "bool",
        "listing_date": "date",
        "inception_date": "date",
        "creation_unit_units": "float",
        "include": "bool",
        "verified_on": "date",
    },
    "symbol_history": {"valid_from": "date", "valid_to": "date"},
    "nav_clock": {"effective_from": "date", "effective_to": "date"},
    "corporate_actions_manual": {"ex_date": "date", "ratio": "float"},
    "duty_india": {
        "effective_from": "date",
        "effective_to": "date",
        "bcd_pct": "float",
        "aidc_pct": "float",
        "sws_pct": "float",
        "other_pct": "float",
        "total_pct": "float",
    },
    "band_regimes_india": {
        "effective_from": "date",
        "effective_to": "date",
        "band_init_pct": "float",
        "flex_step_pct": "float",
        "flex_max": "float",
    },
    "series_catalogue": {"publication_lag_days": "int", "start_expected": "date"},
    "calendar_overrides_in": {"date": "date"},
}


def _nonempty(s: pd.Series) -> pd.Series:
    return s.fillna("").astype(str).str.strip() != ""


def _source_when(flag_col: str, flag_true) -> Check:
    def check(df: pd.DataFrame) -> pd.Series:
        need = df[flag_col] == flag_true
        return ~need | _nonempty(df["source_url"])

    return Check(check, element_wise=False, error=f"source_url required when {flag_col} = {flag_true}")


def _reason_when_excluded() -> Check:
    return Check(
        lambda df: df["include"] | _nonempty(df["exclude_reason"]),
        element_wise=False,
        error="exclude_reason required when include = false",
    )


def _ordered(start: str, end: str, strict: bool = False) -> Check:
    def check(df: pd.DataFrame) -> pd.Series:
        ok = df[end].isna() | df[start].isna()
        return ok | ((df[start] < df[end]) if strict else (df[start] <= df[end]))

    return Check(check, element_wise=False, error=f"{start} must be {'<' if strict else '<='} {end}")


def _unique(cols: list[str]) -> Check:
    return Check(
        lambda df: ~df.duplicated(subset=cols, keep=False), element_wise=False, error=f"duplicate key {cols}"
    )


DATE = pa.DateTime
OPT_STR = Column(str, nullable=True, required=True)

SCHEMAS: dict[str, DataFrameSchema] = {
    "instruments_us": DataFrameSchema(
        {
            "instrument_id": Column(str, Check.str_matches(r"^US:[A-Z.]+$"), unique=True),
            "market": Column(str, Check.equal_to("US")),
            "ticker": Column(str, unique=True),
            "isin": Column(str, Check.str_matches(r"^US[0-9A-Z]{9}[0-9]$"), nullable=True),
            "cusip": Column(str, Check.str_length(9, 9), nullable=True),
            "name": Column(str),
            "issuer": Column(str),
            "group": Column(str, Check.isin(US_GROUPS)),
            "subgroup": Column(str),
            "underlying": Column(str),
            "legal_form": Column(str, Check.isin(LEGAL_FORMS)),
            "rule_6c11": Column(str, Check.isin(YNU)),
            "listing_date": Column(DATE),
            "delisting_date": Column(DATE, nullable=True),
            "currency": Column(str, Check.equal_to("USD")),
            "nav_source_id": Column(str),
            "px_source_id": Column(str),
            "shares_source_id": Column(str, nullable=True),
            "include": Column(bool),
            "exclude_reason": Column(str, nullable=True),
            "notes": Column(str, nullable=True),
            "source_url": Column(str, nullable=True),
            "verified_by": Column(str),
            "verified_on": Column(DATE),
        },
        checks=[
            _source_when("include", True),
            _reason_when_excluded(),
            _ordered("listing_date", "delisting_date"),
        ],
        strict=False,
    ),
    "instruments_in": DataFrameSchema(
        {
            "instrument_id": Column(str, Check.str_matches(r"^IN:IN[FE][0-9A-Z]{9}$"), unique=True),
            "market": Column(str, Check.equal_to("IN")),
            "isin": Column(str, Check.str_matches(r"^IN[FE][0-9A-Z]{9}$"), unique=True),
            "amfi_scheme_code": Column("Int64", nullable=True),
            "name": Column(str),
            "issuer": Column(str),
            "is_mirae": Column(bool),
            "group": Column(str, Check.isin(IN_GROUPS)),
            "subgroup": Column(str, nullable=True),
            "underlying": Column(str, nullable=True),
            "benchmark_name": Column(str, nullable=True),
            "nse_symbol_current": Column(str, nullable=True),
            "bse_code": Column(str, nullable=True),
            "listing_date": Column(DATE, nullable=True),
            "inception_date": Column(DATE, nullable=True),
            "creation_unit_units": Column(float, nullable=True),
            "include": Column(bool),
            "exclude_reason": Column(str, nullable=True),
            "notes": Column(str, nullable=True),
            "source_url": Column(str, nullable=True),
            "verified_by": Column(str),
            "verified_on": Column(DATE),
        },
        checks=[
            _source_when("include", True),
            _reason_when_excluded(),
            Check(
                lambda df: ~df["include"] | df["amfi_scheme_code"].notna(),
                element_wise=False,
                error="included Indian instruments need an AMFI scheme code",
            ),
        ],
        strict=False,
    ),
    "symbol_history": DataFrameSchema(
        {
            "instrument_id": Column(str, Check.str_matches(r"^(US|IN):")),
            "exchange": Column(str, Check.isin(EXCHANGES)),
            "symbol": Column(str),
            "isin": Column(str, nullable=True),
            "valid_from": Column(DATE, nullable=True),
            "valid_to": Column(DATE, nullable=True),
            "source_url": Column(str),
        },
        checks=[_unique(["instrument_id", "exchange", "valid_from"]), _ordered("valid_from", "valid_to")],
        strict=False,
    ),
    "nav_clock": DataFrameSchema(
        {
            "instrument_id": Column(str, Check.str_matches(r"^(US|IN):")),
            "effective_from": Column(DATE),
            "effective_to": Column(DATE, nullable=True),
            "nav_basis": Column(str, Check.isin(NAV_BASES)),
            "valuation_time_local": Column(str, Check.str_matches(r"^\d{2}:\d{2}$"), nullable=True),
            "valuation_tz": Column(str, nullable=True),
            "source_url": Column(str),
            "notes": Column(str, nullable=True),
        },
        checks=[_unique(["instrument_id", "effective_from"]), _ordered("effective_from", "effective_to")],
        strict=False,
    ),
    "corporate_actions_manual": DataFrameSchema(
        {
            "instrument_id": Column(str, Check.str_matches(r"^(US|IN):")),
            "ex_date": Column(DATE),
            "type": Column(str, Check.isin(CA_TYPES)),
            "ratio": Column(float, Check.gt(0)),
            "applies_to": Column(str, Check.isin(APPLIES_TO)),
            "verified": Column(str, Check.isin(YN)),
            "source_url": Column(str, nullable=True),
            "notes": Column(str, nullable=True),
        },
        checks=[_unique(["instrument_id", "ex_date", "type", "applies_to"]), _source_when("verified", "y")],
        strict=False,
    ),
    "duty_india": DataFrameSchema(
        {
            "metal": Column(str, Check.isin(["gold", "silver"])),
            "effective_from": Column(DATE),
            "effective_to": Column(DATE, nullable=True),
            "bcd_pct": Column(float, Check.in_range(0, 100), nullable=True),
            "aidc_pct": Column(float, Check.in_range(0, 100), nullable=True),
            "sws_pct": Column(float, Check.in_range(0, 100), nullable=True),
            "other_pct": Column(float, Check.in_range(0, 100), nullable=True),
            "total_pct": Column(float, Check.in_range(0, 100), nullable=True),
            "verified": Column(str, Check.isin(YN)),
            "source_url": Column(str, nullable=True),
            "notes": Column(str, nullable=True),
        },
        checks=[
            _unique(["metal", "effective_from"]),
            _ordered("effective_from", "effective_to"),
            _source_when("verified", "y"),
            Check(
                lambda df: (df["verified"] == "n") | df["total_pct"].notna(),
                element_wise=False,
                error="verified rows need total_pct",
            ),
        ],
        strict=False,
    ),
    "band_regimes_india": DataFrameSchema(
        {
            "market": Column(str, Check.equal_to("IN")),
            "exchange": Column(str, Check.isin(["NSE", "BSE"])),
            "group": Column(str, Check.isin(BAND_GROUPS)),
            "effective_from": Column(DATE),
            "effective_to": Column(DATE, nullable=True),
            "base_rule": Column(str, Check.isin(BASE_RULES)),
            "band_init_pct": Column(float, Check.gt(0)),
            "flex_step_pct": Column(float, nullable=True),
            "flex_max": Column(float, nullable=True),
            "cooling_off_note": Column(str, nullable=True),
            "verified": Column(str, Check.isin(YN)),
            "source_url": Column(str, nullable=True),
        },
        checks=[
            _unique(["market", "exchange", "group", "effective_from"]),
            _ordered("effective_from", "effective_to"),
            _source_when("verified", "y"),
        ],
        strict=False,
    ),
    "series_catalogue": DataFrameSchema(
        {
            "series_id": Column(str, unique=True),
            "description": Column(str),
            "source_id": Column(str),
            "source_code": Column(str),
            "unit": Column(str),
            "frequency": Column(str),
            "publication_lag_days": Column(int, Check.ge(0)),
            "tz": Column(str),
            "start_expected": Column(DATE, nullable=True),
            "notes": Column(str, nullable=True),
        },
        strict=False,
    ),
    "calendar_overrides_in": DataFrameSchema(
        {
            "date": Column(DATE, unique=True),
            "is_trading": Column(str, Check.isin(YN)),
            "session_type": Column(str, Check.isin(SESSION_TYPES), nullable=True),
            "reason": Column(str),
            "apply": Column(str, Check.isin(YN)),
            "verified": Column(str, Check.isin(YN)),
            "source_url": Column(str),
        },
        strict=False,
    ),
}

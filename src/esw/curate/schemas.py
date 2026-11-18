"""Pandera schemas for the curated store (System Specification §6.3; P07 AC-07.1)."""

from __future__ import annotations

import pandas as pd
import pandera.pandas as pa
from pandera.pandas import Check, Column, DataFrameSchema


def _unique(cols):
    return Check(lambda df: ~df.duplicated(subset=cols), element_wise=False, error=f"duplicate key {cols}")


def _tz_utc(s: pd.Series) -> bool:
    return str(getattr(s.dt, "tz", None)) == "UTC"


KNOWN_AT = Column(checks=Check(_tz_utc, element_wise=False, error="known_at must be UTC"), nullable=False)

CURATED: dict[str, DataFrameSchema] = {
    "px_daily": DataFrameSchema(
        {
            "instrument_id": Column(str),
            "date": Column(pa.DateTime),
            "close": Column(float, Check.gt(0), nullable=True),
            "volume": Column(float, Check.ge(0), nullable=True),
            "known_at": KNOWN_AT,
        },
        checks=[_unique(["instrument_id", "date"])],
        strict=False,
    ),
    "nav_daily": DataFrameSchema(
        {
            "instrument_id": Column(str),
            "date": Column(pa.DateTime),
            "nav": Column(float, Check.gt(0)),
            "known_at": KNOWN_AT,
        },
        checks=[_unique(["instrument_id", "date"])],
        strict=False,
    ),
    "series_daily": DataFrameSchema(
        {"series_id": Column(str), "date": Column(pa.DateTime), "value": Column(float), "known_at": KNOWN_AT},
        checks=[_unique(["series_id", "date"])],
        strict=False,
    ),
    "calendar": DataFrameSchema(
        {"market": Column(str), "date": Column(pa.DateTime), "is_trading": Column(bool)},
        checks=[_unique(["market", "date"])],
        strict=False,
    ),
    "instrument": DataFrameSchema(
        {"instrument_id": Column(str, unique=True), "include": Column(bool)}, strict=False
    ),
    "operational_event": DataFrameSchema({"event_id": Column(str, unique=True)}, strict=False),
    "capacity": DataFrameSchema({"known_at": KNOWN_AT}, strict=False),
}


def validate_curated(cur_dir) -> dict[str, int]:
    out = {}
    for name, schema in CURATED.items():
        df = pd.read_parquet(cur_dir / f"{name}.parquet")
        schema.validate(df, lazy=True)
        out[name] = len(df)
    return out

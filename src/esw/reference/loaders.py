"""Load and validate reference tables: `esw.reference.load(name)` (P02 T02.10)."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from esw.config import Settings, get_settings
from esw.reference.schemas import SCHEMAS, TYPES

TABLES = list(SCHEMAS)


def table_path(name: str, settings: Settings | None = None) -> Path:
    settings = settings or get_settings()
    return settings.path("reference") / f"{name}.csv"


def coerce(name: str, df: pd.DataFrame) -> pd.DataFrame:
    """Convert a string-typed frame to the table's types. Empty strings become missing values."""
    df = df.copy()
    for c in df.columns:
        df[c] = df[c].where(df[c].astype(str).str.strip() != "", None)
    for col, kind in TYPES.get(name, {}).items():
        if col not in df.columns:
            continue
        if kind == "date":
            df[col] = pd.to_datetime(df[col], format="%Y-%m-%d", errors="raise")
        elif kind == "Int64":
            df[col] = pd.to_numeric(df[col], errors="raise").astype("Int64")
        elif kind == "int":
            df[col] = pd.to_numeric(df[col], errors="raise").astype("int64")
        elif kind == "float":
            df[col] = pd.to_numeric(df[col], errors="raise").astype("float64")
        elif kind == "bool":
            vals = df[col].astype(str).str.lower()
            if not vals.isin(["true", "false"]).all():
                bad = sorted(set(vals) - {"true", "false"})
                raise ValueError(f"{name}.{col}: booleans must be true/false, found {bad}")
            df[col] = vals == "true"
    return df


def read_raw(name: str, settings: Settings | None = None, path: Path | None = None) -> pd.DataFrame:
    return pd.read_csv(path or table_path(name, settings), dtype=str, keep_default_na=False, encoding="utf-8")


def validate_frame(name: str, df: pd.DataFrame) -> pd.DataFrame:
    """Coerce and validate a string frame; raises pandera.errors.SchemaErrors (lazy) on failure."""
    typed = coerce(name, df)
    return SCHEMAS[name].validate(typed, lazy=True)


def load(name: str, settings: Settings | None = None, path: Path | None = None) -> pd.DataFrame:
    """Return the validated reference table `name` (e.g. "instruments_us")."""
    if name not in SCHEMAS:
        raise KeyError(f"unknown reference table {name!r}; known: {TABLES}")
    return validate_frame(name, read_raw(name, settings, path))

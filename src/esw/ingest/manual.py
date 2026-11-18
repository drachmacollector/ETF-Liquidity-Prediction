"""Register files the user dropped in `data/manual_drop/<source_id>/` (MI-04, MI-05).

Each new file (by SHA-256) gets one `status = manual` line in the ingest log with the rows parsed
and the date range, so every manual file is traceable (System Specification §6.2). Files whose
format has no parser are still logged, with `rows_parsed = null`.
"""

from __future__ import annotations

import json
import re
from collections.abc import Callable
from pathlib import Path

import pandas as pd

from esw.config import Settings, get_settings
from esw.ingest import parsers as P
from esw.paths import ingest_log_path
from esw.runlog import append_ingest_log, iso_utc, sha256_file

# (source folder, filename regex) -> (parser, instrument-id builder)
_PARSERS: list[tuple[str, str, Callable[[bytes], pd.DataFrame], Callable[[str], str | None]]] = [
    (
        "us_iss_uscf",
        r"^([a-z]+)-historicalnav-\d{8}\.csv$",
        P.parse_uscf_navhist,
        lambda m: f"US:{m.upper()}",
    ),
    (
        "us_iss_globalx",
        r"^([A-Z]+)-premium-discount-.*\.csv$",
        P.parse_globalx_premium_discount,
        lambda m: f"US:{m}",
    ),
    (
        "in_spot",
        r"^MCX_(GOLD|SILVER)_SPOT.*\.xls$",
        P.parse_mcx_spot,
        lambda m: f"SERIES:in_{m.lower()}_spot",
    ),
]


def _logged_hashes(log_path: Path) -> set[str]:
    if not log_path.exists():
        return set()
    out = set()
    with open(log_path, encoding="utf-8") as fh:
        for line in fh:
            try:
                out.add(json.loads(line).get("sha256"))
            except json.JSONDecodeError:
                continue
    return out


def describe(path: Path, source: str) -> dict:
    """Parse a dropped file if a parser matches; return rows/date range/instrument."""
    for src, pattern, parser, iid in _PARSERS:
        m = re.match(pattern, path.name)
        if src == source and m:
            df = parser(path.read_bytes())
            first, last, n = P.date_span(df)
            return {"instrument_id": iid(m.group(1)), "rows_parsed": n, "date_min": first, "date_max": last}
    return {"instrument_id": None, "rows_parsed": None, "date_min": None, "date_max": None}


def register_manual_drops(settings: Settings | None = None, run_id: str = "") -> list[dict]:
    """Log every not-yet-logged file under `data/manual_drop/`. Returns the new records."""
    settings = settings or get_settings()
    root = settings.root
    assert root is not None
    drop = settings.path("manual_drop")
    log_path = ingest_log_path(settings)
    seen = _logged_hashes(log_path)
    new = []
    for path in sorted(p for p in drop.rglob("*") if p.is_file()):
        digest = sha256_file(path)
        if digest in seen:
            continue
        source = path.relative_to(drop).parts[0]
        err = None
        try:
            info = describe(path, source)
        except Exception as exc:  # noqa: BLE001 - record any parse failure
            info = {"instrument_id": None, "rows_parsed": None, "date_min": None, "date_max": None}
            err = f"{type(exc).__name__}: {exc}"
        rec = {
            "ts_utc": iso_utc(),
            "source": f"manual:{source}",
            "url": None,
            "path": path.relative_to(root).as_posix(),
            "sha256": digest,
            "bytes": path.stat().st_size,
            "http_status": None,
            "status": "manual",
            "error": err,
            "run_id": run_id,
            **info,
        }
        append_ingest_log(rec, log_path)
        seen.add(digest)
        new.append(rec)
    return new

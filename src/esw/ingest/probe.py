"""P01 probe framework: small, polite checks of every source, recorded in a probe matrix.

Each probe saves the raw responses under `data/raw/_probes/<source_id>/`, logs each file in the
ingestion manifest, and returns one or more `ProbeRow`s. `run_probes` writes/merges
`reports/data/source_probe_matrix.csv` (keyed by source_id + instrument_id).
"""

from __future__ import annotations

import csv
import logging
from collections.abc import Callable
from dataclasses import asdict, dataclass, fields
from pathlib import Path

from esw.config import Settings, get_settings
from esw.ingest.http import PoliteSession
from esw.runlog import append_ingest_log, iso_utc, sha256_file

log = logging.getLogger(__name__)

STATUSES = ("OK", "PARTIAL", "BLOCKED", "MANUAL_ONLY", "NOT_FOUND")


@dataclass
class ProbeRow:
    source_id: str
    scope: str
    instrument_id: str = ""
    url_pattern: str = ""
    method: str = ""  # api | file | scrape | manual | library
    auth: str = "none"  # none | key | login
    status: str = ""
    history_start: str = ""
    history_end: str = ""
    rows: int | str = ""
    fields: str = ""
    adjusted: str = "unknown"  # y | n | split_only | unknown
    rate_limit_note: str = ""
    tos_url: str = ""
    tos_summary: str = ""
    notes: str = ""

    def __post_init__(self) -> None:
        if self.status not in STATUSES:
            raise ValueError(f"invalid probe status {self.status!r}")


MATRIX_COLUMNS = [f.name for f in fields(ProbeRow)]


class ProbeRunner:
    """Shared helpers for probes: polite HTTP, raw saving with manifest logging, fixtures."""

    def __init__(self, settings: Settings | None = None, run_id: str = "") -> None:
        self.settings = settings or get_settings()
        self.http = PoliteSession(self.settings)
        self.raw_dir = self.settings.path("raw") / "_probes"
        self.fixtures_dir = self.settings.root / "tests" / "fixtures"  # type: ignore[operator]
        self.run_id = run_id

    def save_raw(
        self,
        source_id: str,
        name: str,
        content: bytes,
        *,
        url: str = "",
        http_status: int | None = None,
        instrument_id: str = "",
        status: str = "ok",
        error: str | None = None,
    ) -> Path:
        d = self.raw_dir / source_id
        d.mkdir(parents=True, exist_ok=True)
        path = d / name
        path.write_bytes(content)
        append_ingest_log(
            {
                "ts_utc": iso_utc(),
                "source": source_id,
                "instrument_id": instrument_id,
                "url": url,
                "path": str(path.relative_to(self.settings.root)),  # type: ignore[arg-type]
                "sha256": sha256_file(path),
                "bytes": len(content),
                "http_status": http_status,
                "status": status,
                "error": error,
                "run_id": self.run_id,
            },
            self.settings.path("manifests") / "ingest_log.jsonl",
        )
        return path

    def log_failure(self, source_id: str, url: str, error: str, http_status: int | None = None) -> None:
        append_ingest_log(
            {
                "ts_utc": iso_utc(),
                "source": source_id,
                "url": url,
                "path": "",
                "sha256": "",
                "http_status": http_status,
                "status": "failed",
                "error": error[:500],
                "run_id": self.run_id,
            },
            self.settings.path("manifests") / "ingest_log.jsonl",
        )

    def save_fixture(self, source_id: str, name: str, content: bytes) -> Path:
        d = self.fixtures_dir / source_id
        d.mkdir(parents=True, exist_ok=True)
        path = d / name
        path.write_bytes(content)
        return path


ProbeFn = Callable[[ProbeRunner], list[ProbeRow]]
PROBES: dict[str, ProbeFn] = {}


def probe(source_id: str) -> Callable[[ProbeFn], ProbeFn]:
    def deco(fn: ProbeFn) -> ProbeFn:
        PROBES[source_id] = fn
        return fn

    return deco


def matrix_path(settings: Settings | None = None) -> Path:
    s = settings or get_settings()
    return s.path("reports") / "data" / "source_probe_matrix.csv"


def write_matrix(rows: list[ProbeRow], path: Path) -> None:
    """Merge rows into the matrix CSV: rows for a source_id being re-probed replace older ones."""
    existing: list[dict] = []
    if path.exists():
        with open(path, encoding="utf-8", newline="") as fh:
            existing = list(csv.DictReader(fh))
    new_sources = {r.source_id for r in rows}
    kept = [r for r in existing if r["source_id"] not in new_sources]
    merged = kept + [asdict(r) for r in rows]
    merged.sort(key=lambda r: (r["source_id"], r["instrument_id"]))
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=MATRIX_COLUMNS)
        w.writeheader()
        w.writerows(merged)


def run_probes(source_ids: list[str], runner: ProbeRunner) -> list[ProbeRow]:
    # Import probe modules so they register themselves.
    from esw.ingest import probes_in, probes_mkt, probes_us  # noqa: F401

    unknown = [s for s in source_ids if s not in PROBES]
    if unknown:
        raise KeyError(f"unknown probe(s): {unknown}; known: {sorted(PROBES)}")
    rows: list[ProbeRow] = []
    for sid in source_ids:
        log.info("probe %s", sid)
        try:
            rows.extend(PROBES[sid](runner))
        except Exception as exc:  # noqa: BLE001 - one failed probe must not stop the others
            log.exception("probe %s crashed", sid)
            rows.append(
                ProbeRow(source_id=sid, scope="probe crashed", status="NOT_FOUND", notes=repr(exc)[:300])
            )
    write_matrix(rows, matrix_path(runner.settings))
    return rows


def all_probe_ids() -> list[str]:
    from esw.ingest import probes_in, probes_mkt, probes_us  # noqa: F401

    return list(PROBES)

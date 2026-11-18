"""Shared ingestion plumbing (P04 T04.1): fetch-once raw files, manifest lines, failure isolation.

Every adapter writes raw files under `data/raw/<source_id>/...` exactly once (immutable; re-downloads
need `refresh=True` and create a new dated file), logs one manifest line per file (`ok`, `failed`,
`skipped_cached` or `manual`), and returns source-shaped frames that `stage()` writes to
`data/staged/<area>/<source_id>.parquet`.
"""

from __future__ import annotations

import datetime as dt
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from esw.config import Settings, get_settings
from esw.runlog import append_ingest_log, iso_utc, sha256_file


@dataclass
class FetchTask:
    source_id: str
    instrument_id: str | None
    url: str
    path: Path
    params: dict | None = None
    headers: dict | None = None


@dataclass
class FetchResult:
    task: FetchTask
    status: str  # ok | skipped_cached | failed
    path: Path | None
    error: str | None = None


class Fetcher:
    """Runs FetchTasks with a given session; one failure never stops the batch."""

    def __init__(self, settings: Settings | None = None, run_id: str = ""):
        self.settings = settings or get_settings()
        self.run_id = run_id
        self.root = self.settings.root

    def _rel(self, p: Path) -> str:
        return p.relative_to(self.root).as_posix() if self.root and p.is_absolute() else p.as_posix()

    def log(
        self, task: FetchTask, status: str, http_status: int | None = None, error: str | None = None, **extra
    ) -> None:
        p = task.path
        rec = {
            "ts_utc": iso_utc(),
            "source": task.source_id,
            "instrument_id": task.instrument_id,
            "url": task.url,
            "path": self._rel(p),
            "sha256": sha256_file(p) if p.exists() and status in {"ok", "skipped_cached", "manual"} else None,
            "bytes": p.stat().st_size if p.exists() else 0,
            "http_status": http_status,
            "status": status,
            "rows_parsed": extra.get("rows"),
            "date_min": extra.get("date_min"),
            "date_max": extra.get("date_max"),
            "error": error,
            "run_id": self.run_id,
        }
        append_ingest_log(rec)

    def run(
        self,
        task: FetchTask,
        get: Callable,
        refresh: bool = False,
        validate: Callable[[bytes], bool] | None = None,
    ) -> FetchResult:
        if task.path.exists() and not refresh:
            self.log(task, "skipped_cached")
            return FetchResult(task, "skipped_cached", task.path)
        try:
            resp = get(task.url, params=task.params, headers=task.headers)
        except Exception as exc:  # noqa: BLE001 - isolate failures per task
            self.log(task, "failed", error=f"{type(exc).__name__}: {exc}"[:300])
            return FetchResult(task, "failed", None, str(exc))
        if resp.status_code != 200 or (validate and not validate(resp.content)):
            self.log(task, "failed", http_status=resp.status_code, error=f"HTTP {resp.status_code}")
            return FetchResult(task, "failed", None, f"HTTP {resp.status_code}")
        path = task.path
        if path.exists():  # refresh: never overwrite raw data
            path = path.with_name(f"{path.stem}_{dt.date.today():%Y%m%d}{path.suffix}")
            task.path = path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(resp.content)
        self.log(task, "ok", http_status=200)
        return FetchResult(task, "ok", path)


def stage(df: pd.DataFrame, area: str, name: str, settings: Settings | None = None) -> Path:
    """Write a staged table deterministically (sorted, no index)."""
    settings = settings or get_settings()
    out = settings.path("staged") / area / f"{name}.parquet"
    out.parent.mkdir(parents=True, exist_ok=True)
    keys = [c for c in ("instrument_id", "ticker", "date") if c in df.columns]
    df = df.sort_values(keys).reset_index(drop=True) if keys else df
    df.to_parquet(out, index=False)
    return out

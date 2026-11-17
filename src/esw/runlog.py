"""Logging, run tracking, ingestion manifest and data fingerprints (System Specification §6.2, §12.5–12.6)."""

from __future__ import annotations

import csv
import hashlib
import json
import logging
import subprocess
import sys
import traceback
from collections.abc import Iterable
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import yaml

from esw.config import Settings, get_settings

LOG_FORMAT = "%(asctime)s %(levelname)s %(name)s run=%(run_id)s | %(message)s"

REGISTRY_COLUMNS = [
    "run_id",
    "started_utc",
    "ended_utc",
    "phase",
    "purpose",
    "model_id",
    "data_cutoff",
    "train_end",
    "test_period",
    "key_metrics_json",
    "status",
    "git_commit",
    "notes",
]

INGEST_REQUIRED = {"ts_utc", "source", "path", "sha256", "status"}
INGEST_STATUSES = {"ok", "failed", "skipped_cached", "manual", "not_found"}


# --------------------------------------------------------------------------- logging
class _RunIdFilter(logging.Filter):
    def __init__(self, run_id: str) -> None:
        super().__init__()
        self.run_id = run_id

    def filter(self, record: logging.LogRecord) -> bool:
        if not hasattr(record, "run_id"):
            record.run_id = self.run_id
        return True


def setup_logging(run_id: str = "-", command: str = "esw", logs_dir: Path | None = None) -> logging.Logger:
    """Configure the root logger for console + file output. Safe to call repeatedly."""
    root = logging.getLogger()
    for h in list(root.handlers):
        if getattr(h, "_esw", False):
            root.removeHandler(h)
    root.setLevel(logging.INFO)
    fmt = logging.Formatter(LOG_FORMAT)
    flt = _RunIdFilter(run_id)

    console = logging.StreamHandler(sys.stderr)
    console.setFormatter(fmt)
    console.addFilter(flt)
    console._esw = True  # type: ignore[attr-defined]
    root.addHandler(console)

    if logs_dir is not None:
        logs_dir.mkdir(parents=True, exist_ok=True)
        fname = logs_dir / f"{datetime.now().strftime('%Y%m%d')}_{command}.log"
        fh = logging.FileHandler(fname, encoding="utf-8")
        fh.setFormatter(fmt)
        fh.addFilter(flt)
        fh._esw = True  # type: ignore[attr-defined]
        root.addHandler(fh)
    return logging.getLogger("esw")


# --------------------------------------------------------------------------- helpers
def utc_now() -> datetime:
    return datetime.now(UTC)


def iso_utc(dt: datetime | None = None) -> str:
    return (dt or utc_now()).strftime("%Y-%m-%dT%H:%M:%SZ")


def git_commit(root: Path) -> str:
    """`<hash>` or `<hash>+dirty`; `unknown` if git is unavailable."""
    try:
        h = subprocess.run(
            ["git", "rev-parse", "HEAD"], cwd=root, capture_output=True, text=True, check=True
        ).stdout.strip()
        dirty = subprocess.run(
            ["git", "status", "--porcelain"], cwd=root, capture_output=True, text=True, check=True
        ).stdout.strip()
        return f"{h}+dirty" if dirty else h
    except (OSError, subprocess.CalledProcessError):
        return "unknown"


def sha256_file(path: Path, chunk: int = 1 << 20) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for block in iter(lambda: fh.read(chunk), b""):
            h.update(block)
    return h.hexdigest()


def parquet_content_hash(path: Path) -> str:
    """Hash of a Parquet file's *content* (schema + rows), independent of file-level metadata."""
    import pandas as pd

    df = pd.read_parquet(path)
    h = hashlib.sha256()
    h.update(json.dumps([(c, str(t)) for c, t in df.dtypes.items()]).encode())
    h.update(pd.util.hash_pandas_object(df, index=False).values.tobytes())
    return h.hexdigest()


def fingerprint(paths: Iterable[Path]) -> dict[str, str]:
    """SHA-256 per file; Parquet files are hashed by content."""
    out: dict[str, str] = {}
    for p in sorted(Path(x) for x in paths):
        out[str(p)] = parquet_content_hash(p) if p.suffix == ".parquet" else sha256_file(p)
    return out


# --------------------------------------------------------------------------- ingest manifest
def append_ingest_log(record: dict[str, Any], log_path: Path | None = None) -> None:
    """Validate an ingestion record (System Specification §6.2) and append it as one JSON line."""
    missing = INGEST_REQUIRED - record.keys()
    if missing:
        raise ValueError(f"ingest record missing keys: {sorted(missing)}")
    if record["status"] not in INGEST_STATUSES:
        raise ValueError(f"invalid ingest status {record['status']!r}; allowed {sorted(INGEST_STATUSES)}")
    if record["status"] in {"ok", "manual"} and not record.get("sha256"):
        raise ValueError("ok/manual records need a sha256")
    if log_path is None:
        from esw.paths import ingest_log_path

        log_path = ingest_log_path()
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with open(log_path, "a", encoding="utf-8") as fh:
        fh.write(json.dumps(record, default=str, sort_keys=True) + "\n")


# --------------------------------------------------------------------------- runs
@dataclass
class RunContext:
    """Context manager that creates `runs/<YYYYMMDD-HHMMSS>_<slug>/` and a registry row.

    Usage:
        with RunContext(phase="P04", purpose="ingest", slug="ingest_us") as run:
            run.log.info("...")
            run.log_metrics({"rows": 123})
    """

    phase: str
    purpose: str
    slug: str
    settings: Settings | None = None
    runs_dir: Path | None = None
    model_id: str = ""
    data_cutoff: str = ""
    train_end: str = ""
    test_period: str = ""
    notes: str = ""
    metrics: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.settings = self.settings or get_settings()
        self.runs_dir = self.runs_dir or self.settings.path("runs")
        self.started = utc_now()
        base = f"{self.started.strftime('%Y%m%d-%H%M%S')}_{self.slug}"
        run_id, i = base, 1
        while (self.runs_dir / run_id).exists():
            i += 1
            run_id = f"{base}_{i}"
        self.run_id = run_id
        self.dir = self.runs_dir / run_id
        self.status = "running"
        self.log = logging.getLogger(f"esw.run.{self.slug}")

    def __enter__(self) -> RunContext:
        assert self.settings is not None and self.settings.root is not None
        self.dir.mkdir(parents=True, exist_ok=False)
        setup_logging(self.run_id, self.slug, self.settings.path("logs"))
        cfg = self.settings.model_dump(mode="json", exclude={"root"})
        (self.dir / "config.yaml").write_text(yaml.safe_dump(cfg, sort_keys=False), encoding="utf-8")
        self.commit = git_commit(self.settings.root)
        (self.dir / "git_commit.txt").write_text(self.commit + "\n", encoding="utf-8")
        self.log.info("run started: phase=%s purpose=%s dir=%s", self.phase, self.purpose, self.dir)
        return self

    def log_metrics(self, metrics: dict[str, Any]) -> None:
        self.metrics.update(metrics)
        (self.dir / "metrics.json").write_text(
            json.dumps(self.metrics, indent=2, default=str, sort_keys=True), encoding="utf-8"
        )

    def write_fingerprint(self, paths: Iterable[Path]) -> None:
        (self.dir / "data_fingerprint.json").write_text(
            json.dumps(fingerprint(paths), indent=2), encoding="utf-8"
        )

    def __exit__(self, exc_type, exc, tb) -> bool:
        self.ended = utc_now()
        self.status = "failed" if exc_type else "ok"
        error = "".join(traceback.format_exception(exc_type, exc, tb)) if exc_type else ""
        self._write_readme(error)
        self._append_registry()
        self.log.info("run ended: status=%s", self.status)
        return False  # never swallow exceptions

    def _write_readme(self, error: str) -> None:
        lines = [
            f"# Run {self.run_id}",
            "",
            f"- Phase: {self.phase}",
            f"- Purpose: {self.purpose}",
            f"- Started (UTC): {iso_utc(self.started)}",
            f"- Ended (UTC): {iso_utc(self.ended)}",
            f"- Status: {self.status}",
            f"- Git commit: {self.commit}",
            f"- Metric keys: {', '.join(sorted(self.metrics)) or '(none)'}",
            "",
            "## Notes",
            "",
            self.notes or "_(agent notes go here)_",
        ]
        if error:
            lines += ["", "## Error", "", "```", error.strip(), "```"]
        (self.dir / "README.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

    def _append_registry(self) -> None:
        assert self.runs_dir is not None
        reg = self.runs_dir / "registry.csv"
        new = not reg.exists() or reg.stat().st_size == 0
        row = {
            "run_id": self.run_id,
            "started_utc": iso_utc(self.started),
            "ended_utc": iso_utc(self.ended),
            "phase": self.phase,
            "purpose": self.purpose,
            "model_id": self.model_id,
            "data_cutoff": self.data_cutoff,
            "train_end": self.train_end,
            "test_period": self.test_period,
            "key_metrics_json": json.dumps(self.metrics, default=str, sort_keys=True) if self.metrics else "",
            "status": self.status,
            "git_commit": self.commit,
            "notes": self.notes,
        }
        with open(reg, "a", newline="", encoding="utf-8") as fh:
            w = csv.DictWriter(fh, fieldnames=REGISTRY_COLUMNS)
            if new:
                w.writeheader()
            w.writerow(row)


def ensure_registry(runs_dir: Path) -> Path:
    """Create `runs/registry.csv` with a header if it does not exist."""
    runs_dir.mkdir(parents=True, exist_ok=True)
    reg = runs_dir / "registry.csv"
    if not reg.exists() or reg.stat().st_size == 0:
        with open(reg, "w", newline="", encoding="utf-8") as fh:
            csv.DictWriter(fh, fieldnames=REGISTRY_COLUMNS).writeheader()
    return reg

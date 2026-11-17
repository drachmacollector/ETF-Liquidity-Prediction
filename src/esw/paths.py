"""Canonical paths derived from settings (System Specification §3)."""

from __future__ import annotations

from pathlib import Path

from esw.config import Settings, get_settings

CANONICAL_DIRS = (
    "reference",
    "raw",
    "manual_drop",
    "staged",
    "curated",
    "derived",
    "manifests",
    "runs",
    "models",
    "outputs",
    "reports",
    "logs",
    "records",
)


def canonical_paths(settings: Settings | None = None) -> dict[str, Path]:
    s = settings or get_settings()
    return {name: s.path(name) for name in CANONICAL_DIRS}


def ingest_log_path(settings: Settings | None = None) -> Path:
    s = settings or get_settings()
    return s.path("manifests") / "ingest_log.jsonl"


def registry_path(settings: Settings | None = None) -> Path:
    s = settings or get_settings()
    return s.path("runs") / "registry.csv"

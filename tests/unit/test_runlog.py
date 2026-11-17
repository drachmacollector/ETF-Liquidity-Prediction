"""RunContext, registry and ingestion-manifest behaviour."""

import csv
import json

import pandas as pd
import pytest

from esw.config import load_settings
from esw.runlog import (
    REGISTRY_COLUMNS,
    RunContext,
    append_ingest_log,
    fingerprint,
    parquet_content_hash,
)


def _read_registry(runs_dir):
    with open(runs_dir / "registry.csv", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


@pytest.fixture()
def settings():
    return load_settings()


def test_run_context_creates_folder_and_registry(tmp_path, settings):
    with RunContext(phase="P00", purpose="test", slug="unit", settings=settings, runs_dir=tmp_path) as run:
        run.log_metrics({"a": 1})
    for f in ("config.yaml", "git_commit.txt", "README.md", "metrics.json"):
        assert (run.dir / f).exists(), f
    rows = _read_registry(tmp_path)
    assert len(rows) == 1
    assert list(rows[0].keys()) == REGISTRY_COLUMNS
    assert rows[0]["status"] == "ok" and rows[0]["phase"] == "P00"
    assert json.loads(rows[0]["key_metrics_json"]) == {"a": 1}


def test_run_context_records_failure(tmp_path, settings):
    with (
        pytest.raises(RuntimeError),
        RunContext(phase="P00", purpose="test", slug="boom", settings=settings, runs_dir=tmp_path) as run,
    ):
        raise RuntimeError("boom")
    rows = _read_registry(tmp_path)
    assert rows[-1]["status"] == "failed"
    assert "RuntimeError" in (run.dir / "README.md").read_text(encoding="utf-8")


def test_two_runs_same_second_get_distinct_ids(tmp_path, settings):
    a = RunContext(phase="P00", purpose="t", slug="same", settings=settings, runs_dir=tmp_path)
    with a:
        pass
    b = RunContext(phase="P00", purpose="t", slug="same", settings=settings, runs_dir=tmp_path)
    with b:
        pass
    assert a.run_id != b.run_id


def _good_record(**kw):
    rec = {"ts_utc": "2026-11-17T00:00:00Z", "source": "x", "path": "p", "sha256": "abc", "status": "ok"}
    rec.update(kw)
    return rec


def test_ingest_log_appends_valid_records(tmp_path):
    log = tmp_path / "ingest_log.jsonl"
    append_ingest_log(_good_record(), log)
    append_ingest_log(_good_record(status="failed", sha256=""), log)
    lines = log.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 2 and json.loads(lines[0])["status"] == "ok"


@pytest.mark.parametrize(
    "bad",
    [
        {"status": "weird"},
        {"sha256": ""},  # ok record without checksum
    ],
)
def test_ingest_log_rejects_malformed(tmp_path, bad):
    with pytest.raises(ValueError):
        append_ingest_log(_good_record(**bad), tmp_path / "log.jsonl")


def test_ingest_log_rejects_missing_keys(tmp_path):
    rec = _good_record()
    del rec["path"]
    with pytest.raises(ValueError):
        append_ingest_log(rec, tmp_path / "log.jsonl")


def test_parquet_content_hash_ignores_file_metadata(tmp_path):
    df = pd.DataFrame({"a": [1, 2], "b": ["x", "y"]})
    p1, p2 = tmp_path / "1.parquet", tmp_path / "2.parquet"
    df.to_parquet(p1, compression="snappy")
    df.to_parquet(p2, compression="gzip")
    assert parquet_content_hash(p1) == parquet_content_hash(p2)
    fp = fingerprint([p1, p2])
    assert len(fp) == 2

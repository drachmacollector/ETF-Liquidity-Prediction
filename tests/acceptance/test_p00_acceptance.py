"""P00 acceptance: environment works, doctor passes, secrets are not tracked."""

import re
import subprocess
import sys

import pytest

from esw.config import find_repo_root

pytestmark = pytest.mark.acceptance
ROOT = find_repo_root()


def _run(*args):
    return subprocess.run([sys.executable, "-m", "esw", *args], cwd=ROOT, capture_output=True, text=True)


def test_version_command():
    r = _run("version")
    assert r.returncode == 0, r.stderr
    assert r.stdout.startswith("esw 0.1.0")


def test_doctor_passes():
    r = _run("doctor")
    assert r.returncode == 0, r.stdout + r.stderr
    assert "All checks passed." in r.stdout


def test_env_not_tracked_and_ignored():
    tracked = subprocess.run(["git", "ls-files", ".env"], cwd=ROOT, capture_output=True, text=True).stdout
    assert tracked.strip() == ""
    ignored = subprocess.run(["git", "check-ignore", ".env"], cwd=ROOT, capture_output=True, text=True)
    assert ignored.returncode == 0


def test_no_secret_values_in_tracked_files():
    """Tracked files must not contain an assignment of a non-empty API key."""
    files = subprocess.run(["git", "ls-files"], cwd=ROOT, capture_output=True, text=True).stdout.split("\n")
    pattern = re.compile(r"(TIINGO_API_KEY|FRED_API_KEY)\s*=\s*['\"]?[A-Za-z0-9]{16,}")
    for f in files:
        p = ROOT / f
        if not f or not p.is_file() or p.suffix in {".pdf", ".png", ".ico", ".parquet", ".zip"}:
            continue
        text = p.read_text(encoding="utf-8", errors="ignore")
        assert not pattern.search(text), f"possible secret in {f}"


def test_required_files_exist():
    for rel in (
        "pyproject.toml",
        "config/settings.yaml",
        ".env.example",
        ".gitignore",
        "runs/registry.csv",
        "data/manifests/ingest_log.jsonl",
        "uv.lock",
    ):
        assert (ROOT / rel).exists(), rel

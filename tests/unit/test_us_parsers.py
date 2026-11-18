"""P04: US adapters parse their golden files; fetcher idempotency and failure isolation (offline)."""

from pathlib import Path

import pandas as pd
import pytest

from esw.ingest.base import Fetcher, FetchTask
from esw.ingest.us_issuers import parse_invesco_navs, parse_uscf_api

FX = Path(__file__).resolve().parents[1] / "fixtures"


def test_uscf_api_parser_raw_split():
    df = parse_uscf_api((FX / "us_iss_uscf" / "USO_historicalnav_api_trimmed.json").read_bytes(), "USO")
    s = df.set_index("date")["nav"]
    assert s[pd.Timestamp("2020-04-29")] / s[pd.Timestamp("2020-04-28")] == pytest.approx(8.44, abs=0.05)


def test_invesco_parser():
    df = parse_invesco_navs((FX / "us_iss_invesco" / "DBC_navs_trimmed.json").read_bytes())
    assert {"date", "nav", "total_net_assets", "shares_out"} <= set(df.columns)
    assert df["date"].min() == pd.Timestamp("2016-09-29") and (df["nav"] > 0).all()


class _Resp:
    def __init__(self, code, content=b"[1]"):
        self.status_code, self.content = code, content


def test_fetcher_idempotent_and_isolated(tmp_path, monkeypatch):
    logged = []
    monkeypatch.setattr("esw.ingest.base.append_ingest_log", lambda rec, *a, **k: logged.append(rec))
    f = Fetcher(run_id="test")
    f.root = tmp_path
    ok = FetchTask("t", "US:A", "http://x/a", tmp_path / "a.json")
    bad = FetchTask("t", "US:B", "http://x/b", tmp_path / "b.json")
    calls = {"n": 0}

    def get(url, params=None, headers=None):
        calls["n"] += 1
        return _Resp(500) if url.endswith("b") else _Resp(200, b"[1,2]")

    assert f.run(ok, get).status == "ok"
    assert f.run(bad, get).status == "failed"  # one failure does not stop the batch
    assert f.run(ok, get).status == "skipped_cached"  # idempotent: no second download
    assert calls["n"] == 2 and [r["status"] for r in logged] == ["ok", "failed", "skipped_cached"]

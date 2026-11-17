"""P01 acceptance: every planned source probed, matrix well-formed, reports and fixtures present."""

import csv
import json

import pytest

from esw.config import find_repo_root

pytestmark = pytest.mark.acceptance
ROOT = find_repo_root()
MATRIX = ROOT / "reports" / "data" / "source_probe_matrix.csv"

# Source families that P01 §T01.2–T01.4 requires to be probed.
REQUIRED_SOURCES = {
    "us_px_tiingo", "us_px_stooq", "us_px_yf", "us_iss_spdr_gold", "us_iss_ishares", "us_iss_ssga",
    "us_iss_uscf", "us_iss_invesco", "us_iss_vaneck", "us_iss_globalx", "us_iss_xtrackers", "us_iss_abrdn",
    "us_iss_teucrium", "us_iss_vanguard", "us_wayback", "us_edgar",
    "in_bhav_udiff", "in_bhav_legacy", "in_bse_bhav", "in_amfi_navall", "in_amfi_hist", "in_mfapi",
    "in_spot_mcx", "in_spot_ibja", "in_indiavix", "in_amfi_aum",
    "mkt_fred", "mkt_eia", "mkt_fut_yf", "mkt_cal",
}  # fmt: skip


@pytest.fixture(scope="module")
def matrix():
    assert MATRIX.exists(), "run `esw probe` first"
    with open(MATRIX, encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def test_every_required_source_probed(matrix):
    probed = {r["source_id"] for r in matrix}
    assert probed >= REQUIRED_SOURCES, sorted(REQUIRED_SOURCES - probed)


def test_status_values_and_ok_rows_have_history(matrix):
    for r in matrix:
        assert r["status"] in {"OK", "PARTIAL", "BLOCKED", "MANUAL_ONLY", "NOT_FOUND"}
        if r["status"] == "OK" and r["source_id"] not in {"us_edgar", "mkt_cal", "in_mfapi_vs_amfi"}:
            assert r["history_start"], f"OK row without history_start: {r['source_id']} {r['instrument_id']}"


def test_no_probe_crashed(matrix):
    assert not [r for r in matrix if r["scope"] == "probe crashed"]


def test_reports_exist():
    for rel in (
        "reports/data/source_probe_report.md",
        "reports/data/primary_text_notes.md",
        "reports/data/terms_of_use_summary.md",
        "reports/data/universe_feasibility.md",
        "reference/source_registry.csv",
    ):
        assert (ROOT / rel).exists(), rel


def test_fixtures_exist_for_ok_sources():
    fx = ROOT / "tests" / "fixtures"
    for sid in ("us_px_tiingo", "us_iss_spdr_gold", "us_iss_ishares", "us_iss_ssga", "in_bhav_udiff",
                "in_bhav_legacy", "in_amfi_navall", "in_amfi_hist", "in_mfapi", "mkt_fred", "mkt_eia"):  # fmt: skip
        assert any((fx / sid).glob("*")), f"no fixture for {sid}"


def test_probe_files_logged_with_checksums():
    """Every probe download is in the ingestion manifest with a checksum; failures carry an error."""
    log = ROOT / "data" / "manifests" / "ingest_log.jsonl"
    entries = [json.loads(x) for x in log.read_text(encoding="utf-8").splitlines() if x.strip()]
    probes = [e for e in entries if "_probes" in e.get("path", "") or e["status"] == "failed"]
    assert probes
    for e in probes:
        if e["status"] == "ok":
            assert len(e["sha256"]) == 64
            assert (ROOT / e["path"]).exists(), e["path"]
        if e["status"] == "failed":
            assert e.get("error")

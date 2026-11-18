"""P03 acceptance: catalogue counts, required incidents, capacity coverage, validation, review state."""

import pandas as pd
import pytest

from esw.config import find_repo_root, get_settings
from esw.reference.catalogue import run_catalogue_validation

pytestmark = pytest.mark.acceptance
ROOT = find_repo_root()
REF = ROOT / "reference"
REQUIRED = [
    "INC-US-2008-BOND", "INC-US-2009-UNG", "INC-US-2011-EGPT", "INC-US-2012-TVIX", "INC-US-2013-TAPER",
    "INC-US-2015-GREK", "INC-US-2015-CHINA", "INC-US-2020-BOND", "INC-US-2020-GOLD-EFP", "INC-US-2020-USO",
    "INC-US-2021-SLV", "INC-US-2022-RUSSIA", "INC-US-2025-SILVER", "INC-US-2026-METALS", "INC-IN-2013-GOLD",
    "INC-IN-2020-COVID", "INC-IN-2022-INTL", "INC-IN-2024-INTL", "INC-IN-2025-SILVER", "INC-IN-2026-CRASH",
    "INC-IN-2026-INTL",
]  # fmt: skip


def _r(name):
    return pd.read_csv(REF / f"{name}.csv", dtype=str, keep_default_na=False)


def test_ac_03_1_counts_and_required_rows():
    inc = _r("incidents")
    assert len(inc) >= 18 and (inc.market == "US").sum() >= 12 and (inc.market == "IN").sum() >= 6
    assert set(REQUIRED) <= set(inc.incident_id)
    assert (inc.near_miss == "y").any() and inc.set_index("incident_id").loc[
        "INC-US-2021-SLV", "near_miss"
    ] == "y"


def test_ac_03_2_operational_events():
    ev = _r("operational_events")
    assert len(ev) >= 30
    assert (ev.source_url != "").all() and ev.grade.isin(["V", "R", "K", "A"]).all()
    assert ((ev.date_precision == "month") | (ev.known_at != "")).all()


def test_ac_03_3_capacity_uso_ung():
    cap = _r("capacity_us")
    for t in ("US:USO", "US:UNG"):
        c = cap[cap.instrument_id == t]
        for yr in ("2009", "2020"):
            assert c.as_of.str.startswith(yr).any(), (t, yr)
        assert c.known_at.str.endswith("Z").all()


def test_ac_03_4_labels_and_review():
    inc = _r("incidents")
    assert (inc.mechanisms != "").all() and (inc.primary_family != "").all()
    assert (ROOT / "reports" / "catalogue" / "catalogue_report.md").exists()


def test_ac_03_6_validation_passes():
    assert run_catalogue_validation(get_settings()).errors == []

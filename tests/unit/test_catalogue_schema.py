"""P03: catalogue validation rejects bad rows (offline)."""

import pandas as pd

from esw.config import get_settings
from esw.reference.catalogue import (
    CatalogueReport,
    _known_ids,
    _read,
    run_catalogue_validation,
    validate_capacity,
    validate_events,
    validate_incidents,
)

ST = get_settings()


def _known():
    return _known_ids(ST)


def test_catalogue_validates():
    rep = run_catalogue_validation(ST)
    assert rep.errors == [], rep.errors[:5]


def test_bad_mechanism_and_family_rejected():
    inc = _read(ST, "incidents")
    inc.loc[0, "mechanisms"] = "M9"
    inc.loc[1, "primary_family"] = "XYZ"
    rep = CatalogueReport()
    validate_incidents(inc, _known(), rep)
    assert any("bad mechanisms" in e for e in rep.errors)
    assert any("bad primary_family" in e for e in rep.errors)


def test_missing_known_at_rejected():
    ev = _read(ST, "operational_events")
    i = ev.index[ev["date_precision"] == "day"][0]
    ev.loc[i, "known_at"] = ""
    rep = CatalogueReport()
    validate_events(ev, _known(), set(_read(ST, "incidents")["incident_id"]), rep)
    assert any("known_at" in e for e in rep.errors)


def test_unknown_instrument_rejected():
    ev = _read(ST, "operational_events")
    ev.loc[0, "instrument_ids"] = "US:NOPE"
    rep = CatalogueReport()
    validate_events(ev, _known(), set(_read(ST, "incidents")["incident_id"]), rep)
    assert any("unknown instrument" in e for e in rep.errors)


def test_bad_capacity_metric_rejected():
    cap = _read(ST, "capacity_us")
    cap.loc[0, "metric"] = "headroom"
    rep = CatalogueReport()
    validate_capacity(cap, _known(), rep)
    assert any("bad metric" in e for e in rep.errors)


def test_known_at_is_not_effective_at_for_filings():
    ev = _read(ST, "operational_events")
    v = ev[ev["source_url"].str.contains("sec.gov/Archives")]
    # EDGAR rows carry an acceptance timestamp with seconds, never a bare effective date
    assert v["known_at"].str.match(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$").all()
    assert (pd.to_datetime(v["known_at"]).dt.second != 0).mean() > 0.8

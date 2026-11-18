"""P03: validation of the incident, operational-event and capacity tables (`esw catalogue validate`).

Rules (P03 T03.9): unique IDs; allowed codes; `known_at` present for `date_precision = day` (it may
precede `effective_at`: announcements come first); instrument IDs exist in the reference tables
(`EXT:` IDs mark instruments outside the universe, e.g. the TVIX ETN); every row sourced.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import pandas as pd

from esw.config import Settings, get_settings

MECHANISMS = {f"M{i}" for i in range(1, 9)}
FAMILIES = {"CRE", "STL", "UND", "LIQ", "DEM", "MKT"}
DIRECTIONS = {"PREMIUM", "DISCOUNT", "BOTH"}
GRADES = {"V", "R", "K", "A"}
GROUPS = {
    "US_COMM_PHYS",
    "US_COMM_FUT",
    "US_BOND",
    "US_INTL",
    "US_CTRL",
    "IN_GOLD",
    "IN_SILVER",
    "IN_INTL",
    "IN_DEBT",
    "IN_CTRL",
}
EVENT_TYPES = {
    "creation_suspended",
    "creation_resumed",
    "creation_limited",
    "subscription_halt_fof",
    "subscription_resume_fof",
    "subscription_halt_etf_direct",
    "industry_cap_stop",
    "trading_halt",
    "trading_resumed",
    "market_closure_unscheduled",
    "market_reopen",
    "registration_effective",
    "fund_liquidation_announced",
    "prospectus_risk_warning",
}
SCOPES = {"instrument", "issuer", "industry", "market"}
CAPACITY_METRICS = {
    "registered_shares_total",
    "registered_shares_remaining",
    "shares_outstanding_reported",
    "registration_type",
}
REVIEW_STATUS = {"pending_second_pass", "second_pass_done", "user_approved", "user_edited"}


@dataclass
class CatalogueReport:
    errors: list[str] = field(default_factory=list)
    info: list[str] = field(default_factory=list)

    def summary(self) -> str:
        return f"catalogue validation: {len(self.errors)} error(s)"


def _read(settings: Settings, name: str) -> pd.DataFrame:
    return pd.read_csv(settings.path("reference") / f"{name}.csv", dtype=str, keep_default_na=False)


def _known_ids(settings: Settings) -> set[str]:
    ids: set[str] = set()
    for t in ("instruments_us", "instruments_in"):
        ids |= set(_read(settings, t)["instrument_id"])
    return ids


def _ts_ok(s: str) -> bool:
    try:
        t = pd.Timestamp(s)
    except (ValueError, TypeError):
        return False
    return t.tzinfo is not None


def _date_ok(s: str) -> bool:
    try:
        pd.Timestamp(s)
    except (ValueError, TypeError):
        return False
    return True


def _check_ids(field_val: str, known: set[str], where: str, rep: CatalogueReport) -> None:
    for iid in filter(None, field_val.split(";")):
        if iid.startswith("EXT:"):
            continue
        if iid not in known:
            rep.errors.append(f"{where}: unknown instrument {iid}")


def validate_incidents(df: pd.DataFrame, known: set[str], rep: CatalogueReport) -> None:
    for i in df.index[df["incident_id"].duplicated()]:
        rep.errors.append(f"incidents: duplicate id {df.at[i, 'incident_id']}")
    for r in df.to_dict("records"):
        w = f"incidents {r['incident_id']}"
        mech = [m for m in r["mechanisms"].split(";") if m]
        if not mech or set(mech) - MECHANISMS:
            rep.errors.append(f"{w}: bad mechanisms {r['mechanisms']!r}")
        if r["primary_family"] not in FAMILIES:
            rep.errors.append(f"{w}: bad primary_family {r['primary_family']!r}")
        if r["direction"] not in DIRECTIONS:
            rep.errors.append(f"{w}: bad direction {r['direction']!r}")
        if r["market"] not in {"US", "IN"}:
            rep.errors.append(f"{w}: bad market")
        if r["group"] not in GROUPS:
            rep.errors.append(f"{w}: bad group {r['group']!r}")
        for c in ("near_miss", "include_in_validation", "in_dev_period", "in_lockbox"):
            if r[c] not in {"y", "n"}:
                rep.errors.append(f"{w}: {c} must be y/n")
        for c in ("approx_onset", "analogue_anchor_date"):
            if not _date_ok(r[c]):
                rep.errors.append(f"{w}: bad {c}")
        for c in ("peak_date", "approx_end"):
            if r[c] and not _date_ok(r[c]):
                rep.errors.append(f"{w}: bad {c}")
        if not _ts_ok(r["first_public_known_at"]):
            rep.errors.append(f"{w}: first_public_known_at must be a UTC timestamp")
        if r["grade"] not in GRADES:
            rep.errors.append(f"{w}: bad grade")
        if not r["sources"].strip():
            rep.errors.append(f"{w}: no source")
        if r["review_status"] not in REVIEW_STATUS:
            rep.errors.append(f"{w}: bad review_status")
        _check_ids(r["instrument_ids"], known, w, rep)
    rep.info.append(f"incidents: {len(df)} rows checked")


def validate_events(df: pd.DataFrame, known: set[str], incident_ids: set[str], rep: CatalogueReport) -> None:
    for i in df.index[df["event_id"].duplicated()]:
        rep.errors.append(f"operational_events: duplicate id {df.at[i, 'event_id']}")
    for r in df.to_dict("records"):
        w = f"operational_events {r['event_id']}"
        if r["type"] not in EVENT_TYPES:
            rep.errors.append(f"{w}: bad type {r['type']!r}")
        if r["scope"] not in SCOPES:
            rep.errors.append(f"{w}: bad scope {r['scope']!r}")
        if r["date_precision"] not in {"day", "month"}:
            rep.errors.append(f"{w}: bad date_precision")
        if not _date_ok(r["effective_at"]):
            rep.errors.append(f"{w}: bad effective_at")
        if r["date_precision"] == "day" and not _ts_ok(r["known_at"]):
            rep.errors.append(f"{w}: known_at (UTC timestamp) required for day precision")
        if r["ended_at"] and not _date_ok(r["ended_at"]):
            rep.errors.append(f"{w}: bad ended_at")
        if r["ended_known_at"] and not _ts_ok(r["ended_known_at"]):
            rep.errors.append(f"{w}: bad ended_known_at")
        if not r["source_url"].strip():
            rep.errors.append(f"{w}: no source_url")
        if r["grade"] not in GRADES:
            rep.errors.append(f"{w}: bad grade")
        if r["related_incident_id"] and r["related_incident_id"] not in incident_ids:
            rep.errors.append(f"{w}: unknown incident {r['related_incident_id']}")
        _check_ids(r["instrument_ids"], known, w, rep)
    rep.info.append(f"operational_events: {len(df)} rows checked")


def validate_capacity(df: pd.DataFrame, known: set[str], rep: CatalogueReport) -> None:
    key = df.duplicated(subset=["instrument_id", "as_of", "metric", "known_at"])
    for i in df.index[key]:
        rep.errors.append(
            f"capacity_us: duplicate row {df.loc[i, ['instrument_id', 'as_of', 'metric']].tolist()}"
        )
    for r in df.to_dict("records"):
        w = f"capacity_us {r['instrument_id']} {r['as_of']} {r['metric']}"
        if r["instrument_id"] not in known:
            rep.errors.append(f"{w}: unknown instrument")
        if r["metric"] not in CAPACITY_METRICS:
            rep.errors.append(f"{w}: bad metric")
        if r["metric"] != "registration_type":
            try:
                if float(r["value"]) < 0:
                    rep.errors.append(f"{w}: negative value")
            except ValueError:
                rep.errors.append(f"{w}: non-numeric value")
        if not _ts_ok(r["known_at"]):
            rep.errors.append(f"{w}: known_at must be a UTC timestamp")
        if not r["source_url"].strip():
            rep.errors.append(f"{w}: no source_url")
    rep.info.append(f"capacity_us: {len(df)} rows checked")


def run_catalogue_validation(settings: Settings | None = None) -> CatalogueReport:
    settings = settings or get_settings()
    rep = CatalogueReport()
    known = _known_ids(settings)
    inc = _read(settings, "incidents")
    validate_incidents(inc, known, rep)
    validate_events(_read(settings, "operational_events"), known, set(inc["incident_id"]), rep)
    validate_capacity(_read(settings, "capacity_us"), known, rep)
    return rep

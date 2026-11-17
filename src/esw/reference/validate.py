"""`esw reference validate`: schema checks for every reference table plus the T02.11 cross-table checks.

Writes `reports/data/reference_validation.md`. Errors fail the command; warnings are reported only.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import pandas as pd
import pandera.errors as pe

from esw.config import Settings, get_settings
from esw.reference.loaders import TABLES, coerce, read_raw, table_path
from esw.reference.schemas import IN_GROUPS, SCHEMAS, US_GROUPS

# P01 feasibility gate (P01 T01.8): group -> (minimum included, must include tickers/symbols)
GATE_US = {
    "US_COMM_PHYS": (3, ["GLD", "SLV"]),
    "US_COMM_FUT": (4, ["USO", "UNG"]),
    "US_BOND": (4, ["LQD"]),
    "US_INTL": (4, []),
    "US_CTRL": (3, []),
}
US_INTL_STRESS = ["EGPT", "GREK", "RSX", "ERUS"]
GATE_IN = {("IN_GOLD", "IN_SILVER"): (10, ["GOLDETF", "SILVERAG"]), ("IN_INTL",): (3, ["MAFANG"])}


@dataclass
class Report:
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    info: list[str] = field(default_factory=list)

    def summary(self) -> str:
        return f"reference validation: {len(self.errors)} error(s), {len(self.warnings)} warning(s)"

    def to_markdown(self) -> str:
        out = ["# Reference validation", "", f"**Result:** {self.summary()}", ""]
        for title, items in (("Errors", self.errors), ("Warnings", self.warnings), ("Checks run", self.info)):
            out += [f"## {title}", ""]
            out += [f"- {x}" for x in items] or ["- none"]
            out.append("")
        return "\n".join(out)


def _periods_ok(df: pd.DataFrame, keys: list[str], name: str, rep: Report, contiguous: bool = True) -> None:
    for k, g in df.sort_values("effective_from").groupby(keys):
        g = g.reset_index(drop=True)
        for i in range(1, len(g)):
            prev_to, cur_from = g.loc[i - 1, "effective_to"], g.loc[i, "effective_from"]
            if pd.isna(prev_to):
                rep.errors.append(f"{name} {k}: open-ended period followed by another period")
            elif cur_from <= prev_to:
                rep.errors.append(f"{name} {k}: overlap at {cur_from.date()}")
            elif contiguous and cur_from != prev_to + pd.Timedelta(days=1):
                rep.errors.append(f"{name} {k}: gap between {prev_to.date()} and {cur_from.date()}")


def load_all(settings: Settings, rep: Report) -> dict[str, pd.DataFrame]:
    tables: dict[str, pd.DataFrame] = {}
    for name in TABLES:
        p = table_path(name, settings)
        if not p.exists():
            rep.errors.append(f"{name}: file {p.name} missing")
            continue
        try:
            typed = coerce(name, read_raw(name, settings))
            tables[name] = SCHEMAS[name].validate(typed, lazy=True)
            rep.info.append(f"{name}: schema OK ({len(typed)} rows)")
        except pe.SchemaErrors as exc:
            fc = exc.failure_cases
            for _, r in fc.head(30).iterrows():
                rep.errors.append(
                    f"{name}: {r['check']} (column {r['column']}, index {r['index']}, value {r['failure_case']})"
                )
            tables[name] = typed
        except Exception as exc:  # noqa: BLE001 - conversion errors are reported, not raised
            rep.errors.append(f"{name}: cannot load ({type(exc).__name__}: {exc})")
    return tables


def cross_checks(t: dict[str, pd.DataFrame], rep: Report) -> None:
    us, ind, sh, nc = (t.get(k) for k in ("instruments_us", "instruments_in", "symbol_history", "nav_clock"))
    if us is None or ind is None or sh is None or nc is None:
        rep.errors.append("cross-table checks skipped: a core table failed to load")
        return

    # 1. nav_clock covers each included instrument's whole listing period, without gaps
    inst = pd.concat(
        [
            us[["instrument_id", "include", "listing_date", "delisting_date"]],
            ind.assign(listing_date=ind["listing_date"].fillna(ind["inception_date"]), delisting_date=pd.NaT)[
                ["instrument_id", "include", "listing_date", "delisting_date"]
            ],
        ]
    )
    _periods_ok(nc, ["instrument_id"], "nav_clock", rep)
    for r in inst[inst["include"]].itertuples(index=False):
        g = nc[nc["instrument_id"] == r.instrument_id]
        if g.empty:
            rep.errors.append(f"nav_clock: no row for included {r.instrument_id}")
            continue
        start = r.listing_date if pd.notna(r.listing_date) else None
        if start is not None and g["effective_from"].min() > start:
            rep.errors.append(
                f"nav_clock: {r.instrument_id} starts {g['effective_from'].min().date()} after listing {start.date()}"
            )
        last_to = g.sort_values("effective_from")["effective_to"].iloc[-1]
        if pd.notna(last_to) and (pd.isna(r.delisting_date) or last_to < r.delisting_date):
            rep.errors.append(f"nav_clock: {r.instrument_id} ends {last_to.date()} before the end of listing")
    rep.info.append("T02.11-1 nav_clock coverage of included instruments")

    # 2. Indian instruments: one AMFI code each (by construction: one row per ISIN), NSE symbol present
    dup = ind["amfi_scheme_code"].duplicated(keep=False)
    for iid in ind.loc[dup, "instrument_id"]:
        rep.errors.append(f"instruments_in: AMFI code shared by several instruments ({iid})")
    nse = sh[sh["exchange"] == "NSE"]
    for iid in ind.loc[ind["include"], "instrument_id"]:
        if iid not in set(nse["instrument_id"]):
            rep.errors.append(f"symbol_history: included {iid} has no NSE symbol")
    rep.info.append("T02.11-2 one AMFI code and at least one NSE symbol per included Indian instrument")

    # 3. no two Indian instruments share an NSE symbol on the same date
    far = pd.Timestamp("2100-01-01")
    n = nse[nse["instrument_id"].str.startswith("IN:")].copy()
    n["vf"] = n["valid_from"].fillna(pd.Timestamp("1900-01-01"))
    n["vt"] = n["valid_to"].fillna(far)
    for sym, g in n.groupby("symbol"):
        if g["instrument_id"].nunique() < 2:
            continue
        rows = g.sort_values("vf").to_dict("records")
        for i, a in enumerate(rows):
            for b in rows[i + 1 :]:
                if a["instrument_id"] != b["instrument_id"] and b["vf"] <= a["vt"] and a["vf"] <= b["vt"]:
                    rep.errors.append(
                        f"symbol_history: NSE symbol {sym} used by {a['instrument_id']} and {b['instrument_id']} at the same time"
                    )
    rep.info.append("T02.11-3 no shared NSE symbol on the same date")

    # 4. group codes
    bad = set(us["group"]) - set(US_GROUPS) | set(ind["group"]) - set(IN_GROUPS)
    if bad:
        rep.errors.append(f"unknown group codes {sorted(bad)}")
    rep.info.append("T02.11-4 group codes are System Specification §5.1 codes")

    # 5. feasibility gate on included instruments
    inc_us = us[us["include"]]
    for grp, (k, must) in GATE_US.items():
        g = inc_us[inc_us["group"] == grp]
        missing = [m for m in must if m not in set(g["ticker"])]
        if len(g) < k or missing:
            rep.errors.append(f"gate {grp}: {len(g)} included (min {k}); missing {missing}")
        else:
            rep.info.append(f"gate {grp}: {len(g)} included (min {k}) PASS")
    if not set(US_INTL_STRESS) & set(inc_us["ticker"]):
        rep.errors.append("gate US_INTL: no stress-window instrument (EGPT/GREK/RSX/ERUS) included")
    inc_in = ind[ind["include"]]
    for grps, (k, must) in GATE_IN.items():
        g = inc_in[inc_in["group"].isin(grps)]
        missing = [m for m in must if m not in set(g["nse_symbol_current"])]
        mirae_ok = all(
            g.loc[g["nse_symbol_current"] == m, "is_mirae"].all() for m in must if m not in missing
        )
        if len(g) < k or missing or not mirae_ok:
            rep.errors.append(f"gate {'+'.join(grps)}: {len(g)} included (min {k}); missing {missing}")
        else:
            rep.info.append(f"gate {'+'.join(grps)}: {len(g)} included (min {k}) PASS")
    rep.info.append("T02.11-5 feasibility gate")

    # 6. duty and band-regime periods
    if "duty_india" in t:
        d = t["duty_india"]
        _periods_ok(d, ["metal"], "duty_india", rep)
        for metal, g in d.groupby("metal"):
            if g["effective_from"].min() > pd.Timestamp("2007-01-01"):
                rep.errors.append(f"duty_india {metal}: starts after 2007-01-01")
            if g["effective_to"].notna().all():
                rep.errors.append(f"duty_india {metal}: no open-ended current row")
    if "band_regimes_india" in t:
        _periods_ok(t["band_regimes_india"], ["exchange", "group"], "band_regimes_india", rep)
    rep.info.append("T02.11-6 duty and band-regime periods contiguous and non-overlapping")

    # unverified rows (MI-09)
    for name in ("duty_india", "band_regimes_india"):
        if name in t:
            nv = int((t[name]["verified"] == "n").sum())
            rep.warnings.append(f"{name}: {nv} row(s) verified = n (listed in MI-09)")


def run_validation(settings: Settings | None = None, write: bool = True) -> Report:
    settings = settings or get_settings()
    rep = Report()
    tables = load_all(settings, rep)
    cross_checks(tables, rep)
    if write:
        out = settings.path("reports") / "data" / "reference_validation.md"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(rep.to_markdown(), encoding="utf-8")
    return rep

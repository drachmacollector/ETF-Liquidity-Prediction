"""P01 T01.8: universe feasibility and source registry, generated from the probe matrix."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from esw.config import Settings, get_settings
from esw.ingest.candidates import US_CANDIDATES

MIN_DAYS = 500  # System Specification §5.2 inclusion rule (US)
MIN_DAYS_IN = 250  # System Specification §5.3 (India)

US_GATE = {
    "US_COMM_PHYS": (3, ["GLD", "SLV"]),
    "US_COMM_FUT": (4, ["USO", "UNG"]),
    "US_BOND": (4, ["LQD"]),
    "US_INTL": (4, []),
    "US_CTRL": (3, []),
}
US_INTL_STRESS = ["EGPT", "GREK", "RSX", "ERUS"]  # at least one with NAV through its stress window


def _load(settings: Settings) -> pd.DataFrame:
    m = pd.read_csv(settings.path("reports") / "data" / "source_probe_matrix.csv", dtype=str).fillna("")
    m["rows_n"] = pd.to_numeric(m["rows"], errors="coerce")
    return m


def us_feasibility(m: pd.DataFrame) -> pd.DataFrame:
    out = []
    px_rows = m[m.source_id == "us_px_tiingo"].set_index("instrument_id")
    yf_rows = m[m.source_id == "us_px_yf"].set_index("instrument_id")
    for t, (group, nav_src) in US_CANDIDATES.items():
        iid = f"US:{t}"
        nav = m[(m.source_id == nav_src) & (m.instrument_id == iid)]
        nav_status = nav.status.iloc[0] if len(nav) else "NOT_PROBED"
        nav_days = nav.rows_n.iloc[0] if len(nav) else float("nan")
        px = px_rows.loc[iid] if iid in px_rows.index else None
        px_status = px["status"] if px is not None else "NOT_PROBED"
        if px_status != "OK" and iid in yf_rows.index and yf_rows.loc[iid, "status"] == "OK":
            px_status = "OK (yfinance; Tiingo pending)"
        elif px_status != "OK":
            px_status = f"{px_status} (Tiingo HTTP 429 rate limit; retry in P04; yfinance fallback)"
        if nav_status == "OK" and (pd.isna(nav_days) or nav_days >= MIN_DAYS):
            feas = "FEASIBLE"
        elif nav_status == "MANUAL_ONLY":
            feas = "FEASIBLE_MANUAL"
        else:
            feas = "INFEASIBLE"
        shares = (
            "y"
            if nav_src in {"us_iss_ishares", "us_iss_ssga", "us_iss_spdr_gold"} and nav_status == "OK"
            else "n/unknown"
        )
        out.append(
            {
                "ticker": t,
                "group": group,
                "nav_source": nav_src,
                "nav_status": nav_status,
                "nav_start": nav.history_start.iloc[0] if len(nav) else "",
                "nav_days": "" if pd.isna(nav_days) else int(nav_days),
                "price_source": "us_px_tiingo",
                "price_status": px_status,
                "price_start": px["history_start"] if px is not None else "",
                "price_end": px["history_end"] if px is not None else "",
                "shares_out": shares,
                "status": feas,
                "note": (nav.notes.iloc[0][:160] if len(nav) else ""),
            }
        )
    return pd.DataFrame(out)


def india_feasibility(m: pd.DataFrame) -> pd.DataFrame:
    rows = m[m.source_id == "in_mfapi"].copy()
    rows["nse_symbol"] = rows.notes.str.extract(r"nse_symbol_now=([^;]+);")[0]
    rows["name"] = rows.notes.str.split("; ").str[-1]
    rows["listed_now"] = ~rows.nse_symbol.fillna("").str.startswith("not in")
    rows["status"] = [
        "FEASIBLE" if (n >= MIN_DAYS_IN and listed) else ("TOO_SHORT" if listed else "NOT_LISTED_ON_NSE")
        for n, listed in zip(rows.rows_n.fillna(0), rows.listed_now, strict=False)
    ]
    rows["price_note"] = [
        "NSE archive from 2016-01; earlier via yfinance/manual" if (s and s < "2016-01-01") else "NSE archive"
        for s in rows.history_start
    ]
    return rows.rename(columns={"scope": "group", "history_start": "nav_start", "rows_n": "nav_days"})[
        ["group", "instrument_id", "nse_symbol", "name", "nav_start", "nav_days", "status", "price_note"]
    ].sort_values(["group", "nav_start"])


def gate(us: pd.DataFrame, ind: pd.DataFrame) -> list[dict]:
    res = []
    ok_us = us[us.status.isin(["FEASIBLE", "FEASIBLE_MANUAL"])]
    for g, (need, must) in US_GATE.items():
        sub = ok_us[ok_us.group == g]
        missing = [t for t in must if t not in set(sub.ticker)]
        auto = int((sub.status == "FEASIBLE").sum())
        res.append(
            {
                "group": g,
                "required": need,
                "feasible": len(sub),
                "feasible_scripted": auto,
                "must_include": ", ".join(must) or "-",
                "missing": ", ".join(missing) or "-",
                "pass": len(sub) >= need and not missing,
            }
        )
    stress = ok_us[ok_us.ticker.isin(US_INTL_STRESS)]
    res.append(
        {
            "group": "US_INTL stress fund (EGPT/GREK/RSX/ERUS)",
            "required": 1,
            "feasible": len(stress),
            "feasible_scripted": int((stress.status == "FEASIBLE").sum()),
            "must_include": "one of EGPT, GREK, RSX, ERUS",
            "missing": "-" if len(stress) else "all",
            "pass": len(stress) >= 1,
        }
    )
    feas_in = ind[ind.status == "FEASIBLE"]
    gs = feas_in[feas_in.group.isin(["IN_GOLD", "IN_SILVER"])]
    res.append(
        {
            "group": "IN_GOLD + IN_SILVER",
            "required": 10,
            "feasible": len(gs),
            "feasible_scripted": len(gs),
            "must_include": "GOLDETF, SILVERAG",
            "missing": ", ".join(s for s in ["GOLDETF", "SILVERAG"] if s not in set(gs.nse_symbol)) or "-",
            "pass": len(gs) >= 10 and {"GOLDETF", "SILVERAG"} <= set(gs.nse_symbol),
        }
    )
    intl = feas_in[feas_in.group == "IN_INTL"]
    res.append(
        {
            "group": "IN_INTL",
            "required": 3,
            "feasible": len(intl),
            "feasible_scripted": len(intl),
            "must_include": "MAFANG",
            "missing": "-" if "MAFANG" in set(intl.nse_symbol) else "MAFANG",
            "pass": len(intl) >= 3 and "MAFANG" in set(intl.nse_symbol),
        }
    )
    return res


def write_reports(settings: Settings | None = None) -> dict:
    s = settings or get_settings()
    m = _load(s)
    us, ind = us_feasibility(m), india_feasibility(m)
    g = gate(us, ind)
    out_dir: Path = s.path("reports") / "data"
    us.to_csv(out_dir / "universe_feasibility_us.csv", index=False)
    ind.to_csv(out_dir / "universe_feasibility_in.csv", index=False)
    lines = [
        "# P01 — Universe feasibility",
        "",
        "Generated by `esw.ingest.feasibility.write_reports()` from `reports/data/source_probe_matrix.csv`. "
        "Status: FEASIBLE = scripted NAV and price history ≥ the inclusion minimum; FEASIBLE_MANUAL = NAV history "
        "obtainable only by manual download (MI-04); INFEASIBLE = no NAV source found.",
        "",
        "## Feasibility gate (P01 T01.8)",
        "",
        pd.DataFrame(g).to_markdown(index=False),
        "",
        f"**Overall gate: {'PASS' if all(x['pass'] for x in g) else 'FAIL'}** "
        "(FEASIBLE_MANUAL instruments count as feasible; their MI-04 downloads become an entry condition of P04).",
        "",
        "## United States",
        "",
        us.drop(columns=["note"]).to_markdown(index=False),
        "",
        "Notes on infeasible and manual instruments:",
        "",
        *[f"- **{r.ticker}** ({r.status}): {r.note}" for r in us[us.status != "FEASIBLE"].itertuples()],
        "",
        "## India (ETFs found in AMFI NAVAll.txt; NAV history via mfapi.in, cross-checked with AMFI)",
        "",
        ind.to_markdown(index=False),
        "",
    ]
    (out_dir / "universe_feasibility.md").write_text("\n".join(lines), encoding="utf-8")
    return {"gate": g, "us": us, "in": ind}


# Fallback order and role per source (decided in P01; see reports/data/source_probe_report.md).
SOURCE_ROLES = {
    "us_px_tiingo": ("primary", "US daily prices (raw close + split factor)"),
    "us_px_yf": ("fallback", "US prices when Tiingo is missing or rate-limited"),
    "us_px_stooq": ("dropped", "browser check served to scripts"),
    "us_iss_spdr_gold": ("primary", "GLD/GLDM NAV, ounces, issuer premium"),
    "us_iss_ishares": ("primary", "iShares NAV and shares outstanding"),
    "us_iss_ssga": ("primary", "SSGA NAV and shares outstanding"),
    "us_iss_uscf": ("manual", "USCF NAV (MI-04)"),
    "us_iss_invesco": ("manual", "Invesco NAV (MI-04)"),
    "us_iss_vaneck": ("unavailable", "EGPT/RSX NAV not found; CRSP option (MI-06)"),
    "us_iss_globalx": ("manual", "GREK NAV (MI-04)"),
    "us_iss_xtrackers": ("manual", "ASHR NAV (MI-04)"),
    "us_iss_abrdn": ("manual", "SIVR/PPLT/PALL NAV (MI-04)"),
    "us_iss_teucrium": ("manual", "CORN/WEAT/SOYB NAV (MI-04)"),
    "us_iss_vanguard": ("manual", "BND/VOO NAV (MI-04, low priority)"),
    "us_wayback": ("unavailable", "no archived NAV files for delisted funds"),
    "us_edgar": ("primary", "SEC filings for capacity and operational events"),
    "in_bhav_udiff": ("primary", "NSE bhavcopy 2024-07-08 onwards (archives host)"),
    "in_bhav_legacy": ("primary", "NSE bhavcopy 2016-01-01 to 2024-07-05 (archives host)"),
    "in_bse_bhav": ("dropped", "403 to scripts"),
    "in_amfi_navall": ("primary", "latest NAVs; scheme master"),
    "in_amfi_hist": ("primary", "NAV history with upload timestamps (2010 onwards)"),
    "in_mfapi": ("fallback", "full NAV history mirror (incl. before 2010); 100% agreement with AMFI on test"),
    "in_mfapi_vs_amfi": ("check", "cross-check"),
    "in_yf_pre2016": ("fallback", "Indian prices before 2016; India VIX"),
    "in_spot_mcx": ("manual", "domestic spot (MI-05)"),
    "in_spot_ibja": ("manual", "domestic spot (MI-05)"),
    "in_indiavix": ("dropped", "nseindia.com API does not answer scripts; use yfinance ^INDIAVIX"),
    "in_amfi_aum": ("later", "monthly AUM endpoint to locate in P05"),
    "mkt_fred": ("primary", "volatility, credit, rates, FX"),
    "mkt_eia": ("primary_until_2024", "NYMEX curve to 2024-04-05"),
    "mkt_fut_yf": ("primary_after_2024", "futures contracts, metals, FX not on FRED, foreign indices"),
    "mkt_cal": ("primary", "exchange calendars"),
}


def build_source_registry(settings: Settings | None = None) -> pd.DataFrame:
    s = settings or get_settings()
    m = _load(s)
    rows = []
    for sid, grp in m.groupby("source_id", sort=True):
        role, purpose = SOURCE_ROLES.get(sid, ("unknown", ""))
        statuses = grp.status.value_counts().to_dict()
        rows.append(
            {
                "source_id": sid,
                "role": role,
                "purpose": purpose,
                "url_pattern": grp.url_pattern.iloc[0],
                "method": grp.method.iloc[0],
                "auth": grp.auth.iloc[0],
                "status_counts": "; ".join(f"{k}={v}" for k, v in statuses.items()),
                "history_start_min": min((x for x in grp.history_start if x), default=""),
                "history_end_max": max((x for x in grp.history_end if x), default=""),
                "rate_limit_note": grp.rate_limit_note.iloc[0],
                "tos_url": grp.tos_url.iloc[0],
                "user_acceptance": "accepted (D-004)" if role not in {"dropped", "unavailable"} else "n/a",
                "notes": grp.notes.iloc[0][:200],
            }
        )
    reg = pd.DataFrame(rows)
    reg.to_csv(s.path("reference") / "source_registry.csv", index=False)
    return reg

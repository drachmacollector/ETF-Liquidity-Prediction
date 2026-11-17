"""Assemble and write the P02 reference CSVs from the bootstrap builders (run once; then edit by hand).

Usage: `python -m esw.reference.bootstrap_write <instruments_in_draft.csv> <symbol_history_in_draft.csv>`
"""

from __future__ import annotations

import datetime as dt
import json
import sys
from pathlib import Path

import pandas as pd

from esw.config import get_settings
from esw.ingest import parsers as P
from esw.ingest.nse_bhav import BhavStore, bhav_url
from esw.reference.bootstrap_clock import build_corporate_actions_us, build_nav_clock
from esw.reference.bootstrap_in import load_samples
from esw.reference.bootstrap_us import build_instruments_us

US_COLS = [
    "instrument_id", "market", "ticker", "isin", "cusip", "cik", "name", "issuer", "group", "subgroup",
    "underlying", "legal_form", "rule_6c11", "listing_date", "delisting_date", "currency", "nav_source_id",
    "px_source_id", "shares_source_id", "include", "exclude_reason", "notes", "source_url", "verified_by",
    "verified_on",
]  # fmt: skip
IN_COLS = [
    "instrument_id", "market", "isin", "amfi_scheme_code", "name", "issuer", "is_mirae", "group", "subgroup",
    "underlying", "benchmark_name", "nse_symbol_current", "bse_code", "listing_date", "inception_date",
    "creation_unit_units", "include", "exclude_reason", "notes", "source_url", "verified_by", "verified_on",
]  # fmt: skip
SH_COLS = ["instrument_id", "exchange", "symbol", "isin", "valid_from", "valid_to", "source_url"]

# Hand facts read from primary documents (P01 notes §3).
IN_OVERRIDES = {
    "INF769K01KG6": {
        "inception_date": "2023-06-09",
        "note": "inception 2023-06-09 per SID ('Inception date of the Scheme: June 09, 2023'); first AMFI NAV 2023-06-12 (OQ-18 rule: SID preferred over listing notice)",
        "source_url": "https://www.miraeassetmf.co.in/docs/default-source/sid/sid_mirae-asset-silver-etf.pdf",
    },
}
SPLIT_RATIOS = [2, 5, 10, 20, 25, 50, 100]


def delisted_lineages(
    samples: pd.DataFrame, current_isins: set[str], sym_in: pd.DataFrame, amfi_2010: pd.DataFrame
) -> list[dict]:
    """Gold/silver ETF symbols seen in bhavcopies whose ISIN belongs to no current lineage."""
    known = set(sym_in["isin"].dropna()) | current_isins
    s = samples.dropna(subset=["isin"])
    s = s[s["isin"].str.startswith("INF") & s["symbol"].str.contains("GOLD|SILV", regex=True)]
    rows = []
    for isin, g in s.groupby("isin"):
        if isin in known:
            continue
        sym = g.sort_values("date")["symbol"].iloc[-1]
        code = amfi_2010.loc[amfi_2010["isin_growth"] == isin, "amfi_scheme_code"]
        name = amfi_2010.loc[amfi_2010["isin_growth"] == isin, "nav_name"]
        rows.append(
            {
                "isin": isin,
                "symbol": sym,
                "first": g["date"].min().date().isoformat(),
                "last": g["date"].max().date().isoformat(),
                "amfi": int(code.iloc[0]) if len(code) else None,
                "name": name.iloc[0] if len(name) else f"{sym} (name not in current AMFI files)",
            }
        )
    return rows


def india_unit_splits(raw: Path, ind: pd.DataFrame, store: BhavStore) -> pd.DataFrame:
    code_to_iid = dict(zip(ind["amfi_scheme_code"].astype(str), ind["instrument_id"], strict=False))
    iid_to_isin = dict(zip(ind["instrument_id"], ind["isin"], strict=False))
    rows = []
    for f in sorted(
        list((raw / "_probes" / "in_mfapi").glob("*.json")) + list((raw / "in_mfapi").glob("*.json"))
    ):
        iid = code_to_iid.get(f.stem)
        if iid is None:
            continue
        df = P.parse_mfapi(f.read_bytes()).sort_values("date")
        df = df[df["nav"] > 0].reset_index(drop=True)
        df["r"] = df["nav"].shift() / df["nav"]
        for _, x in df[(df["r"] > 1.8)].iterrows():
            ratio = min(SPLIT_RATIOS, key=lambda k: abs(k - x["r"]))
            close = abs(x["r"] / ratio - 1) < 0.08
            day = x["date"].date()
            prev = df.loc[df["date"] < x["date"], "date"].max().date()
            # price check: NSE close jump on the same day
            a, b = store.load(prev), store.load(day)
            isin = iid_to_isin[iid]
            pr = None
            if a is not None and b is not None:
                pa_, pb = a.loc[a["isin"] == isin, "close"], b.loc[b["isin"] == isin, "close"]
                if len(pa_) and len(pb) and pb.iloc[0] > 0:
                    pr = pa_.iloc[0] / pb.iloc[0]
            price_ok = pr is not None and abs(pr / ratio - 1) < 0.08
            rows.append(
                {
                    "instrument_id": iid,
                    "ex_date": day.isoformat(),
                    "type": "unit_split",
                    "ratio": float(ratio),
                    "applies_to": "both",
                    "verified": "y" if (close and price_ok) else "n",
                    "source_url": f"https://api.mfapi.in/mf/{f.stem} (NAV); {bhav_url(day)[0]} (NSE close)",
                    "notes": f"NAV ratio {x['r']:.3f} on {day} (previous NAV {prev}); NSE close ratio "
                    + (f"{pr:.3f}" if pr is not None else "n/a")
                    + (
                        ""
                        if (close and price_ok)
                        else "; not an exact split ratio or no price confirmation: check in P07 (possible merger/consolidation)"
                    ),
                }
            )
    return pd.DataFrame(rows)


def main(in_draft: str, sym_draft: str) -> None:
    settings = get_settings()
    ref, raw = settings.path("reference"), settings.path("raw")

    # ---- US
    us = build_instruments_us(settings)
    us_sym = pd.DataFrame(
        {
            "instrument_id": us["instrument_id"],
            "exchange": us["_exchange"],
            "symbol": us["ticker"],
            "isin": us["isin"],
            "valid_from": us["listing_date"],
            "valid_to": us["delisting_date"],
            "source_url": "Tiingo metadata (exchangeCode, startDate/endDate); listing-exchange moves not tracked",
        }
    )
    us[US_COLS].to_csv(ref / "instruments_us.csv", index=False)

    # ---- India
    ind = pd.read_csv(in_draft, dtype=str, keep_default_na=False)
    sym_in = pd.read_csv(sym_draft, dtype=str, keep_default_na=False)
    for isin, ov in IN_OVERRIDES.items():
        m = ind["isin"] == isin
        ind.loc[m, "inception_date"] = ov["inception_date"]
        ind.loc[m, "notes"] = ind.loc[m, "notes"].str.replace(
            "inception_date = first AMFI NAV date (proxy)", ov["note"], regex=False
        )
    amfi_2010 = P.parse_amfi_all_for_date(
        (raw / "_probes" / "in_amfi_hist" / "all_for_date_2010-01-04.json").read_bytes()
    )
    samples = load_samples(settings)
    extra = []
    for d in delisted_lineages(samples, set(ind["isin"]), sym_in, amfi_2010):
        grp = "IN_SILVER" if "SILV" in d["symbol"] else "IN_GOLD"
        extra.append(
            {
                "instrument_id": f"IN:{d['isin']}",
                "market": "IN",
                "isin": d["isin"],
                "amfi_scheme_code": "" if d["amfi"] is None else str(d["amfi"]),
                "name": d["name"],
                "issuer": "",
                "is_mirae": "false",
                "group": grp,
                "subgroup": "gold" if grp == "IN_GOLD" else "silver",
                "underlying": "Physical gold" if grp == "IN_GOLD" else "Physical silver",
                "benchmark_name": "",
                "nse_symbol_current": "",
                "bse_code": "",
                "listing_date": "",
                "inception_date": "",
                "creation_unit_units": "",
                "include": "false",
                "exclude_reason": "delisted_or_merged (not in the current AMFI scheme list)",
                "notes": f"NSE symbol {d['symbol']} seen in monthly bhavcopy samples {d['first']}..{d['last']}; kept for survivorship (P05 may recover prices; NAV needs the old AMFI code)",
                "source_url": "NSE CM bhavcopy samples (data/raw/in_bhav)",
                "verified_by": "agent (P02)",
                "verified_on": "2026-11-17",
            }
        )
        sym_in = pd.concat(
            [
                sym_in,
                pd.DataFrame(
                    [
                        {
                            "instrument_id": f"IN:{d['isin']}",
                            "exchange": "NSE",
                            "symbol": d["symbol"],
                            "isin": d["isin"],
                            "valid_from": "",
                            "valid_to": d["last"],
                            "source_url": "NSE CM bhavcopy monthly samples (approximate: last month seen)",
                        }
                    ]
                ),
            ],
            ignore_index=True,
        )
    ind = pd.concat([ind, pd.DataFrame(extra)], ignore_index=True)
    ind[IN_COLS].to_csv(ref / "instruments_in.csv", index=False)

    sh = pd.concat([us_sym, sym_in[SH_COLS]], ignore_index=True)
    sh.to_csv(ref / "symbol_history.csv", index=False)

    # ---- nav clock (all instruments with a known start)
    nc = build_nav_clock(us, ind[ind["include"] == "true"])
    nc.to_csv(ref / "nav_clock.csv", index=False)

    # ---- corporate actions
    store = BhavStore(settings, run_id="P02-reference")
    ca = pd.concat(
        [build_corporate_actions_us(raw, us), india_unit_splits(raw, ind, store)], ignore_index=True
    )
    ca = ca.sort_values(["instrument_id", "ex_date"])
    ca.to_csv(ref / "corporate_actions_manual.csv", index=False)
    print(
        json.dumps(
            {
                "us": len(us),
                "in": len(ind),
                "symbol_history": len(sh),
                "nav_clock": len(nc),
                "corporate_actions": len(ca),
            }
        )
    )
    print(dt.datetime.now())


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])

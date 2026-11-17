"""One-off builder for `reference/instruments_in.csv` and the Indian rows of `symbol_history.csv` (P02 T02.2-T02.3).

Inputs (all logged raw files):

* AMFI `NAVAll.txt` (P01) - scheme code, ISIN, name, AMC, category for every live ETF;
* mfapi.in NAV histories (P01 raw, plus new fetches for instruments added in P02) - first NAV date and
  NAV day counts;
* NSE bhavcopies: one per month 2007-01..2026-11 (`data/raw/in_bhav/`), plus extra days fetched by
  bisection to date each listing and each symbol/ISIN change exactly (first bhavcopy appearance);
* BSE bhavcopy 2026-11-16 - BSE scrip codes.

Lineage: a fund's NSE symbol and even its ISIN can change (AMC mergers, renames). Two (ISIN, symbol)
segments belong to the same lineage when they share an ISIN or when a symbol continues under a new
ISIN between consecutive samples. The instrument key is the **current** ISIN (`IN:<ISIN>`); earlier
ISINs are kept in `symbol_history.isin` and in `notes` so P05 can map old bhavcopy rows and old AMFI
codes to the instrument.
"""

from __future__ import annotations

import datetime as dt
import json
import re
from collections.abc import Callable
from pathlib import Path

import pandas as pd

from esw.config import Settings, get_settings
from esw.ingest import parsers as P
from esw.ingest.candidates import IN_CONTROL_ISINS, classify_india
from esw.ingest.http import PoliteSession
from esw.ingest.nse_bhav import BhavStore
from esw.runlog import append_ingest_log, iso_utc, sha256_file

VERIFIED_ON = "2026-11-17"
MIN_NAV_DAYS = 250  # System Specification §5.3
NAVALL_URL = "https://portal.amfiindia.com/spages/NAVAll.txt"
LIQUID = re.compile(r"Liquid|1D Rate|Overnight", flags=re.I)


# --------------------------------------------------------------------------- helpers
def _log(src: str, url: str, p: Path, root: Path, run_id: str, **kw) -> None:
    append_ingest_log(
        {
            "ts_utc": iso_utc(),
            "source": src,
            "instrument_id": kw.get("instrument_id"),
            "url": url,
            "path": str(p.relative_to(root)),
            "sha256": sha256_file(p),
            "bytes": p.stat().st_size,
            "http_status": 200,
            "status": "ok",
            "rows_parsed": kw.get("rows"),
            "date_min": kw.get("date_min"),
            "date_max": kw.get("date_max"),
            "error": None,
            "run_id": run_id,
        }
    )


def mfapi_history(code: int, settings: Settings, run_id: str, session: PoliteSession) -> pd.DataFrame:
    raw = settings.path("raw")
    for p in (raw / "_probes" / "in_mfapi" / f"{code}.json", raw / "in_mfapi" / f"{code}.json"):
        if p.exists():
            return P.parse_mfapi(p.read_bytes())
    url = f"https://api.mfapi.in/mf/{code}"
    resp = session.get(url)
    resp.raise_for_status()
    p = raw / "in_mfapi" / f"{code}.json"
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_bytes(resp.content)
    df = P.parse_mfapi(resp.content)
    first, last, n = P.date_span(df)
    _log("in_mfapi", url, p, settings.root, run_id, instrument_id=None, rows=n, date_min=first, date_max=last)
    return df


def bse_codes(settings: Settings, run_id: str, day: dt.date = dt.date(2026, 11, 16)) -> dict[str, str]:
    p = settings.path("raw") / "in_bse_bhav" / f"{day:%Y}" / f"BhavCopy_BSE_CM_0_0_0_{day:%Y%m%d}_F_0000.CSV"
    url = f"https://www.bseindia.com/download/BhavCopy/Equity/{p.name}"
    if not p.exists():
        s = PoliteSession(settings, browser=True)
        resp = s.get(url, headers={"Referer": "https://www.bseindia.com/"})
        resp.raise_for_status()
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(resp.content)
        _log("in_bse_bhav", url, p, settings.root, run_id, date_min=str(day), date_max=str(day))
    df = pd.read_csv(p, dtype=str)
    return dict(zip(df["ISIN"].str.strip(), df["FinInstrmId"].str.strip(), strict=False))


# --------------------------------------------------------------------------- lineages from samples
def load_samples(settings: Settings) -> pd.DataFrame:
    rows = []
    for p in sorted((settings.path("raw") / "in_bhav").rglob("*.zip")):
        df = P.parse_nse_bhavcopy(p.read_bytes())
        rows.append(df[["date", "isin", "symbol", "series"]])
    s = pd.concat(rows, ignore_index=True)
    s = s[s["series"].isin(["EQ", "BE"]) | s["series"].isna()]
    return s


# Lineage links the samples cannot show (symbol and ISIN changed on the same day).
MANUAL_LINKS = {
    # Motilal Oswal Nasdaq 100 ETF: N100 (INF247L01031) became MON100 (INF247L01AP3) with the
    # June 2021 unit split (NAV ratio 10.1 on 2021-06-21).
    "INF247L01AP3": ["I:INF247L01031", "S:N100"],
}


def lineages(samples: pd.DataFrame, seed_isins: set[str]) -> dict[str, dict]:
    """Group (isin, symbol) segments into lineages that contain a seed ISIN.

    Returns {seed_isin: {"isins": set, "symbols": set}}.
    """
    pairs = samples.dropna(subset=["isin"])[["isin", "symbol"]].drop_duplicates()
    # union-find over ISINs and symbols
    parent: dict[str, str] = {}

    def find(x: str) -> str:
        parent.setdefault(x, x)
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def union(a: str, b: str) -> None:
        parent[find(a)] = find(b)

    for isin, sym in pairs.itertuples(index=False):
        union(f"I:{isin}", f"S:{sym}")
    for isin, extra in MANUAL_LINKS.items():
        for x in extra:
            union(f"I:{isin}", x)
    out = {}
    for seed in seed_isins:
        root = find(f"I:{seed}")
        members = [k for k in list(parent) if find(k) == root]
        out[seed] = {
            "isins": {m[2:] for m in members if m.startswith("I:")},
            "symbols": {m[2:] for m in members if m.startswith("S:")},
        }
    return out


def _present(df: pd.DataFrame | None, isins: set[str], symbols: set[str]) -> pd.DataFrame:
    if df is None:
        return df
    m = df["isin"].isin(isins)
    if df["isin"].isna().all():  # early legacy files without ISIN: match by symbol
        m = df["symbol"].isin(symbols)
    return df[m & (df["series"].isin(["EQ", "BE"]))]


def _weekdays(a: dt.date, b: dt.date) -> list[dt.date]:
    return [
        a + dt.timedelta(days=i) for i in range((b - a).days + 1) if (a + dt.timedelta(days=i)).weekday() < 5
    ]


def bisect_first(store: BhavStore, lo: dt.date, hi: dt.date, pred: Callable[[pd.DataFrame], bool]) -> dt.date:
    """First trading day in (lo, hi] where `pred` holds, given pred is false on lo and true on hi.

    Days without a bhavcopy (holidays) are dropped from the search list as they are found.
    """
    days = _weekdays(lo + dt.timedelta(days=1), hi)
    left, right = 0, len(days) - 1
    while left < right:
        mid = (left + right) // 2
        df = store.load(days[mid])
        if df is None:
            del days[mid]
            right -= 1
            continue
        if pred(df):
            right = mid
        else:
            left = mid + 1
    return days[right]


def timeline(samples: pd.DataFrame, lin: dict, store: BhavStore) -> list[dict]:
    """Exact-dated (isin, symbol) segments for one lineage."""
    isins, symbols = lin["isins"], lin["symbols"]
    by_date = {}
    for d, g in samples.groupby("date"):
        hit = g[g["isin"].isin(isins)] if g["isin"].notna().any() else g[g["symbol"].isin(symbols)]
        by_date[d.date()] = hit.iloc[0] if len(hit) else None
    dates = sorted(by_date)
    segs: list[dict] = []
    prev_d, prev_key = None, None
    for d in dates:
        r = by_date[d]
        key = None if r is None else (None if pd.isna(r["isin"]) else r["isin"], r["symbol"])
        if key is not None and prev_key is None and segs:
            # re-appearance after months without trades on the sample days: continue the last
            # segment if nothing changed, otherwise compare against the last segment seen
            last = segs[-1]
            if key[1] == last["symbol"] and (
                key[0] == last["isin"] or key[0] is None or last["isin"] is None
            ):
                last["last_seen"] = d
                if last["isin"] is None and key[0] is not None:
                    last["isin"] = key[0]
                prev_d, prev_key = d, key
                continue
            prev_key = (last["isin"], last["symbol"])
        if key is not None and prev_key is None:
            # listing: bisect from the previous sample day
            start = d
            if prev_d is not None:
                start = bisect_first(store, prev_d, d, lambda df: len(_present(df, isins, symbols)) > 0)
            segs.append({"isin": key[0], "symbol": key[1], "valid_from": start, "last_seen": d})
        elif key is not None and prev_key is not None:
            same_symbol = key[1] == prev_key[1]
            same_isin = key[0] == prev_key[0] or key[0] is None or prev_key[0] is None
            if same_symbol and same_isin:
                segs[-1]["last_seen"] = d
                if segs[-1]["isin"] is None and key[0] is not None:
                    segs[-1]["isin"] = key[0]
            else:
                new_sym, new_isin = key[1], key[0]

                def is_new(df, s=new_sym, i=new_isin):
                    x = _present(df, isins, symbols)
                    return bool(((x["symbol"] == s) & ((x["isin"] == i) if i else True)).any())

                start = bisect_first(store, prev_d, d, is_new)
                segs.append({"isin": new_isin, "symbol": new_sym, "valid_from": start, "last_seen": d})
        elif key is None and prev_key is not None:
            segs[-1]["gap_after"] = d
        prev_d, prev_key = d, key
    # valid_to = day before the next segment starts; open for the current one
    for a, b in zip(segs, segs[1:], strict=False):
        a["valid_to"] = b["valid_from"] - dt.timedelta(days=1)
    if segs:
        last = segs[-1]
        last["valid_to"] = None if last["last_seen"] >= dates[-1] else last["last_seen"]
    # backfill missing ISIN for pre-2011 segments of the same symbol
    for a, b in zip(segs, segs[1:], strict=False):
        if a["isin"] is None and a["symbol"] == b["symbol"]:
            a["isin"] = b["isin"]
    return segs


# --------------------------------------------------------------------------- descriptive fields
def subgroup_and_benchmark(group: str, name: str) -> tuple[str, str, str]:
    n = name.lower()
    if group == "IN_GOLD":
        return "gold", "Physical gold", "Domestic price of physical gold"
    if group == "IN_SILVER":
        return "silver", "Physical silver", "Domestic price of physical silver"
    if group == "IN_INTL":
        if "hang seng" in n:
            idx = "Hang Seng TECH Index" if "tech" in n else "Hang Seng Index"
            return "hk_equity", "Hong Kong equities", idx
        if "fang" in n:
            return "us_equity", "US equities", "NYSE FANG+ Index"
        if "q50" in n:
            return "us_equity", "US equities", "Nasdaq Q-50 Index"
        if "nasdaq 100" in n:
            return "us_equity", "US equities", "Nasdaq-100 Index"
        if "s&p 500 top 50" in n:
            return "us_equity", "US equities", "S&P 500 Top 50 Index"
        return "intl_equity", "Overseas equities", ""
    if group == "IN_DEBT":
        if "bharat bond" in n:
            return "psu_bond", "PSU bonds (target maturity)", "Nifty Bharat Bond Index (matching maturity)"
        if "sdl" in n:
            return "sdl", "State development loans", ""
        if re.search(r"g-?sec|gilt", n):
            return "gsec", "Government securities", ""
        if LIQUID.search(name):
            return "liquid", "Overnight/liquid money market", ""
        return "debt_other", "Debt", ""
    if group == "IN_CTRL":
        for pat, idx in (
            ("bank", "Nifty Bank Index"),
            ("next 50", "Nifty Next 50 Index"),
            ("sensex", "BSE Sensex"),
            ("nifty 50", "Nifty 50 Index"),
        ):
            if pat in n:
                return "large_cap_in", "Indian equities", idx
        return "large_cap_in", "Indian equities", ""
    return "", "", ""


ISSUER_FIX = {"Mirae Asset Mutual Fund": "Mirae Asset"}


def build_instruments_in(
    settings: Settings | None = None, run_id: str = "P02-reference"
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Return (instruments_in, symbol_history_in)."""
    settings = settings or get_settings()
    raw = settings.path("raw")
    nav = P.parse_amfi_navall((raw / "_probes" / "in_amfi_navall" / "NAVAll.txt").read_bytes())
    etf = nav[nav["category"].fillna("").str.contains("ETF")].copy()
    etf["group"] = [classify_india(n, c) for n, c in zip(etf["scheme_name"], etf["category"], strict=True)]
    etf.loc[etf["isin_growth"].isin(IN_CONTROL_ISINS), "group"] = "IN_CTRL"
    etf = etf[etf["group"].notna()].copy()
    etf["isin"] = etf["isin_growth"].fillna(etf["isin_reinv"])
    counts = etf.groupby("isin")["amfi_scheme_code"].nunique()

    store = BhavStore(settings, run_id=run_id)
    current = store.load(dt.date(2026, 11, 16))
    cur_sym = dict(zip(current["isin"], current["symbol"], strict=False))
    bse = bse_codes(settings, run_id)
    samples = load_samples(settings)
    session = PoliteSession(settings)

    # seeds: in-scope ETFs (non-liquid) listed today
    seeds = {i for i in etf["isin"].dropna() if i in cur_sym}
    lins = lineages(samples, seeds)

    rows, sym_rows = [], []
    for r in etf.sort_values(["group", "scheme_name"]).itertuples(index=False):
        isin = r.isin
        name = r.scheme_name.strip()
        hist = mfapi_history(int(r.amfi_scheme_code), settings, run_id, session)
        nav_start = hist["date"].min() if len(hist) else pd.NaT
        nav_days = int(hist["nav"].notna().sum()) if len(hist) else 0
        sub, und, bench = subgroup_and_benchmark(r.group, name)
        notes = []
        include, reason = True, ""
        if pd.isna(isin):
            include, reason = False, "mapping_conflict"
            notes.append("no ISIN in NAVAll")
        elif counts.get(isin, 0) != 1:
            include, reason = False, "mapping_conflict"
            notes.append(f"{counts.get(isin, 0)} AMFI codes share this ISIN")
        if include and r.group == "IN_DEBT" and LIQUID.search(name):
            include, reason = False, "liquid_overnight (System Specification 5.3)"
        if include and isin not in cur_sym:
            include, reason = False, "not_listed_on_nse (absent from the 2026-11-16 bhavcopy)"
        if include and nav_days < MIN_NAV_DAYS:
            include, reason = False, f"too_short ({nav_days} NAV days < {MIN_NAV_DAYS})"
        listing = ""
        if isin in lins:
            segs = timeline(samples, lins[isin], store)
            if segs:
                listing = segs[0]["valid_from"].isoformat()
                old_isins = sorted({s["isin"] for s in segs if s["isin"] and s["isin"] != isin})
                old_syms = [s["symbol"] for s in segs if s["symbol"] != cur_sym.get(isin)]
                if old_isins:
                    notes.append(f"predecessor ISIN(s): {', '.join(old_isins)}")
                if old_syms:
                    notes.append(f"earlier NSE symbol(s): {', '.join(dict.fromkeys(old_syms))}")
                if segs[0]["valid_from"] <= dt.date(2007, 1, 31):
                    notes.append(
                        "listed before the first sampled bhavcopy (2007-01); listing date is a lower bound"
                    )
                for s in segs:
                    sym_rows.append(
                        {
                            "instrument_id": f"IN:{isin}",
                            "exchange": "NSE",
                            "symbol": s["symbol"],
                            "isin": s["isin"] or "",
                            "valid_from": s["valid_from"].isoformat(),
                            "valid_to": s["valid_to"].isoformat() if s["valid_to"] else "",
                            "source_url": "NSE CM bhavcopy (nsearchives.nseindia.com): monthly samples, change dates by bisection",
                        }
                    )
        if isin in bse:
            sym_rows.append(
                {
                    "instrument_id": f"IN:{isin}",
                    "exchange": "BSE",
                    "symbol": bse[isin],
                    "isin": isin,
                    "valid_from": "",
                    "valid_to": "",
                    "source_url": "BSE CM bhavcopy 2026-11-16 (scrip code; history not built)",
                }
            )
        notes.append("inception_date = first AMFI NAV date (proxy)")
        rows.append(
            {
                "instrument_id": f"IN:{isin}",
                "market": "IN",
                "isin": isin,
                "amfi_scheme_code": int(r.amfi_scheme_code),
                "name": name,
                "issuer": ISSUER_FIX.get(r.amc, r.amc.replace(" Mutual Fund", "")),
                "is_mirae": "true" if "Mirae" in r.amc else "false",
                "group": r.group,
                "subgroup": sub,
                "underlying": und,
                "benchmark_name": bench,
                "nse_symbol_current": cur_sym.get(isin, ""),
                "bse_code": bse.get(isin, ""),
                "listing_date": listing,
                "inception_date": "" if pd.isna(nav_start) else nav_start.date().isoformat(),
                "creation_unit_units": "",
                "include": "true" if include else "false",
                "exclude_reason": reason,
                "notes": "; ".join(notes),
                "source_url": NAVALL_URL,
                "verified_by": "agent (P02)",
                "verified_on": VERIFIED_ON,
                "_nav_days": nav_days,
            }
        )
    return pd.DataFrame(rows), pd.DataFrame(sym_rows)


def save_json(obj, path: Path) -> None:
    path.write_text(json.dumps(obj, indent=1, default=str), encoding="utf-8")

"""P04 T04.6 / P05: coverage of staged prices and NAV against the trading calendar."""

from __future__ import annotations

import pandas as pd

from esw.config import Settings, get_settings
from esw.reference import load
from esw.reference.calendars import load_calendar


def _gaps(dates: pd.Series, cal_days: pd.DatetimeIndex) -> int:
    """Longest run of consecutive expected trading days with no row."""
    have = set(pd.to_datetime(dates))
    best = cur = 0
    for d in cal_days:
        if d in have:
            cur = 0
        else:
            cur += 1
            best = max(best, cur)
    return best


def us_coverage(settings: Settings | None = None) -> pd.DataFrame:
    settings = settings or get_settings()
    staged = settings.path("staged")
    inst = load("instruments_us", settings)
    cal = load_calendar(settings)
    xnys = cal[(cal["market"] == "XNYS") & cal["is_trading"]]["date"]
    px = pd.read_parquet(staged / "us_px" / "us_px_tiingo.parquet")
    navs = {p.stem: pd.read_parquet(p) for p in (staged / "us_nav").glob("*.parquet")}
    manual = set()
    for p in settings.path("manual_drop").rglob("*"):
        if p.is_file():
            manual.add(p.name.split("-")[0].split("_")[0].upper())
    today = pd.Timestamp.today().normalize()
    rows = []
    for r in inst.itertuples(index=False):
        t = r.ticker
        p = px[px["ticker"] == t]
        src = "us_iss_uscf" if r.nav_source_id == "us_iss_uscf" else r.nav_source_id
        n = navs.get(src, pd.DataFrame(columns=["ticker", "date", "nav", "shares_out", "issuer_prem_bps"]))
        n = n[n["ticker"] == t]
        start = max(r.listing_date, pd.Timestamp("2004-01-01"))
        end = r.delisting_date if pd.notna(r.delisting_date) else min(today, xnys.max())
        exp = xnys[(xnys >= start) & (xnys <= end)]
        pfirst = p["date"].min() if len(p) else pd.NaT
        nfirst = n["date"].min() if len(n) else pd.NaT
        exp_px = exp[exp >= pfirst] if len(p) else exp
        exp_nav = exp[exp >= nfirst] if len(n) else exp
        rows.append(
            {
                "ticker": t,
                "include": r.include,
                "px_first": pfirst.date() if len(p) else None,
                "px_last": p["date"].max().date() if len(p) else None,
                "px_days": int(p["date"].isin(exp).sum()),
                "px_expected_days": len(exp_px),
                "px_coverage_pct": round(100 * p["date"].isin(exp_px).sum() / max(len(exp_px), 1), 2),
                "px_longest_gap": _gaps(p["date"], pd.DatetimeIndex(exp_px)) if len(p) else None,
                "nav_first": nfirst.date() if len(n) else None,
                "nav_last": n["date"].max().date() if len(n) else None,
                "nav_days": int(n["date"].isin(exp).sum()),
                "nav_expected_days": len(exp_nav),
                "nav_coverage_pct": round(100 * n["date"].isin(exp_nav).sum() / max(len(exp_nav), 1), 2)
                if len(n)
                else 0.0,
                "nav_longest_gap": _gaps(n["date"], pd.DatetimeIndex(exp_nav)) if len(n) else None,
                "nav_start_lag_days": (nfirst - r.listing_date).days if len(n) else None,
                "shares_days": int(n["shares_out"].notna().sum()) if "shares_out" in n else 0,
                "issuer_prem_days": int(n["issuer_prem_bps"].notna().sum()) if "issuer_prem_bps" in n else 0,
                "sources_used": f"us_px_tiingo; {src if len(n) else '-'}",
                "manual_files": "y" if t in manual else "n",
            }
        )
    return pd.DataFrame(rows)


def in_coverage(
    settings: Settings | None = None, trading_days: pd.DatetimeIndex | None = None
) -> pd.DataFrame:
    """P05 T05.8: per Indian instrument, against bhavcopy trading days (>= 500 rows) after listing."""
    settings = settings or get_settings()
    st = settings.path("staged")
    inst = load("instruments_in", settings)
    px = pd.read_parquet(st / "in_bhav" / "in_bhav_nse.parquet")
    amfi = pd.read_parquet(st / "in_nav" / "in_amfi_hist.parquet")
    mf = pd.read_parquet(st / "in_nav" / "in_mfapi.parquet")
    if trading_days is None:
        summ = pd.read_parquet(st / "in_bhav" / "bhav_day_summary.parquet")
        trading_days = pd.DatetimeIndex(sorted(summ.loc[summ["rows"] >= 500, "date"]))
    sh = load("symbol_history", settings)
    rows = []
    for r in inst.itertuples(index=False):
        p = px[px["instrument_id"] == r.instrument_id]
        a = amfi[amfi["instrument_id"] == r.instrument_id]
        m = mf[mf["instrument_id"] == r.instrument_id]
        nav_dates = pd.concat([a["date"], m["date"]]).drop_duplicates()
        first = p["date"].min() if len(p) else pd.NaT
        exp = trading_days[trading_days >= first] if len(p) else trading_days[:0]
        nfirst = nav_dates.min() if len(nav_dates) else pd.NaT
        exp_nav = (
            trading_days[trading_days >= max(nfirst, first)]
            if len(nav_dates) and len(p)
            else trading_days[:0]
        )
        syms = sh[(sh["instrument_id"] == r.instrument_id) & (sh["exchange"] == "NSE")]["symbol"].unique()
        rows.append(
            {
                "instrument_id": r.instrument_id,
                "isin": r.isin,
                "symbols": ";".join(syms),
                "include": r.include,
                "px_first": first.date() if len(p) else None,
                "px_last": p["date"].max().date() if len(p) else None,
                "px_days": int(p["date"].isin(exp).sum()),
                "expected_days": len(exp),
                "px_coverage_pct": round(100 * p["date"].isin(exp).sum() / max(len(exp), 1), 2)
                if len(p)
                else 0.0,
                "zero_volume_days": int((p["volume"] == 0).sum()) if len(p) else 0,
                "mapped_by_symbol_days": int((p["mapped_by"] == "symbol").sum()) if len(p) else 0,
                "nav_first": nfirst.date() if len(nav_dates) else None,
                "nav_last": nav_dates.max().date() if len(nav_dates) else None,
                "nav_days": int(nav_dates.isin(exp_nav).sum()),
                "nav_coverage_pct": round(100 * nav_dates.isin(exp_nav).sum() / max(len(exp_nav), 1), 2)
                if len(exp_nav)
                else 0.0,
                "nav_amfi_days": len(a),
                "nav_mfapi_only_days": int((~m["date"].isin(a["date"])).sum()),
            }
        )
    return pd.DataFrame(rows)

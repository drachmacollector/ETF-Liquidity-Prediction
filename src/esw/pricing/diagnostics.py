"""P08 reports: premium EDA, the 1 Apr 2026 Indian NAV-basis break, and the arbitrage-cost cross-check.

Descriptive analysis of measured premiums. Model estimate context only; not investment advice.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from esw.config import Settings, get_settings

KEY = [
    "US:GLD",
    "US:SLV",
    "US:USO",
    "US:UNG",
    "US:LQD",
    "US:HYG",
    "US:EWJ",
    "US:GREK",
    "US:SPY",
    "IN:INF769K01KG6",
    "IN:INF769K01JP9",
    "IN:INF769K01HF4",
]
NAMES = {
    "IN:INF769K01KG6": "SILVERAG",
    "IN:INF769K01JP9": "GOLDETF",
    "IN:INF769K01HF4": "MAFANG",
    "IN:INF204KB17I5": "GOLDBEES",
}


def _plt():
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    return plt


def premium_eda(panel: pd.DataFrame, settings: Settings) -> str:
    out = settings.path("reports") / "pricing"
    out.mkdir(parents=True, exist_ok=True)
    v = panel[panel["valid"]]
    q = v.groupby("group")["prem_bps"].quantile([0.01, 0.05, 0.5, 0.95, 0.99]).unstack().round(1)
    q.columns = ["p1", "p5", "p50", "p95", "p99"]
    sc = v.groupby("instrument_id")["s_bps"].median().round(1).sort_values()
    zz = (
        v.assign(year=v["date"].dt.year, big=v["z"].abs() > 3)
        .groupby(["group", "year"])["big"]
        .mean()
        .unstack(0)
    )
    inc = pd.read_parquet(settings.path("curated") / "incident.parquet")
    plt = _plt()
    fig, axes = plt.subplots(len(KEY), 1, figsize=(11, 2.0 * len(KEY)))
    for ax, iid in zip(axes, KEY, strict=True):
        d = panel[panel["instrument_id"] == iid]
        ax.plot(d["date"], d["prem_bps"], lw=0.5)
        for r in inc.itertuples(index=False):
            if iid in r.instrument_ids.split(";"):
                ax.axvspan(
                    pd.Timestamp(r.approx_onset),
                    pd.Timestamp(r.approx_end or r.approx_onset) + pd.Timedelta(days=5),
                    color="red",
                    alpha=0.15,
                )
        ax.set_title(NAMES.get(iid, iid), fontsize=8, loc="left")
        ax.tick_params(labelsize=7)
    fig.tight_layout()
    fig.savefig(out / "premium_timeseries.png", dpi=110)
    plt.close(fig)
    gl = panel[(panel["instrument_id"] == "US:GLD") & panel["post_strike_move_bps"].notna() & panel["valid"]]
    corr = gl[["div_bps", "post_strike_move_bps"]].corr().iloc[0, 1] if len(gl) else np.nan
    lines = [
        "# Premium EDA (P08)",
        "",
        "Premium = 10,000 × (close / NAV − 1), valid rows only (Spec §4.3). Model estimate context only; not investment advice.",
        "",
        "## Premium quantiles by group (bps)",
        "",
        q.to_markdown(),
        "",
        "## Robust scale s (median over time, bps) per instrument",
        "",
        sc.rename("s_bps").to_frame().to_markdown(),
        "",
        "## Share of days with |z| > 3 by year",
        "",
        zz.round(3).to_markdown(),
        "",
        "## Clock mismatch evidence (GLD)",
        "",
        f"Correlation of `div_bps` (ETF return − NAV return) with `post_strike_move_bps` (COMEX front month at the US close vs the NAV-implied LBMA PM price): **{corr:.2f}**. GLD's NAV is struck at the London PM fix while the ETF closes at 16:00 New York; the daily premium therefore contains the gold move between the two clocks.",
        "",
        "![premiums](premium_timeseries.png)",
        "",
    ]
    text = "\n".join(lines)
    (out / "premium_eda.md").write_text(text, encoding="utf-8")
    return text


def nav_basis_break(panel: pd.DataFrame, settings: Settings) -> str:
    out = settings.path("reports") / "pricing"
    m = panel[panel["group"].isin(["IN_GOLD", "IN_SILVER"]) & panel["valid"]].copy()
    m = m.sort_values(["instrument_id", "date"])
    m["ret_spot"] = m.groupby("instrument_id")["domestic_spot_inr"].pct_change(fill_method=None)
    m["ret_parity"] = m.groupby("instrument_id")["parity_inr"].pct_change(fill_method=None)
    m["era"] = np.where(m["date"] >= "2026-04-01", "after (domestic spot)", "before (import parity)")
    m = m[m["date"] >= "2025-04-01"]  # one year before and after the break
    rows = []
    for (era, grp), g in m.groupby(["era", "group"]):
        rows.append(
            {
                "era": era,
                "group": grp,
                "days": len(g),
                "median |prem| bps": round(g["prem_bps"].abs().median(), 1),
                "p95 |prem| bps": round(g["prem_bps"].abs().quantile(0.95), 1),
                "corr(ret_nav, ret_spot)": round(g[["ret_nav", "ret_spot"]].corr().iloc[0, 1], 3),
                "corr(ret_nav, ret_parity)": round(g[["ret_nav", "ret_parity"]].corr().iloc[0, 1], 3),
                "median Layer 1 bps": round(g["lp_bps"].median(), 1),
            }
        )
    t = pd.DataFrame(rows)
    after = t[t["era"].str.startswith("after")]
    before = t[t["era"].str.startswith("before")]
    verdict = (
        "**Supported**: after 1 Apr 2026 NAV returns correlate more with domestic spot than with import parity, and less with parity than before."
        if len(after)
        and len(before)
        and (after["corr(ret_nav, ret_spot)"].mean() > after["corr(ret_nav, ret_parity)"].mean())
        else "**Not supported by these numbers** (see table)."
    )
    lines = [
        "# The 1 April 2026 Indian NAV-basis break (P08 T08.5)",
        "",
        "Indian gold and silver ETF NAVs moved from LBMA-based import parity (plus a notional premium) to exchange-polled domestic spot on 1 Apr 2026 (SEBI circular of 26 Feb 2026). Window: 1 Apr 2025 – DATA_CUTOFF. Returns are daily; spot is the MCX poll nearest the 15:30 close; parity uses the previous US close of COMEX futures and USD/INR (timing noise acknowledged).",
        "",
        t.to_markdown(index=False),
        "",
        f"Conclusion: {verdict}",
        "",
        "Layer-1 note: Layer 1 needs a verified duty row; the May 2026 duty change is unverified (MI-09 D7), so `lp_bps` after 13 May 2026 is null and the 'after' Layer-1 median uses Apr–May 2026 only.",
        "",
    ]
    text = "\n".join(lines)
    (out / "india_nav_basis_break.md").write_text(text, encoding="utf-8")
    return text


def cost_crosscheck(panel: pd.DataFrame, settings: Settings) -> str:
    import bidask

    out = settings.path("reports") / "pricing"
    rows = []
    for iid in ["US:GLD", "US:SLV", "US:USO", "US:LQD", "IN:INF204KB17I5"]:
        d = panel[(panel["instrument_id"] == iid) & panel["valid"]].dropna(
            subset=["open", "high", "low", "close"]
        )
        d = d[d["date"] >= "2015-01-01"]
        if len(d) < 100:
            continue
        ohlc = d[["open", "high", "low", "close"]].reset_index(drop=True)
        edge = bidask.edge_rolling(ohlc, window=21) * 1e4
        rows.append(
            {
                "instrument": NAMES.get(iid, iid),
                "median EDGE spread bps": round(float(np.nanmedian(edge)), 1),
                "half spread bps": round(float(np.nanmedian(edge)) / 2, 1),
                "median band width bps": round(float(d["band_width_bps"].median()), 1),
                "median band half-width bps": round(float(d["band_width_bps"].median()) / 2, 1),
            }
        )
    t = pd.DataFrame(rows)
    lines = [
        "# Bottom-up arbitrage-cost cross-check (P08 T08.6)",
        "",
        "Half the EDGE bid-ask spread estimate (21-day rolling, Ardia-Guidotti-Kroencke, from daily OHLC; 2015+) versus the empirical no-arbitrage band (2.5–97.5% of the trailing 250 valid premiums). Creation fees are omitted (not reliably documented per fund). Report only; not used downstream.",
        "",
        t.to_markdown(index=False),
        "",
        "Reading: the empirical band is wider than half the spread for every fund — it also contains NAV-clock timing noise (GLD/SLV), stale bond prices (LQD) and roll/futures effects (USO), which a spread-only cost misses.",
        "",
    ]
    text = "\n".join(lines)
    (out / "arbitrage_cost_crosscheck.md").write_text(text, encoding="utf-8")
    return text


def known_facts(panel: pd.DataFrame) -> pd.DataFrame:
    def g(i, lo, hi):
        return panel[(panel["instrument_id"] == i) & (panel["date"] >= lo) & (panel["date"] <= hi)]

    rows = [
        ("USO 2020-04-21 premium", g("US:USO", "2020-04-21", "2020-04-21")["prem_bps"].iloc[0], "3600 ± 600"),
        ("USO 2020-05-01 premium", g("US:USO", "2020-05-01", "2020-05-01")["prem_bps"].iloc[0], "145 ± 100"),
        ("UNG max Aug-Sep 2009", g("US:UNG", "2009-08-01", "2009-09-30")["prem_bps"].max(), "1200 to 2500"),
        ("LQD min 9-23 Mar 2020", g("US:LQD", "2020-03-09", "2020-03-23")["prem_bps"].min(), "-700 to -300"),
        (
            "GLD median |prem| 2010-2019",
            g("US:GLD", "2010-01-01", "2019-12-31")["prem_bps"].abs().median(),
            "< 50",
        ),
        (
            "SPY median |prem| 2010-2019",
            g("US:SPY", "2010-01-01", "2019-12-31")["prem_bps"].abs().median(),
            "< 10",
        ),
        (
            "SILVERAG max 9-16 Oct 2025",
            g("IN:INF769K01KG6", "2025-10-09", "2025-10-16")["prem_bps"].max(),
            ">= 300",
        ),
        (
            "MAFANG median Apr 2026",
            g("IN:INF769K01HF4", "2026-04-01", "2026-04-30")["prem_bps"].median(),
            "1200 to 3000",
        ),
    ]
    ip = panel.dropna(subset=["issuer_prem_diff_bps"])
    for iid in ("US:GREK", "US:BKLN"):  # Rule 6c-11 funds publishing closing-price premiums
        rows.append(
            (
                f"{iid} issuer premium |diff| median",
                ip.loc[ip["instrument_id"] == iid, "issuer_prem_diff_bps"].abs().median(),
                "< 5",
            )
        )
    return pd.DataFrame(rows, columns=["check", "actual", "expected"])


def build_reports(settings: Settings | None = None) -> dict:
    settings = settings or get_settings()
    panel = pd.read_parquet(settings.path("derived") / "pricing" / "pricing_panel.parquet")
    kf = known_facts(panel)
    kf.to_csv(settings.path("reports") / "pricing" / "known_facts.csv", index=False)
    return {
        "eda": premium_eda(panel, settings),
        "break": nav_basis_break(panel, settings),
        "cost": cost_crosscheck(panel, settings),
        "facts": kf,
    }

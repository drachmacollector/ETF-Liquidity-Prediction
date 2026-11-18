"""P07 reports: quality report (+ flags CSV) and the data dictionary."""

from __future__ import annotations

import pandas as pd

from esw.config import Settings, get_settings

DICT = {
    "instrument": (
        "instrument_id",
        "reference tables",
        "known at all times",
        {
            "instrument_id": "US:<ticker> or IN:<ISIN>",
            "group": "Spec §5.1 group",
            "nav_basis_default": "first nav_clock basis",
            "include": "in the modelling universe",
            "listing_date": "first trading day (India: first bhavcopy appearance or inception)",
        },
    ),
    "calendar": (
        "market, date",
        "exchange_calendars; India: NSE bhavcopy presence for past dates",
        "scheduled: known at all times",
        {"is_trading": "trading day", "session_type": "regular | half | special"},
    ),
    "px_daily": (
        "instrument_id, date",
        "Tiingo (US), NSE bhavcopy (India)",
        "US t 16:15 New York; India t 18:00 IST",
        {
            "close": "official close, unadjusted for dividends, on the current split basis",
            "volume": "units, current split basis",
            "split_factor_applied": "factor by which raw prices were divided",
            "mapped_by_symbol": "India pre-2011 rows mapped by symbol",
        },
    ),
    "nav_daily": (
        "instrument_id, date",
        "issuer files/APIs (US), AMFI then mfapi (India)",
        "US t 20:00 New York; India AMFI upload time (else t 23:59 IST)",
        {
            "nav": "NAV per unit, current split basis",
            "shares_out": "units outstanding (US issuers where published)",
            "nav_source": "source used",
        },
    ),
    "issuer_premium": (
        "instrument_id, date",
        "SPDR Gold, Invesco, Global X files",
        "t 20:00 New York",
        {"issuer_prem_bps": "issuer-published premium (their clock/midpoint)"},
    ),
    "series_daily": (
        "series_id, date",
        "FRED, EIA, yfinance, derived",
        "t + catalogue lag (business days), 18:00 source local time",
        {
            "value": "series value",
            "ret": "log return with roll days nulled (continuous futures)",
            "roll_flag": "detected roll day",
        },
    ),
    "in_spot_polls": (
        "metal, polled_at_ist",
        "MCX polled spot (MI-05)",
        "the poll time",
        {"price_inr": "INR per 10 g (gold) or per kg (silver)"},
    ),
    "corporate_action": (
        "instrument_id, ex_date, type, applies_to",
        "reference",
        "known at all times (historical, verified)",
        {"ratio": "new units per old unit"},
    ),
    "operational_event": (
        "event_id",
        "reference (P03)",
        "event known_at (never effective_at)",
        {"effective_at": "date the action takes effect"},
    ),
    "incident": (
        "incident_id",
        "reference (P03)",
        "first_public_known_at",
        {"mechanisms": "M1-M8 (pass-1 labels, MI-08 pending)"},
    ),
    "capacity": (
        "instrument_id, as_of, metric, known_at, value",
        "SEC filings",
        "EDGAR acceptance time",
        {"metric": "registered_shares_total | registered_shares_remaining | shares_outstanding_reported"},
    ),
    "duty": (
        "metal, effective_from",
        "reference (Budget documents)",
        "known at all times; unverified rows unused",
        {"total_pct": "effective import duty %"},
    ),
    "band_regime": (
        "market, exchange, group, effective_from",
        "reference (exchange circulars)",
        "known at all times",
        {"band_init_pct": "initial band %"},
    ),
    "nav_clock": (
        "instrument_id, effective_from",
        "reference",
        "known at all times",
        {"nav_basis": "Spec §6.3 basis code"},
    ),
    "quality_flag": ("table, key, check_id", "P07 checks", "-", {"severity": "info | warn | error"}),
}


def write_reports(settings: Settings | None = None, res: dict | None = None) -> None:
    settings = settings or get_settings()
    cur = settings.path("curated")
    out = settings.path("reports") / "data"
    flags = pd.read_parquet(cur / "quality_flag.parquet")
    flags.to_csv(out / "quality_flags.csv", index=False)
    px = pd.read_parquet(
        cur / "px_daily.parquet", columns=["instrument_id", "date", "price_source", "mapped_by_symbol"]
    )
    nav = pd.read_parquet(cur / "nav_daily.parquet", columns=["instrument_id", "date", "nav_source"])
    inst = pd.read_parquet(cur / "instrument.parquet")
    cut = (cur / "DATA_CUTOFF.txt").read_text().strip()
    ca = pd.read_parquet(cur / "corporate_action.parquet")
    g = flags[flags["check_id"] == "gap_gt_25pct"]
    lines = [
        "# Quality report (P07)",
        "",
        f"**DATA_CUTOFF = {cut}** (latest date with price and NAV for ≥ 90% of included instruments in both markets).",
        "",
        "## Precedence used",
        "",
        "- US prices: Tiingo raw (all instruments; yfinance fallback not needed). US NAV: the issuer source in `instruments_us.nav_source_id`.",
        "- India prices: NSE bhavcopy (BSE fallback not needed). India NAV: AMFI history, mfapi for dates AMFI lacks.",
        f"- Rows: px_daily {len(px):,}; nav_daily {len(nav):,} ({(nav['nav_source'] == 'in_mfapi').sum():,} from mfapi); India price rows mapped by symbol {int(px['mapped_by_symbol'].sum()):,}.",
        "",
        "## Flags by check and severity",
        "",
        flags.groupby(["check_id", "severity"]).size().rename("n").reset_index().to_markdown(index=False),
        "",
        "## Errors and resolution",
        "",
        "Split candidates (`error`) found on the first build: 24, all in Indian ETFs where price and NAV change unit basis on different days (often with an ISIN change). Each was resolved by a verified `unit_split` row (price leg and NAV leg dated separately) in `reference/corporate_actions_manual.csv`; ICICI's 2018-07-03 seed row was dropped (no jump; a gap in the mfapi history). **Unresolved errors: 0.**",
        "",
        f"Corporate actions applied: {len(ca)} ({(ca['instrument_id'].str.startswith('US')).sum()} US, {(ca['instrument_id'].str.startswith('IN')).sum()} India).",
        "",
        "USO reference test: premium +838 bps (20 Apr 2020), +3,641 (21 Apr), +866 (22 Apr), +145 (1 May); continuous across the 1-for-8 reverse split on 29 Apr (both legs adjusted).",
        "",
        "## |close/NAV − 1| > 25% (`warn`), all annotated",
        "",
        g.groupby("instrument_id").size().rename("days").reset_index().to_markdown(index=False),
        "",
        "Annotations: incident windows from `reference/incidents.csv` (Indian international ETFs under the overseas cap; USO 21 Apr 2020) and `reference/gap_annotations.csv` (EWH Oct 1997, Hang Seng BeES Mar 2020, N100 2018, Axis gold split day).",
        "",
        "## NAV spikes (`warn`, excluded from labels in P08)",
        "",
        "Rule: NAV return beyond 5 robust SD on t and t+1 with opposite signs, NAV back near its previous level, and the price making neither move. These are timing artefacts on volatile days (London-fixed SLV, Asian closes, Indian March-2020 NAVs).",
        "",
        flags[flags["check_id"] == "nav_spike"][["instrument_id", "date"]].to_markdown(index=False),
        "",
        "## Stale NAV runs (`info`)",
        "",
        f"{(flags['check_id'] == 'nav_stale_run').sum()} runs of ≥ 3 unchanged NAVs; kept (often a closed-market signal).",
        "",
        "## Final coverage",
        "",
        f"Included instruments: {int(inst['include'].sum())} ({int((inst['include'] & (inst['market'] == 'US')).sum())} US, {int((inst['include'] & (inst['market'] == 'IN')).sum())} India). Per-instrument coverage: `reports/data/coverage_us.md`, `coverage_in.md`.",
        "",
    ]
    (out / "quality_report.md").write_text("\n".join(lines), encoding="utf-8")
    dd = [
        "# Data dictionary (curated store, P07)",
        "",
        "Every table carries `source`; time-stamped tables carry `known_at` (UTC) per System Specification §7; `ingested_at` comes from the ingest manifest.",
        "",
    ]
    for name, (pk, src, ka, cols) in DICT.items():
        p = cur / f"{name}.parquet"
        if not p.exists():
            continue
        df = pd.read_parquet(p)
        dd += [
            f"## {name}",
            "",
            f"- Primary key: `{pk}`; source: {src}; `known_at`: {ka}; rows: {len(df):,}",
            "",
            "| Column | Type | Description |",
            "|---|---|---|",
        ]
        dd += [f"| `{c}` | {df[c].dtype} | {cols.get(c, '')} |" for c in df.columns]
        dd.append("")
    (out / "data_dictionary.md").write_text("\n".join(dd), encoding="utf-8")

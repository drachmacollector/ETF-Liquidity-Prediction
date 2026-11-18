"""P03 T03.8: `reports/catalogue/catalogue_report.md` and `timeline.png`."""

from __future__ import annotations

import pandas as pd

from esw.config import Settings, get_settings


def _read(settings: Settings, name: str) -> pd.DataFrame:
    return pd.read_csv(settings.path("reference") / f"{name}.csv", dtype=str, keep_default_na=False)


def timeline(inc: pd.DataFrame, path) -> None:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    colors = {
        "CRE": "#c0392b",
        "STL": "#2471a3",
        "UND": "#b7950b",
        "LIQ": "#7d3c98",
        "DEM": "#d35400",
        "MKT": "#566573",
    }
    df = inc.copy()
    df["start"] = pd.to_datetime(df["approx_onset"])
    df["end"] = pd.to_datetime(df["approx_end"].replace("", None)).fillna(pd.Timestamp("2026-11-17"))
    df = df.sort_values(["market", "start"], ascending=[False, True]).reset_index(drop=True)
    fig, ax = plt.subplots(figsize=(11, 0.32 * len(df) + 1.5))
    for i, r in df.iterrows():
        width = max((r["end"] - r["start"]).days, 20)
        ax.barh(
            i,
            width,
            left=r["start"],
            color=colors.get(r["primary_family"], "grey"),
            alpha=0.5 if r["near_miss"] == "y" else 0.95,
            hatch="//" if r["near_miss"] == "y" else None,
        )
    ax.set_yticks(range(len(df)))
    ax.set_yticklabels(df["incident_id"], fontsize=7)
    ax.axvline(pd.Timestamp("2020-01-01"), color="black", lw=0.8, ls="--")
    ax.text(pd.Timestamp("2020-02-01"), -0.8, "lockbox from 2020", fontsize=7)
    handles = [plt.Rectangle((0, 0), 1, 1, color=c) for c in colors.values()]
    ax.legend(
        handles,
        list(colors),
        fontsize=7,
        loc="lower left",
        title="family (hatched = near-miss)",
        title_fontsize=7,
    )
    ax.set_title("Incident catalogue: approximate onset to end")
    fig.tight_layout()
    fig.savefig(path, dpi=120)
    plt.close(fig)


def build_report(settings: Settings | None = None, agreement: dict | None = None) -> str:
    settings = settings or get_settings()
    out_dir = settings.path("reports") / "catalogue"
    out_dir.mkdir(parents=True, exist_ok=True)
    inc, ev, cap = (
        _read(settings, "incidents"),
        _read(settings, "operational_events"),
        _read(settings, "capacity_us"),
    )
    timeline(inc, out_dir / "timeline.png")
    period = inc.apply(
        lambda r: (
            "India" if r["market"] == "IN" else ("US dev" if r["in_dev_period"] == "y" else "US lockbox")
        ),
        axis=1,
    )
    lines = [
        "# Incident and operational-event catalogue (P03)",
        "",
        "Model estimate context only; not investment advice. Mechanism labels are agent-assigned (pass 1 and pass 2) pending the user's review (MI-08).",
        "",
        "## Counts",
        "",
        f"- Incidents: **{len(inc)}** ({(inc['market'] == 'US').sum()} US, {(inc['market'] == 'IN').sum()} India); near-misses: {(inc['near_miss'] == 'y').sum()}; usable for validation: {(inc['include_in_validation'] == 'y').sum()}",
        f"- Operational events: **{len(ev)}**; month-precision rows: {(ev['date_precision'] == 'month').sum()}",
        f"- Capacity rows: **{len(cap)}** for {cap['instrument_id'].nunique()} instruments",
        "",
        "### By period and family",
        "",
        pd.crosstab(period, inc["primary_family"]).to_markdown(),
        "",
        "### Operational events by type",
        "",
        ev["type"].value_counts().rename("events").to_frame().to_markdown(),
        "",
        "![timeline](timeline.png)",
        "",
        "## Incidents",
        "",
        inc[
            [
                "incident_id",
                "primary_family",
                "mechanisms",
                "direction",
                "approx_onset",
                "approx_end",
                "near_miss",
                "include_in_validation",
                "grade",
            ]
        ].to_markdown(index=False),
        "",
        "## Rows with month precision (excluded from features)",
        "",
        (
            ev.loc[
                ev["date_precision"] == "month", ["event_id", "type", "effective_at", "notes"]
            ].to_markdown(index=False)
            or "none"
        ),
        "",
        "## Double review",
        "",
    ]
    if agreement:
        lines += [f"- {k}: {v}" for k, v in agreement.items()]
    else:
        lines.append("- Second pass pending.")
    cap_path = settings.path("reports") / "catalogue" / "source_capture.csv"
    if cap_path.exists():
        sc = pd.read_csv(cap_path)
        lines += [
            "",
            "## Source capture",
            "",
            f"- {(~sc['status'].str.startswith('failed')).sum()} source pages saved under `data/raw/catalogue_sources/`; failures (paywalls, 403) are listed in `source_capture.csv` — the URL and grade stay in the tables.",
        ]
    text = "\n".join(lines) + "\n"
    (out_dir / "catalogue_report.md").write_text(text, encoding="utf-8")
    return text

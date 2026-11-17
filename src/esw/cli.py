"""Command-line entry point: `python -m esw <command>` (or `esw <command>`).

Later phases add commands here (probe, ingest, curate, build, evaluate, daily, ...).
"""

from __future__ import annotations

import importlib
import platform
import shutil
import sys
from importlib.metadata import PackageNotFoundError, version

import typer

from esw import __version__
from esw.config import find_repo_root, get_settings, secret_status
from esw.paths import canonical_paths, ingest_log_path
from esw.runlog import RunContext, ensure_registry, git_commit

app = typer.Typer(
    add_completion=False, no_args_is_help=True, help="ETF Arbitrage-Stress Early Warning System"
)

# distribution name -> import name
CORE_PACKAGES = {
    "pandas": "pandas",
    "numpy": "numpy",
    "pyarrow": "pyarrow",
    "duckdb": "duckdb",
    "scipy": "scipy",
    "scikit-learn": "sklearn",
    "lightgbm": "lightgbm",
    "shap": "shap",
    "pandera": "pandera",
    "pydantic": "pydantic",
    "PyYAML": "yaml",
    "python-dotenv": "dotenv",
    "requests": "requests",
    "tenacity": "tenacity",
    "openpyxl": "openpyxl",
    "exchange_calendars": "exchange_calendars",
    "bidask": "bidask",
    "matplotlib": "matplotlib",
    "plotly": "plotly",
    "jinja2": "jinja2",
    "streamlit": "streamlit",
    "typer": "typer",
}


@app.command("version")
def version_cmd() -> None:
    """Print the package version and git commit."""
    root = find_repo_root()
    typer.echo(f"esw {__version__} (git {git_commit(root)})")


@app.command()
def paths() -> None:
    """Print the resolved canonical paths."""
    for name, p in canonical_paths().items():
        typer.echo(f"{name:12s} {p}")


@app.command()
def doctor(
    fix: bool = typer.Option(False, "--fix", help="Create missing canonical directories."),
    smoke_run: bool = typer.Option(False, "--smoke-run", help="Create a smoke-test run folder."),
) -> None:
    """Check the environment, dependencies, secrets (names only) and directories."""
    failures: list[str] = []
    typer.echo(f"Python     {sys.version.split()[0]} ({platform.platform()})")
    typer.echo(f"esw        {__version__}")
    typer.echo(f"git        {'found' if shutil.which('git') else 'MISSING'}")
    if not shutil.which("git"):
        failures.append("git not found")

    typer.echo("\nPackages:")
    for dist, mod in CORE_PACKAGES.items():
        try:
            importlib.import_module(mod)
            v = version(dist)
            typer.echo(f"  ok       {dist:20s} {v}")
        except (ImportError, PackageNotFoundError) as e:
            typer.echo(f"  MISSING  {dist:20s} {e}")
            failures.append(f"package {dist}")

    try:
        settings = get_settings()
        typer.echo("\nSettings:  config/settings.yaml loaded and validated")
    except Exception as e:  # noqa: BLE001 - report any settings failure
        typer.echo(f"\nSettings:  INVALID ({e})")
        raise typer.Exit(code=1) from e

    root = settings.root
    assert root is not None
    typer.echo(f".env       {'present' if (root / '.env').exists() else 'absent'}")
    for name, is_set in secret_status().items():
        typer.echo(f"  {name:16s} {'set' if is_set else 'not set'}")

    typer.echo("\nDirectories:")
    for name, p in canonical_paths(settings).items():
        if not p.exists() and fix:
            p.mkdir(parents=True, exist_ok=True)
        state = "ok" if p.exists() else "MISSING"
        if state != "ok":
            failures.append(f"dir {name}")
        typer.echo(f"  {state:8s} {name:12s} {p.relative_to(root)}")
    if fix:
        ensure_registry(settings.path("runs"))
        ingest_log_path(settings).touch(exist_ok=True)

    if smoke_run:
        with RunContext(phase="P00", purpose="smoke", slug="smoke", settings=settings) as run:
            run.notes = "Smoke test of RunContext created by `esw doctor --smoke-run`."
            run.log_metrics({"smoke": 1})
        typer.echo(f"\nSmoke run: {run.dir.relative_to(root)} ({run.status})")

    if failures:
        typer.echo(f"\nFAILED: {', '.join(failures)}")
        raise typer.Exit(code=1)
    typer.echo("\nAll checks passed.")


@app.command()
def probe(
    source_ids: list[str] = typer.Argument(None, help="Probe IDs to run (default: all)."),
    list_only: bool = typer.Option(False, "--list", help="List available probes and exit."),
) -> None:
    """P01: run small, polite probes of data sources and update reports/data/source_probe_matrix.csv."""
    from esw.ingest.probe import ProbeRunner, all_probe_ids, matrix_path, run_probes

    ids = all_probe_ids()
    if list_only:
        typer.echo(chr(10).join(ids))
        return
    chosen = source_ids or ids
    settings = get_settings()
    with RunContext(phase="P01", purpose="source probes", slug="probe", settings=settings) as run:
        runner = ProbeRunner(settings, run_id=run.run_id)
        rows = run_probes(chosen, runner)
        summary: dict[str, int] = {}
        for row in rows:
            summary[row.status] = summary.get(row.status, 0) + 1
        run.notes = f"Probes run: {', '.join(chosen)}"
        run.log_metrics(
            {"probes": len(chosen), "rows": len(rows), **{f"status_{k}": v for k, v in summary.items()}}
        )
    typer.echo(f"{len(rows)} rows written to {matrix_path(settings)}: {summary}")


@app.command("manual-register")
def manual_register() -> None:
    """Log every new file in data/manual_drop/ in the ingest log (status = manual)."""
    from esw.ingest.manual import register_manual_drops

    settings = get_settings()
    with RunContext(phase="P02", purpose="register manual drops", slug="manual", settings=settings) as run:
        recs = register_manual_drops(settings, run_id=run.run_id)
        run.log_metrics({"files_logged": len(recs)})
    for r in recs:
        typer.echo(
            f"{r['path']}: rows={r['rows_parsed']} {r['date_min']}..{r['date_max']} {r['error'] or ''}"
        )
    typer.echo(f"{len(recs)} new manual file(s) logged.")


reference_app = typer.Typer(no_args_is_help=True, help="P02 reference tables and calendars.")
app.add_typer(reference_app, name="reference")


@reference_app.command("validate")
def reference_validate() -> None:
    """Validate every reference table and the cross-table checks; write reports/data/reference_validation.md."""
    from esw.reference.validate import run_validation

    settings = get_settings()
    report = run_validation(settings)
    typer.echo(report.summary())
    if report.errors:
        raise typer.Exit(code=1)


@reference_app.command("build-calendars")
def reference_build_calendars() -> None:
    """Build data/curated/calendar.parquet (US canonical, India preliminary, foreign markets)."""
    from esw.reference.calendars import build_calendars

    settings = get_settings()
    with RunContext(phase="P02", purpose="build calendars", slug="calendars", settings=settings) as run:
        cal, path = build_calendars(settings)
        counts = cal.groupby("market")["is_trading"].sum().to_dict()
        run.log_metrics({f"trading_days_{k}": int(v) for k, v in counts.items()})
    typer.echo(f"{len(cal)} rows written to {path}")
    for k, v in counts.items():
        typer.echo(f"  {k}: {int(v)} trading days")


if __name__ == "__main__":
    app()

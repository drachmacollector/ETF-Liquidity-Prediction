"""NSE CM bhavcopy fetcher shared by P02 (symbol history, listing dates) and P05 (full backfill).

Files come from `nsearchives.nseindia.com` with a browser-like client (D-010); this host serves the
full archive back to 2007, whereas the older `archives.nseindia.com` host returns 403 before 2016.
Raw files are stored once per day in `data/raw/in_bhav/<yyyy>/` (immutable, logged) and a 404 is
remembered in a small cache so non-trading days are not re-requested.
"""

from __future__ import annotations

import datetime as dt
import json
from pathlib import Path

import pandas as pd

from esw.config import Settings, get_settings
from esw.ingest.http import PoliteSession
from esw.ingest.parsers import parse_nse_bhavcopy
from esw.runlog import append_ingest_log, iso_utc, sha256_file

HOST = "https://nsearchives.nseindia.com/content"
UDIFF_FROM = dt.date(2024, 7, 8)


def bhav_url(day: dt.date) -> tuple[str, str]:
    """(url, file name) for the bhavcopy of `day` in the schema in force on that day."""
    if day >= UDIFF_FROM:
        name = f"BhavCopy_NSE_CM_0_0_0_{day:%Y%m%d}_F_0000.csv.zip"
        return f"{HOST}/cm/{name}", name
    mon = day.strftime("%b").upper()
    name = f"cm{day:%d}{mon}{day:%Y}bhav.csv.zip"
    return f"{HOST}/historical/EQUITIES/{day:%Y}/{mon}/{name}", name


class BhavStore:
    """Fetch-or-load bhavcopies with caching, logging and a remembered list of missing days."""

    def __init__(
        self, settings: Settings | None = None, run_id: str = "", session: PoliteSession | None = None
    ):
        self.settings = settings or get_settings()
        self.run_id = run_id
        self.root = self.settings.path("raw") / "in_bhav"
        self.root.mkdir(parents=True, exist_ok=True)
        self._missing_path = self.root / "_missing_days.json"
        self._missing: set[str] = (
            set(json.loads(self._missing_path.read_text())) if self._missing_path.exists() else set()
        )
        self._session = session
        self._cache: dict[dt.date, pd.DataFrame | None] = {}

    @property
    def session(self) -> PoliteSession:
        if self._session is None:
            self._session = PoliteSession(self.settings, browser=True, min_seconds=2.0)
        return self._session

    def path_for(self, day: dt.date) -> Path:
        return self.root / f"{day:%Y}" / bhav_url(day)[1]

    def fetch(self, day: dt.date) -> Path | None:
        """Return the local path of the file for `day`, downloading it if needed; None if no file exists."""
        p = self.path_for(day)
        if p.exists():
            return p
        if day.isoformat() in self._missing or day > dt.date.today():
            return None
        url, _ = bhav_url(day)
        resp = self.session.get(url, max_retries=2, timeout=60)
        if resp.status_code == 404 or (resp.status_code == 200 and resp.content[:2] != b"PK"):
            self._missing.add(day.isoformat())
            self._missing_path.write_text(json.dumps(sorted(self._missing)))
            return None
        if resp.status_code != 200:
            append_ingest_log(
                {
                    "ts_utc": iso_utc(),
                    "source": "in_bhav",
                    "instrument_id": None,
                    "url": url,
                    "path": str(p),
                    "sha256": None,
                    "status": "failed",
                    "http_status": resp.status_code,
                    "error": f"HTTP {resp.status_code}",
                    "run_id": self.run_id,
                }
            )
            raise RuntimeError(f"bhavcopy {day}: HTTP {resp.status_code}")
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(resp.content)
        root = self.settings.root
        append_ingest_log(
            {
                "ts_utc": iso_utc(),
                "source": "in_bhav",
                "instrument_id": None,
                "url": url,
                "path": p.relative_to(root).as_posix() if root else str(p),
                "sha256": sha256_file(p),
                "bytes": len(resp.content),
                "http_status": 200,
                "status": "ok",
                "rows_parsed": None,
                "date_min": day.isoformat(),
                "date_max": day.isoformat(),
                "error": None,
                "run_id": self.run_id,
            }
        )
        return p

    def load(self, day: dt.date) -> pd.DataFrame | None:
        if day not in self._cache:
            p = self.fetch(day)
            self._cache[day] = None if p is None else parse_nse_bhavcopy(p.read_bytes())
        return self._cache[day]

    def first_on_or_after(self, day: dt.date, max_days: int = 10) -> tuple[dt.date, pd.DataFrame] | None:
        """The first day on or after `day` (weekdays only, up to `max_days`) that has a bhavcopy."""
        d = day
        for _ in range(max_days):
            if d.weekday() < 5:
                df = self.load(d)
                if df is not None:
                    return d, df
            d += dt.timedelta(days=1)
        return None

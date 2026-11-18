"""SEC EDGAR access (declared project user agent, D-004/D-010; <= 5 requests/second).

* `submissions(cik)` - every filing with its EDGAR **acceptance timestamp** (the `known_at` of a filing,
  P03 dating protocol), merging the paged history files.
* `full_text_search(q, ...)` - EDGAR full-text search (2001 onwards).
* `fetch_document(...)` - save a filing document under `data/raw/<dest>/` and log it.

The submissions JSON gives `acceptanceDateTime` in **UTC** (checked in P03: SEC's nightly EFFECT notices
are accepted at 04:15Z in summer and 05:15Z in winter, i.e. a constant 00:15 New York time).
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import pandas as pd

from esw.config import Settings, get_settings
from esw.ingest.http import PoliteSession
from esw.runlog import append_ingest_log, iso_utc, sha256_file

SUBMISSIONS = "https://data.sec.gov/submissions/CIK{cik10}.json"
FILES = "https://data.sec.gov/submissions/{name}"
FTS = "https://efts.sec.gov/LATEST/search-index"
ARCHIVE = "https://www.sec.gov/Archives/edgar/data/{cik}/{acc_nodash}/{doc}"


class Edgar:
    def __init__(self, settings: Settings | None = None, run_id: str = ""):
        self.settings = settings or get_settings()
        self.run_id = run_id
        self.http = PoliteSession(self.settings, min_seconds=0.25)  # SEC fair access: <= 10/s; stay at 4/s
        self.raw = self.settings.path("raw") / "sec_edgar"
        self.raw.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------------ helpers
    def _save(
        self, url: str, path: Path, content: bytes, source: str, instrument_id: str | None = None
    ) -> Path:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)
        root = self.settings.root
        append_ingest_log(
            {
                "ts_utc": iso_utc(),
                "source": source,
                "instrument_id": instrument_id,
                "url": url,
                "path": path.relative_to(root).as_posix() if root else str(path),
                "sha256": sha256_file(path),
                "bytes": len(content),
                "http_status": 200,
                "status": "ok",
                "rows_parsed": None,
                "date_min": None,
                "date_max": None,
                "error": None,
                "run_id": self.run_id,
            }
        )
        return path

    def _get_json(self, url: str, path: Path, refresh: bool = False) -> dict:
        if path.exists() and not refresh:
            return json.loads(path.read_text(encoding="utf-8"))
        resp = self.http.get(url)
        resp.raise_for_status()
        self._save(url, path, resp.content, "sec_edgar")
        return resp.json()

    # ------------------------------------------------------------------ API
    def submissions(self, cik: int | str, refresh: bool = False) -> pd.DataFrame:
        cik10 = f"{int(cik):010d}"
        main = self._get_json(
            SUBMISSIONS.format(cik10=cik10), self.raw / "submissions" / f"CIK{cik10}.json", refresh
        )
        frames = [pd.DataFrame(main["filings"]["recent"])]
        for f in main["filings"].get("files", []):
            extra = self._get_json(
                FILES.format(name=f["name"]), self.raw / "submissions" / f["name"], refresh
            )
            frames.append(pd.DataFrame(extra))
        df = pd.concat(frames, ignore_index=True)
        df["cik"] = int(cik)
        df["acceptance_utc"] = acceptance_utc(df["acceptanceDateTime"])
        return df.sort_values("acceptance_utc").reset_index(drop=True)

    def full_text_search(
        self,
        q: str,
        ciks: list[int] | None = None,
        forms: str | None = None,
        start: str | None = None,
        end: str | None = None,
    ) -> pd.DataFrame:
        params = {"q": q}
        if ciks:
            params["ciks"] = ",".join(f"{int(c):010d}" for c in ciks)
        if forms:
            params["forms"] = forms
        if start or end:
            params.update(dateRange="custom", startdt=start or "2001-01-01", enddt=end or "2030-12-31")
        resp = self.http.get(FTS, params=params)
        resp.raise_for_status()
        hits = resp.json()["hits"]["hits"]
        rows = []
        for h in hits:
            s = h["_source"]
            adsh, _, doc = h["_id"].partition(":")
            rows.append(
                {
                    "adsh": adsh,
                    "doc": doc,
                    "form": s.get("form"),
                    "file_date": s.get("file_date"),
                    "ciks": ";".join(s.get("ciks", [])),
                    "names": ";".join(s.get("display_names", [])),
                }
            )
        return pd.DataFrame(rows)

    def fetch_document(
        self, cik: int | str, adsh: str, doc: str, dest: str, instrument_id: str | None = None
    ) -> Path:
        url = ARCHIVE.format(cik=int(cik), acc_nodash=adsh.replace("-", ""), doc=doc)
        path = self.settings.path("raw") / dest / f"{adsh}_{doc}"
        if path.exists():
            return path
        resp = self.http.get(url)
        resp.raise_for_status()
        return self._save(url, path, resp.content, "catalogue", instrument_id)


def acceptance_utc(values: pd.Series) -> pd.Series:
    """EDGAR submissions-JSON acceptanceDateTime ('2009-07-07T17:52:02.000Z', UTC) -> UTC timestamps."""
    return pd.to_datetime(values.str[:19], format="%Y-%m-%dT%H:%M:%S").dt.tz_localize("UTC")


def html_text(raw: bytes) -> str:
    """Plain text of an EDGAR HTML/TXT document (tags removed, entities decoded, whitespace collapsed)."""
    from html import unescape

    s = raw.decode("utf-8", errors="replace")
    s = re.sub(r"(?is)<(script|style).*?</>", " ", s)
    s = re.sub(r"(?s)<[^>]+>", " ", s)
    s = unescape(s).replace("​", " ").replace(" ", " ")
    return re.sub(r"\s+", " ", s)

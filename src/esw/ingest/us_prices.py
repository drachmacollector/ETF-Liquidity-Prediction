"""P04 T04.2: US daily prices. Tiingo (primary, raw OHLCV + splitFactor + divCash), yfinance fallback.

Tiingo's free tier allows about 50 requests per hour (I-002); `TiingoPacer` keeps a rolling one-hour
window at `tiingo_requests_per_hour` (settings) and sleeps when the window is full. One request per
ticker fetches the full history.
"""

from __future__ import annotations

import collections
import datetime as dt
import json
import os
import time

import pandas as pd

from esw.config import Settings, get_settings
from esw.ingest import parsers as P
from esw.ingest.base import Fetcher, FetchTask, stage
from esw.ingest.http import PoliteSession

TIINGO = "https://api.tiingo.com/tiingo/daily/{t}/prices"
STAGED_COLS = [
    "instrument_id", "ticker", "date", "open", "high", "low", "close", "volume",
    "vendor_split_factor", "vendor_div_cash", "adj_close", "source_id", "raw_path", "ingested_at",
]  # fmt: skip


class TiingoPacer:
    def __init__(self, per_hour: int):
        self.per_hour = per_hour
        self.calls: collections.deque[float] = collections.deque()

    def wait(self) -> None:
        now = time.monotonic()
        while self.calls and now - self.calls[0] > 3600:
            self.calls.popleft()
        if len(self.calls) >= self.per_hour:
            time.sleep(3600 - (now - self.calls[0]) + 5)
        self.calls.append(time.monotonic())


def _tiingo_key() -> str:
    key = os.environ.get("TIINGO_API_KEY")
    if not key:
        from dotenv import load_dotenv

        load_dotenv(get_settings().root / ".env")
        key = os.environ.get("TIINGO_API_KEY")
    if not key:
        raise RuntimeError("TIINGO_API_KEY not set (.env)")
    return key


def fetch_tiingo(
    tickers: list[str], settings: Settings | None = None, run_id: str = "", refresh: bool = False
) -> dict:
    settings = settings or get_settings()
    per_hour = int(settings.sources["us_prices"].get("tiingo_requests_per_hour", 45))
    pacer = TiingoPacer(per_hour)
    sess = PoliteSession(settings)
    key = _tiingo_key()
    fetcher = Fetcher(settings, run_id)
    out = {}
    for t in tickers:
        path = settings.path("raw") / "us_px_tiingo" / "full" / f"{t}.json"
        task = FetchTask(
            "us_px_tiingo",
            f"US:{t}",
            TIINGO.format(t=t.lower()),
            path,
            params={"startDate": "1990-01-01", "format": "json"},
            headers={"Content-Type": "application/json", "Authorization": f"Token {key}"},
        )
        if not path.exists() or refresh:
            pacer.wait()

        def get(url, params=None, headers=None):
            return sess.get(url, params=params, headers=headers, max_retries=2)

        res = fetcher.run(task, get, refresh=refresh, validate=lambda b: b[:1] == b"[" and len(b) > 10)
        out[t] = res.status
    return out


def fetch_yf(tickers: list[str], settings: Settings | None = None, run_id: str = "") -> dict:
    """Fallback: yfinance unadjusted OHLCV (auto_adjust=False) saved as CSV."""
    import yfinance as yf

    settings = settings or get_settings()
    fetcher = Fetcher(settings, run_id)
    out = {}
    for t in tickers:
        path = settings.path("raw") / "us_px_yf" / "full" / f"{t}.csv"
        task = FetchTask("us_px_yf", f"US:{t}", f"yfinance:{t}", path)
        if path.exists():
            fetcher.log(task, "skipped_cached")
            out[t] = "skipped_cached"
            continue
        try:
            h = yf.Ticker(t).history(period="max", auto_adjust=False, actions=True)
            if h.empty:
                raise ValueError("empty")
            path.parent.mkdir(parents=True, exist_ok=True)
            h.to_csv(path)
            fetcher.log(task, "ok", rows=len(h))
            out[t] = "ok"
        except Exception as exc:  # noqa: BLE001
            fetcher.log(task, "failed", error=str(exc)[:200])
            out[t] = "failed"
        time.sleep(0.5)
    return out


def parse_yf_csv(raw: bytes) -> pd.DataFrame:
    import io

    df = pd.read_csv(io.BytesIO(raw))
    df["date"] = pd.to_datetime(df["Date"].str[:10])
    return pd.DataFrame(
        {
            "date": df["date"],
            "open": df["Open"],
            "high": df["High"],
            "low": df["Low"],
            "close": df["Close"],
            "volume": df["Volume"],
            "adj_close": df.get("Adj Close"),
            "div_cash": df.get("Dividends"),
            "split_factor": df.get("Stock Splits", pd.Series(0.0, index=df.index)).replace(0, 1.0),
        }
    )


def stage_prices(settings: Settings | None = None) -> dict[str, int]:
    settings = settings or get_settings()
    raw = settings.path("raw")
    now = pd.Timestamp.now(tz="UTC").floor("s")
    counts = {}
    for source_id, folder, parser in (
        ("us_px_tiingo", raw / "us_px_tiingo" / "full", lambda b: P.parse_tiingo_prices(b)),
        ("us_px_yf", raw / "us_px_yf" / "full", parse_yf_csv),
    ):
        frames = []
        for p in sorted(folder.glob("*.*")) if folder.exists() else []:
            t = p.stem.split("_")[0]
            df = parser(p.read_bytes())
            if df.empty:
                continue
            df = df.rename(columns={"split_factor": "vendor_split_factor", "div_cash": "vendor_div_cash"})
            df["ticker"], df["instrument_id"] = t, f"US:{t}"
            df["source_id"], df["raw_path"], df["ingested_at"] = (
                source_id,
                p.relative_to(settings.root).as_posix(),
                now,
            )
            frames.append(df.reindex(columns=STAGED_COLS))
        if frames:
            all_ = pd.concat(frames, ignore_index=True)
            stage(all_, "us_px", source_id, settings)
            counts[source_id] = len(all_)
    return counts


def tiingo_dates(ticker: str, settings: Settings | None = None) -> tuple[dt.date, dt.date] | None:
    settings = settings or get_settings()
    p = settings.path("raw") / "us_px_tiingo" / "full" / f"{ticker}.json"
    if not p.exists():
        return None
    d = json.loads(p.read_text())
    return (pd.Timestamp(d[0]["date"]).date(), pd.Timestamp(d[-1]["date"]).date()) if d else None

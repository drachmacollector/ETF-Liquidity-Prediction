"""Polite HTTP access (System Specification §11).

Rules: identify honestly with the project user agent, at most one request per
`min_seconds_between_requests` per host, exponential back-off with jitter on 429/5xx and
timeouts. Never imitate a browser or work around bot protection: a blocked source is
recorded as blocked and handled by a manual-download guide instead.
"""

from __future__ import annotations

import logging
import random
import time
from urllib.parse import urlparse

import requests

from esw.config import Settings, get_settings

log = logging.getLogger(__name__)

RETRY_STATUSES = {429, 500, 502, 503, 504}


class PoliteSession:
    def __init__(self, settings: Settings | None = None, timeout: float | None = None) -> None:
        self.settings = settings or get_settings()
        self.http = self.settings.http
        self.timeout = timeout or self.http.timeout_seconds
        self.session = requests.Session()
        self.session.headers["User-Agent"] = self.settings.user_agent
        self._last_request: dict[str, float] = {}

    def _wait_for_host(self, host: str) -> None:
        last = self._last_request.get(host)
        if last is not None:
            gap = time.monotonic() - last
            if gap < self.http.min_seconds_between_requests:
                time.sleep(self.http.min_seconds_between_requests - gap)
        self._last_request[host] = time.monotonic()

    def get(
        self,
        url: str,
        *,
        params: dict | None = None,
        headers: dict | None = None,
        timeout: float | None = None,
        max_retries: int | None = None,
    ) -> requests.Response:
        """GET with rate limiting and retries. Returns the last response; raises on repeated network errors."""
        host = urlparse(url).netloc
        retries = self.http.max_retries if max_retries is None else max_retries
        last_exc: Exception | None = None
        for attempt in range(retries + 1):
            self._wait_for_host(host)
            try:
                resp = self.session.get(url, params=params, headers=headers, timeout=timeout or self.timeout)
            except (requests.ConnectionError, requests.Timeout) as exc:
                last_exc = exc
                log.warning(
                    "GET %s failed (%s), attempt %d/%d", url, type(exc).__name__, attempt + 1, retries + 1
                )
            else:
                if resp.status_code not in RETRY_STATUSES or attempt == retries:
                    return resp
                log.warning("GET %s -> %d, attempt %d/%d", url, resp.status_code, attempt + 1, retries + 1)
            if attempt < retries:
                time.sleep(self.http.backoff_base_seconds * (2**attempt) * (0.5 + random.random()))
        assert last_exc is not None
        raise last_exc

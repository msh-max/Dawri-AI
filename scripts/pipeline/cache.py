"""File-backed HTTP cache + polite fetch helper.

Why: scrapers re-run daily and during local development. Hitting FBref or
Wikidata harder than necessary is rude and risks bans. This module wraps
`requests.Session` with on-disk caching keyed by URL, plus a per-domain
rate limiter and a User-Agent that identifies the project.
"""

from __future__ import annotations

import hashlib
import json
import logging
import threading
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import requests
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

log = logging.getLogger("dawri.cache")

USER_AGENT = (
    "DawriAI/0.1 (+https://github.com/msh-max/msh-max) "
    "non-commercial analytics, daily scrape, attribution displayed"
)

# Polite, generous defaults. CI runs once a day so it's fine to be slow.
_DEFAULT_DELAY_SEC = 3.0
_DEFAULT_TIMEOUT_SEC = 30.0


@dataclass
class FetchResult:
    url: str
    status_code: int
    text: str
    from_cache: bool


class HttpCache:
    def __init__(
        self,
        cache_dir: Path,
        delay_sec: float = _DEFAULT_DELAY_SEC,
        ttl_sec: int = 24 * 60 * 60,
    ) -> None:
        self.cache_dir = cache_dir
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.delay_sec = delay_sec
        self.ttl_sec = ttl_sec
        self._last_fetch_per_host: dict[str, float] = {}
        self._lock = threading.Lock()
        self._session = requests.Session()
        self._session.headers.update({"User-Agent": USER_AGENT})

    def _cache_path(self, url: str) -> Path:
        digest = hashlib.sha256(url.encode("utf-8")).hexdigest()[:24]
        return self.cache_dir / f"{digest}.json"

    def _read_cache(self, url: str) -> FetchResult | None:
        path = self._cache_path(url)
        if not path.exists():
            return None
        try:
            payload: dict[str, Any] = json.loads(path.read_text("utf-8"))
        except (OSError, json.JSONDecodeError):
            return None
        age = time.time() - payload.get("fetched_at", 0)
        if age > self.ttl_sec:
            return None
        if payload.get("url") != url:
            return None  # collision, refetch
        return FetchResult(
            url=url,
            status_code=int(payload["status_code"]),
            text=str(payload["text"]),
            from_cache=True,
        )

    def _write_cache(self, url: str, status_code: int, text: str) -> None:
        path = self._cache_path(url)
        path.write_text(
            json.dumps(
                {
                    "url": url,
                    "status_code": status_code,
                    "text": text,
                    "fetched_at": time.time(),
                },
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )

    def _wait_for_host(self, host: str) -> None:
        with self._lock:
            last = self._last_fetch_per_host.get(host, 0.0)
            elapsed = time.time() - last
            if elapsed < self.delay_sec:
                sleep_for = self.delay_sec - elapsed
                log.debug("rate-limit %s sleeping %.2fs", host, sleep_for)
                time.sleep(sleep_for)
            self._last_fetch_per_host[host] = time.time()

    @retry(
        retry=retry_if_exception_type(
            (requests.ConnectionError, requests.Timeout)
        ),
        wait=wait_exponential(multiplier=2, min=2, max=30),
        stop=stop_after_attempt(4),
        reraise=True,
    )
    def _do_request(
        self, url: str, params: dict[str, Any] | None
    ) -> requests.Response:
        return self._session.get(
            url, params=params, timeout=_DEFAULT_TIMEOUT_SEC
        )

    def get(
        self,
        url: str,
        *,
        params: dict[str, Any] | None = None,
        force_refresh: bool = False,
    ) -> FetchResult:
        full_url = url
        if params:
            from urllib.parse import urlencode

            full_url = f"{url}?{urlencode(sorted(params.items()))}"

        if not force_refresh:
            cached = self._read_cache(full_url)
            if cached is not None:
                log.debug("cache HIT %s", full_url)
                return cached

        from urllib.parse import urlparse

        host = urlparse(url).netloc
        self._wait_for_host(host)
        log.info("fetching %s", full_url)
        resp = self._do_request(url, params)
        result = FetchResult(
            url=full_url,
            status_code=resp.status_code,
            text=resp.text,
            from_cache=False,
        )
        if 200 <= resp.status_code < 300:
            self._write_cache(full_url, resp.status_code, resp.text)
        return result

"""HTTP client for CopperKnob's search.

The ``www`` host (https://www.copperknob.co.uk) serves search pages to
plain HTTP clients with a browser User-Agent — no JavaScript, no browser
automation needed. (The bare ``copperknob.co.uk`` apex sits behind a
Cloudflare challenge; this client simply uses ``www``.)

If Cloudflare ever starts challenging the ``www`` host too, fetches raise
:exc:`CloudflareChallengeError` instead of returning garbage.
"""

from __future__ import annotations

import time
from typing import Dict, List, Optional
from urllib.parse import urlencode

import requests

from .exceptions import CloudflareChallengeError, SearchError
from .parser import parse_search_results, find_next_page_url

BASE_URL = "https://www.copperknob.co.uk"
SEARCH_PATH = "/search"

DEFAULT_UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/126.0.0.0 Safari/537.36"
)

_CHALLENGE_MARKERS = (
    "challenges.cloudflare.com",
    "just a moment",
    "verify you are human",
)


def _looks_challenged(html: str) -> bool:
    low = html.lower()
    return any(m in low for m in _CHALLENGE_MARKERS) and "listitem" not in low


class CopperKnobClient:
    """Search client. Use as a context manager or call :meth:`close`.

    Example::

        with CopperKnobClient() as client:
            for dance in client.search("Cowboy Charleston", max_results=10):
                print(dance["title"], dance["url"])
    """

    def __init__(
        self,
        *,
        base_url: Optional[str] = None,
        user_agent: str = DEFAULT_UA,
        timeout: int = 30,
        proxy: Optional[str] = None,
        verify_tls: bool = True,
        delay_between_requests: float = 1.0,
    ) -> None:
        self.base_url = (base_url or BASE_URL).rstrip("/")
        self.timeout = timeout
        self.delay_between_requests = delay_between_requests
        self._session = requests.Session()
        self._session.headers.update({
            "User-Agent": user_agent,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-GB,en;q=0.9",
        })
        if proxy:
            self._session.proxies.update({"http": proxy, "https": proxy})
        self._session.verify = verify_tls

    def close(self) -> None:
        self._session.close()

    def __enter__(self) -> "CopperKnobClient":
        return self

    def __exit__(self, *exc) -> None:
        self.close()

    # -- search --------------------------------------------------------

    def _get(self, url: str) -> str:
        try:
            resp = self._session.get(url, timeout=self.timeout)
            resp.raise_for_status()
        except requests.RequestException as exc:
            raise SearchError(f"Request failed for {url}: {exc}") from exc
        html = resp.text
        if _looks_challenged(html):
            raise CloudflareChallengeError(
                "Cloudflare is challenging requests to the www host. "
                "This is unusual — wait a while and retry; if it persists, "
                "the site's bot policy changed and the client needs updating."
            )
        return html

    def _search_url(self, query: str, recnum: int = 0, **filters) -> str:
        params = {
            "Order": filters.get("order", "Date"),
            "Lang": filters.get("lang", ""),
            "SearchType": filters.get("search_type", ""),
            "Level": filters.get("level", ""),
            "BeatFrom": filters.get("beat_from", ""),
            "BeatTo": filters.get("beat_to", ""),
            "Wall": filters.get("wall", ""),
            "Search": query,
        }
        if recnum:
            params["recnum"] = recnum
        return f"{self.base_url}{SEARCH_PATH}?{urlencode(params)}"

    def search(
        self,
        query: str,
        *,
        order: str = "Date",
        level: str = "",
        wall: str = "",
        lang: str = "",
        beat_from: str = "",
        beat_to: str = "",
        search_type: str = "",
        max_results: Optional[int] = None,
        max_pages: int = 10,
    ) -> List[Dict]:
        """Search stepsheets and return structured results.

        Each result: ``id``, ``title``, ``url``, ``choreographer``,
        ``date``, ``count``, ``walls``, ``level``, ``music``.
        Follows pagination (20 results/page) until ``max_results`` or
        ``max_pages``.
        """
        results: List[Dict] = []
        url = self._search_url(
            query, order=order, level=level, wall=wall, lang=lang,
            beat_from=beat_from, beat_to=beat_to, search_type=search_type,
        )
        for _ in range(max_pages):
            html = self._get(url)
            batch = parse_search_results(html, self.base_url)
            if not batch:
                break
            results.extend(batch)
            if max_results and len(results) >= max_results:
                break
            next_url = find_next_page_url(html, self.base_url)
            if not next_url:
                break
            url = next_url
            time.sleep(self.delay_between_requests)

        if max_results:
            results = results[:max_results]
        return results


_CLIENT_KWARGS = (
    "base_url", "user_agent", "timeout", "proxy", "verify_tls",
    "delay_between_requests",
)


def search(query: str, **kwargs) -> List[Dict]:
    """One-shot convenience wrapper: search and return results."""
    client_kwargs = {k: kwargs.pop(k) for k in _CLIENT_KWARGS if k in kwargs}
    with CopperKnobClient(**client_kwargs) as client:
        return client.search(query, **kwargs)

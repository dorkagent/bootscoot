#!/usr/bin/env python3
"""BootScoot - line-dance stepsheet search in a single file.

Run it directly::

    python bootscoot.py "Cowboy Charleston" --max-results 10 --format json

Or import it::

    from bootscoot import search, CopperKnobClient

    for dance in search("Bailando", max_results=5):
        print(dance["title"], dance["url"])

Needs: requests, beautifulsoup4
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import time
from typing import Dict, List, Optional
from urllib.parse import urlencode, urljoin

import requests
from bs4 import BeautifulSoup

__version__ = "0.1.0"


# ------------------------------------------------------------------
# Exceptions
# ------------------------------------------------------------------


class CopperKnobError(Exception):
    """Base error for bootscoot."""


class CloudflareChallengeError(CopperKnobError):
    """Raised when Cloudflare's bot challenge blocks the request.

    The client uses the ``www`` host, which normally serves plain HTTP
    clients without a challenge. If this error appears, Cloudflare's
    policy changed: wait a while and retry; if it persists, the client
    needs updating (e.g. a browser-based fallback).
    """


class SearchError(CopperKnobError):
    """Raised when a search request fails or results cannot be parsed."""


# ------------------------------------------------------------------
# Parser: result pages -> structured dicts
# ------------------------------------------------------------------
#
# Real markup (verified 2026-10-10 against the live site)::
#
#     <div class="listitem" onClick="location.href='.../stepsheets/<ID>/<slug>';">
#       <div class="listTitle">
#         <a href=".../stepsheets/<ID>/<slug>">
#           <span class="listTitleColor1">Dance <mark>Title</mark></span></a>
#         <span class="listTitleColor2">Choreographer (CC) - Month Year</span>
#       </div>
#       <div class="listInfo">
#         <p class="listIcons">... 32 Count ... 4 Wall ... Beginner ... Music:
#            Track - Artist</p>
#       </div>
#     </div>
#
# IDs are alphanumeric (e.g. ``22B54H3``). Pagination links carry ``recnum=<offset>``.

_STEPSHEET_RE = re.compile(r"/stepsheets/([A-Za-z0-9]+)/[^/?#]+", re.I)
_COUNT_RE = re.compile(r"(\d+)\s*Count", re.I)
# Partner dances render "- Wall" (no number); strip it from level text too.
_WALL_RE = re.compile(r"(\d+|-)\s*Wall", re.I)
_MARK_RE = re.compile(r"</?mark>", re.I)
_CHOREO_RE = re.compile(
    r"^(?P<choreographer>.+?)\s*-\s*(?P<date>(?:\d{1,2}\s+\w+\s+\d{4})|(?:\w+\s+\d{4}))\s*$"
)


def _clean(text: str) -> str:
    return re.sub(r"\s+", " ", (text or "")).strip()


def parse_search_results(html: str, base_url: str = "https://www.copperknob.co.uk") -> List[Dict]:
    """Extract one dict per result from a search-results page.

    Each dict has: ``id``, ``title``, ``url``, ``choreographer``,
    ``date``, ``count``, ``walls``, ``level``, ``music``. Missing fields
    are ``None``.
    """
    # Unwrap search-term highlights (<mark>Cowboy</mark>s) with no separator,
    # otherwise "Cowboys" becomes "Cowboy s".
    html = _MARK_RE.sub("", html)
    soup = BeautifulSoup(html, "html.parser")
    results: List[Dict] = []

    for item in soup.select("div.listitem"):
        link = item.select_one("div.listTitle a[href]")
        if not link:
            continue
        m = _STEPSHEET_RE.search(link["href"])
        if not m:
            continue

        title_el = link.select_one("span.listTitleColor1") or link
        title = _clean(title_el.get_text(" "))

        choreo_el = item.select_one("span.listTitleColor2")
        choreographer = date = None
        if choreo_el:
            choreo_text = _clean(choreo_el.get_text(" "))
            cm = _CHOREO_RE.match(choreo_text)
            if cm:
                choreographer = cm.group("choreographer").strip()
                date = cm.group("date").strip()
            elif choreo_text:
                # No " - Month Year" suffix (e.g. "Unknown"): keep the name.
                choreographer = choreo_text

        info_el = item.select_one("div.listInfo")
        info_text = _clean(info_el.get_text(" ") if info_el else "")
        count = walls = level = music = None
        cm = _COUNT_RE.search(info_text)
        if cm:
            count = int(cm.group(1))
        wm = _WALL_RE.search(info_text)
        if wm and wm.group(1).isdigit():
            walls = int(wm.group(1))
        # "... 32 Count 4 Wall Beginner Music: Track - Artist"
        mm = re.search(r"Music:\s*(.+)$", info_text, re.I)
        if mm:
            music = mm.group(1).strip() or None
            before = _WALL_RE.sub("", _COUNT_RE.sub("", info_text[: mm.start()]))
            level = _clean(before).strip("- ") or None

        results.append({
            "id": m.group(1),
            "title": title or None,
            "url": urljoin(base_url, link["href"]),
            "choreographer": choreographer,
            "date": date,
            "count": count,
            "walls": walls,
            "level": level,
            "music": music,
        })

    return results


def find_next_page_url(html: str, base_url: str = "https://www.copperknob.co.uk") -> Optional[str]:
    """Return the URL of the next results page, if the markup offers one."""
    soup = BeautifulSoup(html, "html.parser")
    for a in soup.find_all("a", href=True):
        label = _clean(a.get_text(" ")).lower()
        if label in {"next", "next >", ">", "»", "›"}:
            return urljoin(base_url, a["href"])
    return None


# ------------------------------------------------------------------
# Client
# ------------------------------------------------------------------

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


# ------------------------------------------------------------------
# CLI
# ------------------------------------------------------------------


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="bootscoot",
        description="Search line-dance stepsheets from the command line.",
    )
    p.add_argument("query", help="Search text, e.g. \"Cowboy Charleston\"")
    p.add_argument("--level", default="", help="Level filter, e.g. Beginner")
    p.add_argument("--wall", default="", help="Wall count filter, e.g. 4")
    p.add_argument("--lang", default="", help="Stepsheet language filter")
    p.add_argument("--beat-from", default="", help="Minimum beats per minute")
    p.add_argument("--beat-to", default="", help="Maximum beats per minute")
    p.add_argument("--order", default="Date", help="Result ordering (default: Date)")
    p.add_argument(
        "--max-results", type=int, default=20,
        help="Max results to return, follows pagination (default: 20)",
    )
    p.add_argument(
        "--format", choices=["text", "json"], default="text",
        help="Output format (default: text)",
    )
    p.add_argument(
        "--proxy", default=None,
        help="Proxy server URL, e.g. http://user:pass@host:3128",
    )
    p.add_argument(
        "--base-url", default=None,
        help="Target site base URL (default: the site the parser was built for)",
    )
    return p


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)
    try:
        with CopperKnobClient(proxy=args.proxy, base_url=args.base_url) as client:
            results = client.search(
                args.query,
                level=args.level,
                wall=args.wall,
                lang=args.lang,
                beat_from=args.beat_from,
                beat_to=args.beat_to,
                order=args.order,
                max_results=args.max_results,
            )
    except (CloudflareChallengeError, SearchError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    if args.format == "json":
        print(json.dumps(results, indent=2, ensure_ascii=False))
    else:
        if not results:
            print("No results.")
            return 0
        for r in results:
            meta = " | ".join(
                str(x) for x in
                [f"{r['count']}ct" if r.get("count") else None,
                 f"{r['walls']}w" if r.get("walls") else None,
                 r.get("level")]
                if x
            )
            byline = " — ".join(x for x in [r.get("choreographer"), r.get("date")] if x)
            print(f"{r['title']}")
            if byline:
                print(f"  {byline}")
            if meta:
                print(f"  {meta}")
            if r.get("music"):
                print(f"  Music: {r['music']}")
            print(f"  {r['url']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

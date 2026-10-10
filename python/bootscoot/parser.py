"""Parse CopperKnob search-result pages into structured dicts.

Real markup (verified 2026-10-10 against the live site)::

    <div class="listitem" onClick="location.href='.../stepsheets/<ID>/<slug>';">
      <div class="listTitle">
        <a href=".../stepsheets/<ID>/<slug>">
          <span class="listTitleColor1">Dance <mark>Title</mark></span></a>
        <span class="listTitleColor2">Choreographer (CC) - Month Year</span>
      </div>
      <div class="listInfo">
        <p class="listIcons">... 32 Count ... 4 Wall ... Beginner ... Music:
           Track - Artist</p>
      </div>
    </div>

IDs are alphanumeric (e.g. ``22B54H3``). Pagination links carry ``recnum=<offset>``.
"""

from __future__ import annotations

import re
from typing import List, Dict, Optional
from urllib.parse import urljoin

from bs4 import BeautifulSoup

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

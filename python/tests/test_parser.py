"""Parser tests against the real result markup (captured 2026-10-10)."""

import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

from bootscoot.parser import parse_search_results, find_next_page_url

FIXTURE = """
<html><body>
<div class="listitem" onClick="location.href='https://www.copperknob.co.uk/stepsheets/22B54H3/ez-rhinestone-cowboy';">
  <div class="listTitle">
    <a href="https://www.copperknob.co.uk/stepsheets/22B54H3/ez-rhinestone-cowboy">
    <span class="listTitleColor1">
    EZ Rhinestone <mark>Cowboy</mark></span></a>&nbsp;&nbsp;<span class="listTitleColor2">Pat Wilson (NZ) - October 2026            </span>
  </div>
  <div class="listInfo">
    <p class="listIcons"><span class="videoicon"></span><span class="musicicon"></span>
    &nbsp;&nbsp;&nbsp; 32&nbsp;Count&nbsp;&nbsp;&nbsp;
    4&nbsp;Wall&nbsp;&nbsp;&nbsp;
    Beginner&nbsp;&nbsp;&nbsp;Music:
    Rhinestone <mark>Cowboy</mark> - Glen Campbell</p>
  </div>
</div>
<div class="listitem" onClick="location.href='https://www.copperknob.co.uk/stepsheets/QWWS2Z2/show-me-how-you-giddy-up';">
  <div class="listTitle">
    <a href="https://www.copperknob.co.uk/stepsheets/QWWS2Z2/show-me-how-you-giddy-up">
    <span class="listTitleColor1">
    Show Me How You Giddy Up</span></a>&nbsp;&nbsp;<span class="listTitleColor2">Tammy Pemberton (USA) - October 2026</span>
  </div>
  <div class="listInfo">
    <p class="listIcons">&nbsp;&nbsp;&nbsp; 64&nbsp;Count&nbsp;&nbsp;&nbsp;
    2&nbsp;Wall&nbsp;&nbsp;&nbsp;
    Improver Phrased&nbsp;&nbsp;&nbsp;Music:
    Come on <mark>Cowboy</mark> (Giddy Up) - RaeLynn</p>
  </div>
</div>
<a href="https://www.copperknob.co.uk/search?Order=Date&amp;Search=Cowboy&amp;recnum=20">Next</a>
</body></html>
"""


def test_parse_results():
    results = parse_search_results(FIXTURE)
    assert len(results) == 2, results

    r1 = results[0]
    assert r1["id"] == "22B54H3", r1
    assert r1["title"] == "EZ Rhinestone Cowboy", r1
    assert r1["url"] == "https://www.copperknob.co.uk/stepsheets/22B54H3/ez-rhinestone-cowboy"
    assert r1["choreographer"] == "Pat Wilson (NZ)", r1
    assert r1["date"] == "October 2026", r1
    assert r1["count"] == 32, r1
    assert r1["walls"] == 4, r1
    assert r1["level"] == "Beginner", r1
    assert r1["music"] == "Rhinestone Cowboy - Glen Campbell", r1

    r2 = results[1]
    assert r2["id"] == "QWWS2Z2", r2
    assert r2["title"] == "Show Me How You Giddy Up", r2
    assert r2["level"] == "Improver Phrased", r2
    assert r2["music"] == "Come on Cowboy (Giddy Up) - RaeLynn", r2
    assert r2["count"] == 64 and r2["walls"] == 2, r2


def test_next_page():
    nxt = find_next_page_url(FIXTURE)
    assert nxt == "https://www.copperknob.co.uk/search?Order=Date&Search=Cowboy&recnum=20", nxt


def test_empty_page():
    assert parse_search_results("<html><body>no results</body></html>") == []
    assert find_next_page_url("<html></html>") is None


if __name__ == "__main__":
    test_parse_results()
    test_next_page()
    test_empty_page()
    print("parser tests: OK")

"""Client flow tests with a stubbed HTTP layer (no network needed)."""

import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

import bootscoot as C

PAGE1 = """
<html><body>
<div class="listitem"><div class="listTitle">
<a href="/stepsheets/AAA111/dance-one"><span class="listTitleColor1">Dance One</span></a>
<span class="listTitleColor2">Jane Doe (USA) - October 2026</span></div>
<div class="listInfo"><p class="listIcons">32 Count 4 Wall Beginner Music: Song One - Artist</p></div></div>
<div class="listitem"><div class="listTitle">
<a href="/stepsheets/CCC333/partner-mix"><span class="listTitleColor1"><mark>Cowboy</mark>s Mix</span></a>
<span class="listTitleColor2">Unknown</span></div>
<div class="listInfo"><p class="listIcons">40 Count - Wall Partenaire Music: Song Three - Artist</p></div></div>
<a href="/search?Search=Cowboy&recnum=20">Next</a>
</body></html>
"""
PAGE2 = """
<html><body>
<div class="listitem"><div class="listTitle">
<a href="/stepsheets/BBB222/dance-two"><span class="listTitleColor1">Dance Two</span></a>
<span class="listTitleColor2">John Doe (UK) - September 2026</span></div>
<div class="listInfo"><p class="listIcons">64 Count 2 Wall Improver Music: Song Two - Artist</p></div></div>
</body></html>
"""


class FakeSession:
    def __init__(self):
        self.urls = []
        self.headers = {}
        self.proxies = {}
        self.verify = True

    def get(self, url, timeout=None):
        self.urls.append(url)
        html = PAGE2 if "recnum=20" in url else PAGE1
        return FakeResponse(html)

    def close(self):
        pass


class FakeResponse:
    def __init__(self, html):
        self.text = html
        self.status_code = 200

    def raise_for_status(self):
        pass


def test_search_flow():
    client = C.CopperKnobClient()
    client._session = FakeSession()
    try:
        res = client.search("Cowboy", max_results=3)
        assert len(res) == 3, res
        assert res[0]["title"] == "Dance One", res[0]
        assert res[0]["id"] == "AAA111"
        assert res[0]["level"] == "Beginner"
        assert res[0]["music"] == "Song One - Artist"
        # mid-word <mark> stays joined; dateless choreographer kept;
        # "- Wall" leaves walls=None and doesn't leak into level
        assert res[1]["title"] == "Cowboys Mix", res[1]
        assert res[1]["choreographer"] == "Unknown", res[1]
        assert res[1]["date"] is None, res[1]
        assert res[1]["walls"] is None, res[1]
        assert res[1]["level"] == "Partenaire", res[1]
        assert res[2]["title"] == "Dance Two"
        assert "Search=Cowboy" in client._session.urls[0]
        assert "recnum=20" in client._session.urls[1], client._session.urls
        # max_results smaller than a page -> single fetch
        client._session.urls.clear()
        res = client.search("Cowboy", max_results=1)
        assert len(res) == 1 and len(client._session.urls) == 1
        # URL builder uses the real form fields
        url = client._search_url("A B", level="Beginner", wall="4")
        assert "Search=A+B" in url and "Level=Beginner" in url and "Wall=4" in url, url
    finally:
        client.close()
    print("client flow tests: OK")


def test_challenge_detection():
    assert C._looks_challenged("<html><title>Just a moment...</title>challenges.cloudflare.com</html>")
    assert not C._looks_challenged(PAGE1)


if __name__ == "__main__":
    test_search_flow()
    test_challenge_detection()

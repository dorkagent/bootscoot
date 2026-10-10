# bootscoot

Line-dance stepsheet search as a Python module and CLI. Give it a query,
get structured results — title, choreographer, date, count, walls, level,
music, URL. Plain HTTP, no browser needed.

```python
from bootscoot import search

for dance in search("Cowboy Charleston", max_results=10):
    print(dance["title"], "-", dance["choreographer"], "-", dance["url"])
```

```bash
bootscoot "Bailando" --level Beginner --format json
```

## Install

```bash
python -m venv .venv && source .venv/bin/activate   # recommended
pip install -e .
```

Needs only `requests` + `beautifulsoup4`.

## Target site

The site to search is a variable, not hardcoded:

```python
from bootscoot import CopperKnobClient

with CopperKnobClient(base_url="https://www.example-stepsheets.com") as client:
    results = client.search("Cowboy Charleston", max_results=10)
```

or from the CLI:

```bash
bootscoot "Bailando" --base-url https://www.example-stepsheets.com
```

Omit `base_url` to use the default — the site the parser was built and
tested against (see `BASE_URL` in `bootscoot/client.py`).

## API

### `search(query, **kwargs)` → `list[dict]`

One-shot convenience function. Opens a client, searches, closes it.

### `CopperKnobClient(base_url=None, ...)`

Long-lived client (context manager, keeps one HTTP session). `search()`
accepts the search-form filters:

| kwarg | default | meaning |
|---|---|---|
| `query` | — | search text |
| `order` | `"Date"` | result ordering |
| `level` | `""` | e.g. `"Beginner"`, `"Improver"`, `"Intermediate"` |
| `wall` | `""` | wall count, e.g. `"4"` |
| `lang` | `""` | stepsheet language |
| `beat_from` / `beat_to` | `""` | BPM range |
| `max_results` | `None` | cap total results (follows pagination, 20/page) |
| `max_pages` | `10` | safety cap on pages followed |

Each result dict:

```python
{
    "id": "22B54H3",
    "title": "EZ Rhinestone Cowboy",
    "url": "https://<domain>/stepsheets/22B54H3/ez-rhinestone-cowboy",
    "choreographer": "Pat Wilson (NZ)",
    "date": "October 2026",
    "count": 32,
    "walls": 4,
    "level": "Beginner",
    "music": "Rhinestone Cowboy - Glen Campbell",
}
```

Missing fields are `None` rather than raising. Requests are spaced ~1s
apart (`delay_between_requests`) to stay polite; don't hammer the site in
a tight loop.

Notes on the data: `level` comes back in the site's own language, so
French sheets report values like `Débutant` instead of `Beginner` —
filter on it accordingly. The `base_url` variable sets the network
target; the result parser itself matches this site's markup
(`div.listitem`), so pointing it elsewhere only works for sites serving
the same layout.

### CLI

```
bootscoot "Cowboy Charleston" --max-results 10
bootscoot "Bailando" --level Beginner --format json
bootscoot "Waltz" --wall 4 --beat-from 80 --beat-to 100
```

Options: `--level`, `--wall`, `--lang`, `--beat-from`, `--beat-to`,
`--order`, `--max-results`, `--format text|json`, `--proxy`,
`--base-url`.

## Notes & limits

* If the target ever starts serving bot challenges, fetches raise
  `CloudflareChallengeError` instead of returning garbage — the client
  won't silently hand you a challenge page as results.
* The parser keys off the result markup (`div.listitem`), so it
  tolerates minor site redesigns, but a big markup change may need a
  parser tweak.
* Behind a proxy: pass `proxy="http://user:pass@host:3128"` (or `--proxy`
  on the CLI).

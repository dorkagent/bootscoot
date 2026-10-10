# bootscoot

A Python module for using [copperknob.co.uk](https://copperknob.co.uk)'s
line-dance stepsheet search programmatically — from your own scripts or
straight from the command line. No browser, no Selenium/Playwright: the
`www` host serves plain HTTP requests fine (the bare apex domain is the
one behind the Cloudflare challenge, so the client uses `www`).

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

## API

### `search(query, **kwargs)` → `list[dict]`

One-shot convenience function. Opens a client, searches, closes it.

### `CopperKnobClient(...)`

Long-lived client (context manager, keeps one HTTP session). `search()`
accepts the site's own search-form filters:

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
    "url": "https://www.copperknob.co.uk/stepsheets/22B54H3/ez-rhinestone-cowboy",
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

### CLI

```
bootscoot "Cowboy Charleston" --max-results 10
bootscoot "Bailando" --level Beginner --format json
bootscoot "Waltz" --wall 4 --beat-from 80 --beat-to 100
```

Options: `--level`, `--wall`, `--lang`, `--beat-from`, `--beat-to`,
`--order`, `--max-results`, `--format text|json`, `--proxy`.

## Notes & limits

* If Cloudflare ever starts challenging the `www` host too, fetches raise
  `CloudflareChallengeError` instead of returning garbage — the client
  won't silently hand you a challenge page as results.
* The parser keys off the real result markup (`div.listitem`), so it
  tolerates minor site redesigns, but a big markup change may need a
  parser tweak.
* Behind a proxy: pass `proxy="http://user:pass@host:3128"` (or `--proxy`
  on the CLI).

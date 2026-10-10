# bootscoot

Line-dance stepsheet search in two single files — no install step, just
download and run. Give it a query, get structured results (title,
choreographer, date, count, walls, level, music, URL) your script can
take over from there. Plain HTTP, no browser needed, and the target site
is a variable in both — not hardcoded.

- **`bootscoot.py`** — Python. Needs `requests` + `beautifulsoup4`.
  ```bash
  python bootscoot.py "Bailando" --max-results 10 --format json
  ```
  Or import it:
  ```python
  from bootscoot import search
  for dance in search("Bailando", max_results=5):
      print(dance["title"], dance["url"])
  ```
- **`BootScoot.ps1`** — PowerShell. No dependencies.
  ```powershell
  .\BootScoot.ps1 "Bailando" -MaxResults 10
  .\BootScoot.ps1 "Bailando" -AsJson | Out-File results.json
  # or dot-source it and use the functions:
  . .\BootScoot.ps1
  Search-Stepsheets "Cowboy" | Where-Object { $_.Level -eq "Beginner" }
  ```

## Notes

- `level` comes back in the site's own language, so French sheets report
  values like `Débutant` instead of `Beginner` — filter on it accordingly.
- The `base_url` / `-BaseUrl` variable sets the network target; the
  result parser itself matches the site's markup (`div.listitem`), so
  pointing it elsewhere only works for sites serving the same layout.
- Requests are spaced ~1s apart to stay polite; don't hammer the site
  in a tight loop.

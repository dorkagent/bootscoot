# bootscoot

Line-dance stepsheet search in three flavors — Python, PowerShell,
JavaScript. Each one does the same job: give it a query, get structured
results (title, choreographer, date, count, walls, level, music, URL)
your script can take over from there. Plain HTTP, no browser needed, and
the target site is a variable in all three — not hardcoded.

- **[python/](python/)** — module + CLI. `from bootscoot import search`
- **[powershell/](powershell/)** — `BootScoot.psm1`. `Search-Stepsheets` returns objects you pipe anywhere
- **[javascript/](javascript/)** — zero-dependency Node module + CLI

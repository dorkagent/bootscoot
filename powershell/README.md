# BootScoot (PowerShell)

One function. Returns objects your script pipes anywhere.

```powershell
Import-Module ./BootScoot.psm1

Search-Stepsheets "Bailando" -MaxResults 10
Search-Stepsheets "Bailando" -MaxResults 10 -AsJson | Out-File results.json
Search-Stepsheets "Cowboy" | Where-Object { $_.Level -eq "Beginner" } | Select-Object Title, Url
```

Params: `-Query`, `-BaseUrl` (target site, defaults to the site the
parser was built for), `-Level`, `-Wall`, `-Lang`, `-Order` (default
`Date`), `-MaxResults` (default 20, follows pagination), `-MaxPages`
(default 10, safety cap), `-DelaySeconds` (default 1, politeness pause),
`-AsJson` (output a JSON string instead of objects).

Note: `Level` comes back in the site's own language (e.g. `Débutant` on
French sheets).

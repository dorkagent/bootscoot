# BootScoot (PowerShell)

One function. Returns objects your script pipes anywhere.

```powershell
Import-Module ./BootScoot.psm1

Search-Stepsheets "Bailando" -MaxResults 10
Search-Stepsheets "Bailando" -MaxResults 10 -AsJson | Out-File results.json
Search-Stepsheets "Cowboy" | Where-Object { $_.Level -eq "Beginner" } | Select-Object Title, Url
```

Params: `-Query`, `-BaseUrl` (target site, defaults to the site the
parser was built for), `-Level`, `-Wall`, `-Lang`, `-MaxResults` (default
20, follows pagination), `-DelaySeconds` (default 1, politeness pause),
`-AsJson` (output a JSON string instead of objects).

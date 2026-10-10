# BootScoot - line-dance stepsheet search.
# Import-Module ./BootScoot.psm1 ; Search-Stepsheets "Bailando" | ConvertTo-Json

$script:DefaultBaseUrl = "https://www.copperknob.co.uk"
$script:UserAgent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
$script:ChallengeMarkers = @("challenges.cloudflare.com", "just a moment", "verify you are human")

function ConvertFrom-HtmlText {
    param([string]$Html)
    $t = $Html -replace '</?mark[^>]*>', ''   # unwrap highlights: "<mark>Cowboy</mark>s" stays "Cowboys"
    $t = $t -replace '<[^>]+>', ' '
    $t = [System.Net.WebUtility]::HtmlDecode($t)  # every named + numeric entity (&#233;, &eacute;, &nbsp; ...)
    ($t -replace '\s+', ' ').Trim()             # .NET \s also matches the non-breaking space
}

function Test-ChallengePage {
    param([string]$Html)
    if (-not $Html) { return $false }
    $low = $Html.ToLowerInvariant()
    if ($low.Contains("listitem")) { return $false }
    foreach ($m in $script:ChallengeMarkers) { if ($low.Contains($m)) { return $true } }
    return $false
}

function ConvertFrom-StepsheetHtml {
    <#
    .SYNOPSIS
        Parse one search-results page into result objects (no network).
    #>
    [CmdletBinding()]
    param(
        [Parameter(Mandatory)][AllowEmptyString()][string]$Html,
        [string]$BaseUrl = $script:DefaultBaseUrl
    )
    $base = $BaseUrl.TrimEnd("/")
    $blocks = [regex]::Matches($Html, '<div class="listitem"[^>]*>([\s\S]*?)</div>\s*</div>')
    foreach ($b in $blocks) {
        $block = $b.Groups[1].Value
        if ($block -match '<a href="([^"]+)"') { $href = $Matches[1] } else { continue }
        if ($href -match '/stepsheets/([A-Za-z0-9]+)/') { $id = $Matches[1] } else { continue }
        $url = [System.Net.WebUtility]::HtmlDecode($href)
        if ($url -notmatch '^https?://') { $url = $base + '/' + $url.TrimStart('/') }

        $title = $null
        if ($block -match '<span class="listTitleColor1">([\s\S]*?)</span>') {
            $title = ConvertFrom-HtmlText $Matches[1]
            if (-not $title) { $title = $null }
        }

        $choreographer = $null; $date = $null
        if ($block -match '<span class="listTitleColor2">([\s\S]*?)</span>') {
            $parts = (ConvertFrom-HtmlText $Matches[1]) -split '\s+-\s+'
            if ($parts[0]) { $choreographer = $parts[0] }
            if ($parts.Count -gt 1) { $date = $parts[1] }
        }

        $count = $null; $walls = $null; $level = $null; $music = $null
        if ($block -match '<p class="listIcons">([\s\S]*?)</p>') {
            $info = ConvertFrom-HtmlText $Matches[1]
            if ($info -match '(\d+)\s*Count') { $count = [int]$Matches[1] }
            # Capture before testing: a second -match would overwrite $Matches (walls came back 0).
            if ($info -match '(\d+|-)\s*Wall') {
                $w = $Matches[1]
                if ($w -match '^\d+$') { $walls = [int]$w }
            }
            if ($info -match 'Music:\s*(.+)$') {
                $music = $Matches[1].Trim()
                if (-not $music) { $music = $null }
                $before = $info.Substring(0, $info.IndexOf($Matches[0]))
                $level = (($before -replace '\d+\s*Count', '') -replace '(\d+|-)\s*Wall', '').Trim(' -')
                if (-not $level) { $level = $null }
            }
        }

        [pscustomobject]@{
            Id            = $id
            Title         = $title
            Url           = $url
            Choreographer = $choreographer
            Date          = $date
            Count         = $count
            Walls         = $walls
            Level         = $level
            Music         = $music
        }
    }
}

function Invoke-StepsheetRequest {
    param([string]$Uri)
    try {
        $resp = Invoke-WebRequest -Uri $Uri -Headers @{ "User-Agent" = $script:UserAgent } `
            -UseBasicParsing -ErrorAction Stop
    } catch {
        $status = $null
        if ($_.Exception.Response) { $status = [int]$_.Exception.Response.StatusCode }
        $body = $_.ErrorDetails.Message
        if ($status -eq 403 -and (Test-ChallengePage $body)) {
            throw "BootScoot: blocked by a bot challenge (HTTP 403). Wait a while and retry; if it persists, the site's bot policy changed."
        }
        if ($status -eq 429) {
            throw "BootScoot: rate limited (HTTP 429). Slow down (-DelaySeconds) and retry later."
        }
        if ($status) { throw "BootScoot: HTTP $status for $Uri" }
        throw "BootScoot: request failed for ${Uri}: $($_.Exception.Message)"
    }
    if (Test-ChallengePage $resp.Content) {
        throw "BootScoot: blocked by a bot challenge. Wait a while and retry; if it persists, the site's bot policy changed."
    }
    return $resp.Content
}

function Search-Stepsheets {
    <#
    .SYNOPSIS
        Search line-dance stepsheets. Returns objects your script can pipe anywhere.
    .EXAMPLE
        Search-Stepsheets "Cowboy Charleston" -MaxResults 10 | ConvertTo-Json
    #>
    [CmdletBinding()]
    param(
        [Parameter(Mandatory, Position = 0)][string]$Query,
        [string]$BaseUrl = $script:DefaultBaseUrl,
        [string]$Level = "",
        [string]$Wall = "",
        [string]$Lang = "",
        [string]$Order = "Date",
        [ValidateRange(1, 10000)][int]$MaxResults = 20,
        [ValidateRange(1, 1000)][int]$MaxPages = 10,
        [ValidateRange(0, 60)][int]$DelaySeconds = 1,
        [switch]$AsJson
    )

    $base = $BaseUrl.TrimEnd("/")
    $results = [System.Collections.Generic.List[object]]::new()
    $seen = [System.Collections.Generic.HashSet[string]]::new()
    $recnum = 0

    for ($page = 1; $page -le $MaxPages; $page++) {
        $qs = "Order=$([uri]::EscapeDataString($Order))" +
              "&Lang=$([uri]::EscapeDataString($Lang))" +
              "&Level=$([uri]::EscapeDataString($Level))" +
              "&Wall=$([uri]::EscapeDataString($Wall))" +
              "&Search=$([uri]::EscapeDataString($Query))"
        if ($recnum -gt 0) { $qs += "&recnum=$recnum" }

        $html = Invoke-StepsheetRequest "$base/search?$qs"
        $batch = @(ConvertFrom-StepsheetHtml -Html $html -BaseUrl $base)
        if ($batch.Count -eq 0) { break }

        $new = 0
        foreach ($r in $batch) {
            if ($seen.Add($r.Id)) { $results.Add($r); $new++ }
            if ($results.Count -ge $MaxResults) { break }
        }
        # Stop if the page added nothing new (site ignored recnum) or we have enough.
        if ($new -eq 0 -or $results.Count -ge $MaxResults) { break }

        $recnum += 20
        Start-Sleep -Seconds $DelaySeconds
    }

    if ($AsJson) { return ($results | ConvertTo-Json -Depth 3) }
    return $results.ToArray()
}

Export-ModuleMember -Function Search-Stepsheets, ConvertFrom-StepsheetHtml

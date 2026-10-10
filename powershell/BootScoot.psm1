# BootScoot - line-dance stepsheet search.
# Import-Module ./BootScoot.psm1 ; Search-Stepsheets "Bailando" | ConvertTo-Json

$script:DefaultBaseUrl = "https://www.copperknob.co.uk"
$script:UserAgent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"

function ConvertFrom-HtmlText {
    param([string]$Html)
    $t = $Html -replace '</?mark>', '' # unwrap highlights: "<mark>Cowboy</mark>s" stays "Cowboys"
    $t = $t -replace '<[^>]+>', ' '
    $t = $t -replace '&nbsp;', ' '
    $t = $t -replace '&lt;', '<'
    $t = $t -replace '&gt;', '>'
    $t = $t -replace '&quot;', '"'
    $t = $t -replace '&#39;', "'"
    $t = $t -replace '&amp;', '&'
    ($t -replace '\s+', ' ').Trim()
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
        [int]$MaxResults = 20,
        [int]$MaxPages = 10,
        [int]$DelaySeconds = 1,
        [switch]$AsJson
    )

    $base = $BaseUrl.TrimEnd("/")
    $results = @()
    $recnum = 0
    $page = 0

    do {
        $page++
        $qs = "Order=$([uri]::EscapeDataString($Order))" +
              "&Lang=$([uri]::EscapeDataString($Lang))" +
              "&Level=$([uri]::EscapeDataString($Level))" +
              "&Wall=$([uri]::EscapeDataString($Wall))" +
              "&Search=$([uri]::EscapeDataString($Query))"
        if ($recnum -gt 0) { $qs += "&recnum=$recnum" }

        $html = (Invoke-WebRequest -Uri "$base/search?$qs" `
            -Headers @{ "User-Agent" = $script:UserAgent } -UseBasicParsing).Content

        $blocks = [regex]::Matches($html, '<div class="listitem"[^>]*>([\s\S]*?)</div>\s*</div>')
        if ($blocks.Count -eq 0) { break }

        foreach ($b in $blocks) {
            $block = $b.Groups[1].Value
            if ($block -match '<a href="([^"]+)"') { $href = $Matches[1] } else { continue }
            if ($href -match '/stepsheets/([A-Za-z0-9]+)/') { $id = $Matches[1] } else { continue }
            $url = $href
            if ($url -notmatch '^https?://') { $url = $base + '/' + $url.TrimStart('/') }

            $title = $null
            if ($block -match '<span class="listTitleColor1">([\s\S]*?)</span>') {
                $title = ConvertFrom-HtmlText $Matches[1]
            }

            $choreographer = $null; $date = $null
            if ($block -match '<span class="listTitleColor2">([\s\S]*?)</span>') {
                $parts = (ConvertFrom-HtmlText $Matches[1]) -split '\s+-\s+'
                $choreographer = $parts[0]
                if ($parts.Count -gt 1) { $date = $parts[1] }
            }

            $count = $null; $walls = $null; $level = $null; $music = $null
            if ($block -match '<p class="listIcons">([\s\S]*?)</p>') {
                $info = ConvertFrom-HtmlText $Matches[1]
                if ($info -match '(\d+)\s*Count') { $count = [int]$Matches[1] }
                if ($info -match '(\d+|-)\s*Wall' -and $Matches[1] -match '^\d+$') { $walls = [int]$Matches[1] }
                if ($info -match 'Music:\s*(.+)$') {
                    $music = $Matches[1].Trim()
                    $before = $info.Substring(0, $info.IndexOf($Matches[0]))
                    $level = (($before -replace '\d+\s*Count', '') -replace '(\d+|-)\s*Wall', '').Trim(' -')
                    if (-not $level) { $level = $null }
                }
            }

            $results += [pscustomobject]@{
                Id           = $id
                Title        = $title
                Url          = $url
                Choreographer = $choreographer
                Date         = $date
                Count        = $count
                Walls        = $walls
                Level        = $level
                Music        = $music
            }
            if ($results.Count -ge $MaxResults) { break }
        }

        $recnum += 20
        if ($results.Count -lt $MaxResults -and $blocks.Count -gt 0) {
            Start-Sleep -Seconds $DelaySeconds
        }
    } while ($page -lt $MaxPages -and $results.Count -lt $MaxResults -and $blocks.Count -gt 0)

    if ($AsJson) { return ($results | ConvertTo-Json -Depth 3) }
    return $results
}

Export-ModuleMember -Function Search-Stepsheets

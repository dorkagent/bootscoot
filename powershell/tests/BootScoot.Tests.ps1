# Invoke-Pester ./tests   (Pester 5+)
BeforeAll {
    Import-Module "$PSScriptRoot/../BootScoot.psm1" -Force
    $script:Fixture = Get-Content "$PSScriptRoot/fixture.html" -Raw
}

Describe "ConvertFrom-StepsheetHtml" {
    BeforeAll { $script:R = @(ConvertFrom-StepsheetHtml -Html $Fixture) }

    It "parses every result" { $R.Count | Should -Be 3 }

    It "parses a standard row" {
        $r = $R[0]
        $r.Id            | Should -Be "22B54H3"
        $r.Title         | Should -Be "EZ Rhinestone Cowboy"
        $r.Url           | Should -Be "https://www.copperknob.co.uk/stepsheets/22B54H3/ez-rhinestone-cowboy"
        $r.Choreographer | Should -Be "Pat Wilson (NZ)"
        $r.Date          | Should -Be "October 2026"
        $r.Count         | Should -Be 32
        $r.Walls         | Should -Be 4
        $r.Level         | Should -Be "Beginner"
        $r.Music         | Should -Be "Rhinestone Cowboy - Glen Campbell"
    }

    It "handles '- Wall' partner dances without leaking into Level" {
        $R[1].Walls | Should -BeNullOrEmpty
        $R[1].Level | Should -Be "Beginner Partner"
    }

    It "keeps mid-word highlight joined" { $R[1].Music | Should -Be "Coconut Dreams - Cowboys and Indie" }

    It "decodes named and numeric entities" {
        $R[1].Choreographer | Should -Be "France Bastien (CAN) & Serge Légaré (CAN)"
    }

    It "absolutizes relative URLs" {
        $R[1].Url | Should -Be "https://www.copperknob.co.uk/stepsheets/HG42HPZ/coconut-dream-for-2-p"
    }

    It "keeps a dateless choreographer" {
        $R[2].Choreographer | Should -Be "Dancing Cowboy Jim"
        $R[2].Date          | Should -BeNullOrEmpty
    }

    It "returns nothing for an empty page" {
        @(ConvertFrom-StepsheetHtml -Html "<html>no results</html>").Count | Should -Be 0
    }

    It "throws a clear error on a 200 challenge page" {
        InModuleScope BootScoot {
            Mock Invoke-WebRequest { [pscustomobject]@{ Content = "<title>Just a moment...</title>challenges.cloudflare.com" } }
            { Search-Stepsheets "x" -DelaySeconds 0 } | Should -Throw "*bot challenge*"
        }
    }

    It "turns a network failure into a BootScoot error" {
        { Search-Stepsheets "x" -BaseUrl "http://127.0.0.1:1" -DelaySeconds 0 } | Should -Throw "BootScoot:*"
    }
}

Describe "Search-Stepsheets (mocked network)" {
    It "dedupes and stops when the site repeats the same page" {
        InModuleScope BootScoot -Parameters @{ F = $Fixture } {
            param($F)
            Mock Invoke-WebRequest { [pscustomobject]@{ Content = $F } }
            $r = @(Search-Stepsheets "Cowboy" -MaxResults 50 -DelaySeconds 0)
            $r.Count | Should -Be 3
            Should -Invoke Invoke-WebRequest -Times 2 -Exactly
        }
    }

    It "caps at MaxResults with a single request" {
        InModuleScope BootScoot -Parameters @{ F = $Fixture } {
            param($F)
            Mock Invoke-WebRequest { [pscustomobject]@{ Content = $F } }
            @(Search-Stepsheets "Cowboy" -MaxResults 2 -DelaySeconds 0).Count | Should -Be 2
            Should -Invoke Invoke-WebRequest -Times 1 -Exactly
        }
    }
}

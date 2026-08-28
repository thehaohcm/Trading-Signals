# ==============================================================================
#  Trading Signals Deployment Launcher for Windows PowerShell
# ==============================================================================
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path

# Locate Git Bash
$GitBashLocations = @(
    "C:\Program Files\Git\bin\bash.exe",
    "C:\Program Files\Git\usr\bin\bash.exe",
    "C:\Users\$env:USERNAME\AppData\Local\Programs\Git\bin\bash.exe"
)

$GitBash = $null
foreach ($loc in $GitBashLocations) {
    if (Test-Path $loc) {
        $GitBash = $loc
        break
    }
}

if ($GitBash) {
    & $GitBash "$ScriptDir/deploy.sh"
} else {
    Write-Host "✗ Error: Git Bash was not found in standard paths." -ForegroundColor Red
    Write-Host "Please install Git for Windows or run deploy.sh within Git Bash." -ForegroundColor Yellow
}

param(
    [Parameter(Mandatory = $true)]
    [string]$Mt5DataDir,
    [switch]$Force
)

$ErrorActionPreference = "Stop"
$targetDir = Join-Path $Mt5DataDir "MQL5\Experts\GoldAITrader"
$modulesTarget = Join-Path $targetDir "modules"

if (Test-Path $targetDir) {
    $timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
    $backupDir = "${targetDir}_backup_${timestamp}"
    if (-not $Force) {
        $confirm = Read-Host "Existing EA found at '$targetDir'. Create backup and overwrite? (y/N)"
        if ($confirm -ne "y" -and $confirm -ne "Y") {
            Write-Host "Deployment cancelled." -ForegroundColor Yellow
            exit 0
        }
    }
    Copy-Item -Path $targetDir -Destination $backupDir -Recurse -Force
    Write-Host "Backed up existing EA to $backupDir" -ForegroundColor Cyan
}

New-Item -ItemType Directory -Path $modulesTarget -Force | Out-Null
Copy-Item "trading-engine\GoldAITrader.mq5" -Destination $targetDir -Force
Copy-Item "trading-engine\modules\*.mqh" -Destination $modulesTarget -Force

Write-Host "Deployed GoldAITrader EA to $targetDir" -ForegroundColor Green
Write-Host "Next: Open MetaEditor -> compile MQL5\Experts\GoldAITrader\GoldAITrader.mq5" -ForegroundColor Yellow

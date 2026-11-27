$ErrorActionPreference = "Stop"
Write-Host "Running Python Pytest suite..." -ForegroundColor Cyan
& "ai-service\.venv\Scripts\python.exe" -m pytest "ai-service\tests" -v
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host "Running Dashboard Vitest & Build..." -ForegroundColor Cyan
Push-Location "dashboard"
npm test
if ($LASTEXITCODE -ne 0) { Pop-Location; exit $LASTEXITCODE }
npm run build
$buildCode = $LASTEXITCODE
Pop-Location
if ($buildCode -ne 0) { exit $buildCode }

Write-Host "All tests and builds succeeded!" -ForegroundColor Green

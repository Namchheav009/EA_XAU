$ErrorActionPreference = "Stop"
Write-Host "Setting up GoldAITrader..." -ForegroundColor Cyan

if (!(Test-Path "ai-service\.venv")) {
    python -m venv "ai-service\.venv"
}
& "ai-service\.venv\Scripts\python.exe" -m pip install --upgrade pip
& "ai-service\.venv\Scripts\python.exe" -m pip install -r "ai-service\requirements.txt"

if (!(Test-Path "ai-service\.env") -and (Test-Path "ai-service\.env.example")) {
    Copy-Item "ai-service\.env.example" "ai-service\.env"
}

Push-Location "dashboard"
npm install
Pop-Location

& "ai-service\.venv\Scripts\python.exe" "database\init_db.py"
Write-Host "GoldAITrader setup complete!" -ForegroundColor Green

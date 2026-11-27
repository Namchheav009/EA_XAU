Start-Process powershell -ArgumentList "-NoExit", "-File", "$PSScriptRoot\start-backend.ps1"
Start-Process powershell -ArgumentList "-NoExit", "-File", "$PSScriptRoot\start-dashboard.ps1"
Write-Host "Started Backend (http://127.0.0.1:8000) and Dashboard (http://localhost:5173)." -ForegroundColor Green

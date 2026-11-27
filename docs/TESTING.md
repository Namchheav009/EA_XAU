# Testing Guide

## Run All Tests
```powershell
.\scripts\run-tests.ps1
```

## Python Backend (Pytest)
```powershell
.\ai-service\.venv\Scripts\python.exe -m pytest ai-service\tests -v
```
Covers: technical indicators, strategy signals, Cent lot sizing & min-lot rejection, daily loss & drawdown limits, real-account execution blocking, AI missing-model `WAIT` fallback, backtesting engine, and REST API endpoints.

## React Dashboard (Vitest)
```powershell
cd dashboard
npm test
npm run build
```

## MQL5 Compilation
MQL5 compilation requires MetaEditor (`metaeditor64.exe`). If MetaTrader 5 is not installed on the development machine, MQL5 compilation must be verified manually in MetaEditor after deploying with `scripts/deploy-ea.ps1`.

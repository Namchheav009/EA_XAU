# MetaTrader 5 & Exness Setup

1. Install **MetaTrader 5 Desktop (64-bit)** from your Exness Personal Area.
2. Open MT5 and log into your **Exness Demo** account (`File -> Login to Trade Account`).
3. Find `terminal64.exe` path:
   ```powershell
   Get-Process terminal64 -ErrorAction SilentlyContinue | Select-Object Id, Path
   ```
4. Set `DATA_MODE=MT5` and `MT5_TERMINAL_PATH=<your path>` in `ai-service\.env`.
5. In MT5 (`Tools -> Options -> Expert Advisors`), enable **Allow WebRequest for listed URL** and add `http://127.0.0.1:8000` so `AIClient.mqh` can reach FastAPI.

# Deployment Guide

## Deploying the MQL5 Expert Advisor
1. Locate your MT5 Data Folder (`File -> Open Data Folder` in MT5).
2. Run:
   ```powershell
   .\scripts\deploy-ea.ps1 -Mt5DataDir "C:\Users\<USER>\AppData\Roaming\MetaQuotes\Terminal\<ID>"
   ```
   Existing deployments are backed up before overwriting.
3. Open **MetaEditor**, open `MQL5\Experts\GoldAITrader\GoldAITrader.mq5`, and press **F7 (Compile)**.
4. Attach `GoldAITrader` to an `XAUUSDc` M15 chart. **Monitoring Mode** is enabled by default (`InpOperatingMode = MODE_MONITORING`, `InpAllowDemoTrading = false`).
5. **Real-account automated execution is blocked in code** (`SafetyManager.mqh`).

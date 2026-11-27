# Standard Cent (`USC`) Account Guide

Exness Standard Cent accounts denominate balances in **USC** (US Cents): `$100 USD = 10,000 USC`.

## How GoldAITrader Handles Cent Accounts
- **Automatic Detection**: `RiskManager.mqh` checks `AccountInfoString(ACCOUNT_CURRENCY)` for `USC` and symbol suffix `c` (`XAUUSDc`).
- **Broker-Aware Sizing**: MQL5 uses `OrderCalcProfit()` so all profit/loss calculations are natively in `USC` without hardcoded conversion factors.
- **Min-Lot Protection**: On a `10,000 USC` account with `0.5%` risk (`50 USC` budget), if `0.01` lot at the ATR stop loss risks more than `50 USC`, `RiskManager` rejects the trade rather than violating your risk limit.

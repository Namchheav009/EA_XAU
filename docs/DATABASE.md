# Database Schema

Engine: SQLite (`database/goldaitrader.db`) managed via SQLAlchemy 2.x (`ai-service/repositories/models.py`).

## Tables
- `accounts` — Broker account metadata (`account_type` CENT/STANDARD, `currency` USC/USD, `is_mock`). Passwords are never stored.
- `market_candles` — Cached OHLCV bars (`symbol`, `timeframe`, `timestamp_utc` unique constraint).
- `trading_signals` — Evaluated BUY/SELL/WAIT signals, scores, and rejection reasons.
- `trades` & `positions` — Closed trade history and open positions with UTC timestamps.
- `trading_sessions`, `risk_events`, `daily_performance`, `economic_events`
- `ai_models` & `ai_predictions` — Versioned model metrics and inference logs.
- `backtest_runs` & `backtest_trades` — Persisted backtest runs and trade-by-trade logs.
- `system_logs` & `settings` — Audit logs and persisted configuration.

Initialize & seed mock development data:
```powershell
.\scripts\init-database.ps1
```

# REST API Reference

Base URL: `http://127.0.0.1:8000` (Swagger UI at `/docs`).

## System & MT5
- `GET /` — Project metadata
- `GET /health` — Health check
- `GET /mt5/status` — Legacy MT5 status
- `GET /api/v1/system/status` — System mode, emergency stop, connector status
- `GET /api/v1/system/config` / `PUT /api/v1/system/config` — Configuration
- `POST /api/v1/system/emergency-stop?active=true&reason=...` — Emergency stop toggle
- `GET /api/v1/mt5/status`, `/account`, `/symbols`, `/symbol-info`

## Market & Trading
- `GET /api/v1/market/price`, `/candles`, `/indicators`, `/trend`, `/analysis`, `/support-resistance`
- `GET /api/v1/trading/signals`, `/positions`, `/history`, `/performance`

## Risk, AI, News & Backtesting
- `POST /api/v1/risk/calculate`, `GET /api/v1/risk/status`, `GET /api/v1/risk/drawdown`
- `POST /api/v1/ai/predict`, `GET /api/v1/ai/status`, `GET /api/v1/ai/metrics`
- `GET /api/v1/news/upcoming`, `GET /api/v1/news/status`
- `POST /api/v1/backtesting/run`, `GET /api/v1/backtesting/results`, `GET /api/v1/backtesting/results/{id}`

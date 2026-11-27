# GoldAITrader Architecture

```mermaid
flowchart LR
    MT5[MT5 Terminal / XAUUSDc] <-->|IPC / MQL5| EA[GoldAITrader.mq5]
    EA -->|HTTP POST /api/v1/ai/predict| API[FastAPI Backend 127.0.0.1:8000]
    API <-->|Mock or MT5 Connector| CONN[Data Connectors]
    API <-->|SQLAlchemy| DB[(SQLite DB)]
    API <-->|Joblib| AI[Scikit-learn Pipeline]
    UI[React + TS + Vite Dashboard :5173] <-->|REST API| API
```

## Components
- **Trading Engine (`trading-engine/`)**: MQL5 Expert Advisor (`GoldAITrader.mq5`) and modular `.mqh` files enforcing monitoring-by-default, real-account blocking, broker-aware `OrderCalcProfit` sizing, session/news filters, and AI confirmation.
- **Python Backend (`ai-service/`)**: FastAPI server supporting `MOCK` (default) and `MT5` modes, technical analysis, strategies, risk calculator, SQLite persistence, and Scikit-learn AI filtering.
- **Backtesting (`backtesting/`)**: Conservative OHLCV simulator with Cent (`USC`) / Standard (`USD`) accounting, spread, slippage, and commission.
- **Dashboard (`dashboard/`)**: Dark-themed React + TypeScript + Tailwind + Lightweight Charts terminal UI.

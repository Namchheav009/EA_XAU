# Backtesting System

Implemented in `backtesting/engine.py` and exposed via `POST /api/v1/backtesting/run`.

## Features
- Cent (`USC`) and Standard (`USD`) account simulation
- Configurable spread (points), slippage (points), and commission per lot
- Risk-based position sizing, daily loss limit, and max drawdown limit
- Metrics: Net profit, return %, win rate, profit factor, max drawdown %, expectancy, Sharpe ratio

## OHLCV Limitations vs. MT5 Real-Tick Backtesting
- OHLCV bars do not contain intra-bar tick sequences.
- When a single bar's `high` and `low` touch both Stop Loss and Take Profit, this engine **conservatively assumes Stop Loss was hit first**.
- Always validate strategies further in MetaTrader 5 Strategy Tester using **Every tick based on real ticks** before demo forward testing.

# Trading Strategies

All signals are evaluated strictly on **completed candles** (`shift >= 1` in MQL5) to prevent look-ahead bias and duplicate signals.

## Strategy A: Trend-Following Pullback
- **Trend**: H1 `EMA 50 > EMA 200` (bullish) or `EMA 50 < EMA 200` (bearish).
- **Entry**: M15 pullback to `EMA 20`, favorable `RSI(14)`, `MACD` momentum, and confirmed candle body (`>= 40–45%` of range).

## Strategy B: Breakout
- **Entry**: Close beyond 20-bar Support/Resistance with `ADX(14) >= 20`, directional `+DI/-DI`, and `MACD` confirmation.

## Strategy C: Market Regime Filter
- Classifies market into `TRENDING_BULL`, `TRENDING_BEAR`, `RANGING`, or `HIGH_VOLATILITY` (`ATR% > 0.65%`).
- Blocks trend pullbacks during `RANGING` and blocks all entries during `HIGH_VOLATILITY`.

## Scoring (0–100)
Signals below `MinSignalScore` (default `65`) return `WAIT` with explicit `rejection_reasons`.

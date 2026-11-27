# Risk Management

## Default Parameters
- **Risk per trade**: `0.5%` of equity
- **Max daily loss**: `2.0%`
- **Max equity drawdown**: `10.0%` (triggers Emergency Stop)
- **Max daily trades**: `3`
- **Max simultaneous positions**: `1`
- **Risk-to-Reward ratio**: `1:2` (`ATR(14) * 1.5` stop loss)
- **Max consecutive losses**: `3`
- **Martingale / Grid**: Permanently disabled

## Broker-Aware Sizing & Min-Lot Rejection
- MQL5 uses `OrderCalcProfit` and `OrderCalcMargin` so the broker computes exact profit/loss in the account's native currency (`USC` or `USD`).
- If the minimum allowed volume (`0.01` lot) risks more than the configured `0.5%` risk budget (e.g., on a `$100` / `10,000 USC` account during wide ATR), the trade is **rejected** rather than over-leveraging.

## Planned Risk vs. Actual Losses
Lot sizing bounds planned risk at the stop-loss price assuming an exact fill. Actual realized losses may exceed planned risk due to **market gaps, spread widening, commissions, and slippage**.

"""Historical OHLCV Backtesting Engine with conservative SL/TP ordering and Cent account simulation."""

import math
from typing import Any, Dict, List
import numpy as np
import pandas as pd

import sys
from pathlib import Path

AI_SERVICE_DIR = Path(__file__).resolve().parent.parent / "ai-service"
if str(AI_SERVICE_DIR) not in sys.path:
    sys.path.insert(0, str(AI_SERVICE_DIR))

from analysis.indicators import add_all_indicators  # noqa: E402
from risk.calculator import calculate_position_risk  # noqa: E402


def run_backtest(
    df: pd.DataFrame,
    strategy_name: str = "StrategyA_TrendPullback",
    initial_balance: float = 10000.0,
    account_type: str = "CENT",
    risk_percent: float = 0.5,
    atr_multiplier: float = 1.5,
    risk_reward_ratio: float = 2.0,
    spread_points: float = 20.0,
    commission_per_lot: float = 0.0,
    slippage_points: float = 5.0,
    max_daily_loss_pct: float = 2.0,
    max_drawdown_pct: float = 10.0,
) -> Dict[str, Any]:
    """Run conservative OHLCV backtest.

    Conservative intra-bar rule: If a candle's high/low touches BOTH stop-loss
    and take-profit, assume STOP LOSS was hit first (never assume favorable order).
    """
    enriched = add_all_indicators(df)
    currency = "USC" if account_type.upper() == "CENT" else "USD"
    currency_mult = 100.0 if currency == "USC" else 1.0
    point = 0.01
    spread_price = spread_points * point
    slippage_price = slippage_points * point

    balance = initial_balance
    peak_equity = initial_balance
    max_dd_pct = 0.0

    trades: List[Dict[str, Any]] = []
    equity_curve: List[Dict[str, Any]] = []
    open_pos: Dict[str, Any] | None = None

    current_day = None
    day_start_balance = balance
    daily_trades = 0
    consecutive_losses = 0

    for i in range(50, len(enriched)):
        bar = enriched.iloc[i]
        ts = str(bar["timestamp"])
        day_str = ts[:10]
        if day_str != current_day:
            current_day = day_str
            day_start_balance = balance
            daily_trades = 0

        # 1. Check open position exit conservatively
        if open_pos is not None:
            hit_sl = False
            hit_tp = False
            if open_pos["side"] == "BUY":
                hit_sl = float(bar["low"]) <= open_pos["sl"]
                hit_tp = float(bar["high"]) >= open_pos["tp"]
            else:
                hit_sl = float(bar["high"]) >= open_pos["sl"]
                hit_tp = float(bar["low"]) <= open_pos["tp"]

            if hit_sl or hit_tp:
                # Conservative: SL takes precedence if both hit in same OHLC bar
                if hit_sl:
                    exit_price = open_pos["sl"] - slippage_price if open_pos["side"] == "BUY" else open_pos["sl"] + slippage_price
                    exit_reason = "STOP_LOSS"
                else:
                    exit_price = open_pos["tp"] - slippage_price if open_pos["side"] == "BUY" else open_pos["tp"] + slippage_price
                    exit_reason = "TAKE_PROFIT"

                price_diff = (exit_price - open_pos["entry"]) if open_pos["side"] == "BUY" else (open_pos["entry"] - exit_price)
                gross_pnl = price_diff * open_pos["volume"] * 100.0 * currency_mult
                comm = commission_per_lot * open_pos["volume"] * currency_mult
                net_pnl = round(gross_pnl - comm, 2)

                balance = round(balance + net_pnl, 2)
                if net_pnl < 0:
                    consecutive_losses += 1
                else:
                    consecutive_losses = 0

                trades.append(
                    {
                        "side": open_pos["side"],
                        "volume": open_pos["volume"],
                        "entry_price": round(open_pos["entry"], 2),
                        "exit_price": round(exit_price, 2),
                        "pnl": net_pnl,
                        "exit_reason": exit_reason,
                        "opened_at_utc": open_pos["opened_at"],
                        "closed_at_utc": ts,
                    }
                )
                open_pos = None

        peak_equity = max(peak_equity, balance)
        dd = ((peak_equity - balance) / peak_equity) * 100.0 if peak_equity > 0 else 0.0
        max_dd_pct = max(max_dd_pct, dd)
        equity_curve.append({"timestamp": ts, "equity": round(balance, 2), "drawdown_pct": round(dd, 2)})

        # 2. Generate signal on completed bar (i) for entry on next bar open (or close[i] + spread)
        if open_pos is None and i < len(enriched) - 1:
            daily_loss_pct = max(0.0, ((day_start_balance - balance) / day_start_balance) * 100.0) if day_start_balance > 0 else 0.0
            signal = "WAIT"
            if strategy_name == "StrategyB_Breakout":
                prev_high = float(enriched["high"].iloc[i - 20 : i].max())
                prev_low = float(enriched["low"].iloc[i - 20 : i].min())
                if float(bar["close"]) > prev_high and float(bar["adx_14"]) >= 18.0:
                    signal = "BUY"
                elif float(bar["close"]) < prev_low and float(bar["adx_14"]) >= 18.0:
                    signal = "SELL"
            else:
                if float(bar["ema_20"]) > float(bar["ema_50"]) and 40.0 <= float(bar["rsi_14"]) <= 68.0 and float(bar["close"]) > float(bar["open"]):
                    signal = "BUY"
                elif float(bar["ema_20"]) < float(bar["ema_50"]) and 32.0 <= float(bar["rsi_14"]) <= 60.0 and float(bar["close"]) < float(bar["open"]):
                    signal = "SELL"

            if signal != "WAIT":
                next_open = float(enriched.iloc[i + 1]["open"])
                entry = (next_open + spread_price + slippage_price) if signal == "BUY" else (next_open - slippage_price)
                risk_res = calculate_position_risk(
                    equity=balance,
                    account_currency=currency,
                    entry_price=entry,
                    atr_14=float(bar["atr_14"]),
                    signal=signal,
                    risk_percent=risk_percent,
                    atr_multiplier=atr_multiplier,
                    risk_reward_ratio=risk_reward_ratio,
                    daily_loss_pct=daily_loss_pct,
                    max_daily_loss_pct=max_daily_loss_pct,
                    drawdown_pct=dd,
                    max_drawdown_pct=max_drawdown_pct,
                    daily_trades=daily_trades,
                    consecutive_losses=consecutive_losses,
                )
                if risk_res["allowed"]:
                    open_pos = {
                        "side": signal,
                        "volume": risk_res["lot_size"],
                        "entry": entry,
                        "sl": risk_res["stop_loss"],
                        "tp": risk_res["take_profit"],
                        "opened_at": str(enriched.iloc[i + 1]["timestamp"]),
                    }
                    daily_trades += 1

    # Compute performance metrics
    total_trades = len(trades)
    wins = [t["pnl"] for t in trades if t["pnl"] > 0]
    losses = [t["pnl"] for t in trades if t["pnl"] < 0]
    gross_profit = round(sum(wins), 2)
    gross_loss = round(abs(sum(losses)), 2)
    net_profit = round(balance - initial_balance, 2)
    win_rate = round((len(wins) / total_trades) * 100.0, 2) if total_trades > 0 else 0.0
    profit_factor = round(gross_profit / gross_loss, 2) if gross_loss > 0 else (99.0 if gross_profit > 0 else 0.0)
    avg_win = round(float(np.mean(wins)), 2) if wins else 0.0
    avg_loss = round(float(np.mean(losses)), 2) if losses else 0.0
    expectancy = round(net_profit / total_trades, 2) if total_trades > 0 else 0.0

    pnls = np.array([t["pnl"] for t in trades], dtype=float)
    sharpe = round(float((np.mean(pnls) / np.std(pnls)) * math.sqrt(len(pnls))), 2) if len(pnls) > 1 and np.std(pnls) > 0 else 0.0

    return {
        "strategy_name": strategy_name,
        "account_type": account_type,
        "currency": currency,
        "initial_balance": initial_balance,
        "final_balance": round(balance, 2),
        "net_profit": net_profit,
        "total_return_pct": round((net_profit / initial_balance) * 100.0, 2) if initial_balance > 0 else 0.0,
        "gross_profit": gross_profit,
        "gross_loss": gross_loss,
        "win_rate_pct": win_rate,
        "profit_factor": profit_factor,
        "max_drawdown_pct": round(max_dd_pct, 2),
        "expectancy": expectancy,
        "sharpe_ratio": sharpe,
        "average_win": avg_win,
        "average_loss": avg_loss,
        "total_trades": total_trades,
        "trades": trades,
        "equity_curve": equity_curve[-150:],
        "limitations_note": "OHLCV backtesting cannot model intra-bar tick paths; conservative SL-first ordering is applied.",
    }

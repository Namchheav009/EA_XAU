import math
from typing import Any, Dict


def calculate_position_risk(
    equity: float,
    account_currency: str,
    entry_price: float,
    atr_14: float,
    signal: str = "BUY",
    risk_percent: float = 0.5,
    atr_multiplier: float = 1.5,
    risk_reward_ratio: float = 2.0,
    contract_size: float = 100.0,
    volume_min: float = 0.01,
    volume_max: float = 100.0,
    volume_step: float = 0.01,
    daily_loss_pct: float = 0.0,
    max_daily_loss_pct: float = 2.0,
    drawdown_pct: float = 0.0,
    max_drawdown_pct: float = 10.0,
    daily_trades: int = 0,
    max_daily_trades: int = 3,
    consecutive_losses: int = 0,
    max_consecutive_losses: int = 3,
) -> Dict[str, Any]:
    """Calculate broker-aware position sizing and validate all risk protections."""
    is_cent = account_currency.upper() == "USC"

    if daily_loss_pct >= max_daily_loss_pct:
        return _rejected(account_currency, is_cent, f"Daily loss limit reached ({daily_loss_pct:.2f}% >= {max_daily_loss_pct:.2f}%).")
    if drawdown_pct >= max_drawdown_pct:
        return _rejected(account_currency, is_cent, f"Max drawdown limit reached ({drawdown_pct:.2f}% >= {max_drawdown_pct:.2f}%).")
    if daily_trades >= max_daily_trades:
        return _rejected(account_currency, is_cent, f"Max daily trades reached ({daily_trades}/{max_daily_trades}).")
    if consecutive_losses >= max_consecutive_losses:
        return _rejected(account_currency, is_cent, f"Max consecutive losses reached ({consecutive_losses}/{max_consecutive_losses}).")
    if atr_14 <= 0 or equity <= 0:
        return _rejected(account_currency, is_cent, "Equity and ATR must be positive.")

    sl_dist = atr_14 * atr_multiplier
    tp_dist = sl_dist * risk_reward_ratio

    if signal.upper() == "SELL":
        stop_loss = round(entry_price + sl_dist, 2)
        take_profit = round(entry_price - tp_dist, 2)
    else:
        stop_loss = round(entry_price - sl_dist, 2)
        take_profit = round(entry_price + tp_dist, 2)

    # For XAUUSD: 1.0 lot * contract_size (100 oz) * price_move.
    # In a Cent account (USC), 1 USD move = 100 USC, or contract_size reflects USC value.
    # On Exness Standard Cent XAUUSDc, contract_size is 100 oz and 1 USD = 100 USC -> 1.0 lot * 100 * sl_dist * (100 if cent else 1)
    # However, broker OrderCalcProfit handles this natively in MT5; here we model USC/USD explicitly.
    currency_multiplier = 100.0 if is_cent else 1.0
    loss_per_lot = sl_dist * contract_size * currency_multiplier
    risk_budget = equity * (risk_percent / 100.0)

    min_lot_risk = volume_min * loss_per_lot
    if min_lot_risk > risk_budget * 1.05:
        return _rejected(
            account_currency,
            is_cent,
            f"Minimum lot {volume_min} risk ({min_lot_risk:.2f} {account_currency}) exceeds risk budget ({risk_budget:.2f} {account_currency}).",
            stop_loss=stop_loss,
            take_profit=take_profit,
            risk_budget=risk_budget,
        )

    raw_lots = risk_budget / loss_per_lot
    steps = math.floor(raw_lots / volume_step)
    lots = round(max(volume_min, min(volume_max, steps * volume_step)), 2)

    return {
        "allowed": True,
        "account_currency": account_currency,
        "is_cent_account": is_cent,
        "lot_size": lots,
        "stop_loss": stop_loss,
        "take_profit": take_profit,
        "sl_distance": round(sl_dist, 3),
        "tp_distance": round(tp_dist, 3),
        "planned_risk_amount": round(lots * loss_per_lot, 2),
        "risk_budget": round(risk_budget, 2),
        "reason": "Risk validation passed.",
        "risk_note": "Planned risk assumes exact SL fill; actual loss may differ due to gaps, commissions, and slippage.",
    }


def _rejected(
    currency: str,
    is_cent: bool,
    reason: str,
    stop_loss: float = 0.0,
    take_profit: float = 0.0,
    risk_budget: float = 0.0,
) -> Dict[str, Any]:
    return {
        "allowed": False,
        "account_currency": currency,
        "is_cent_account": is_cent,
        "lot_size": 0.0,
        "stop_loss": stop_loss,
        "take_profit": take_profit,
        "sl_distance": 0.0,
        "tp_distance": 0.0,
        "planned_risk_amount": 0.0,
        "risk_budget": round(risk_budget, 2),
        "reason": reason,
        "risk_note": "Trade rejected by RiskManager.",
    }

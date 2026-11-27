from typing import Any, Dict, Optional
from pydantic import BaseModel, Field


class RiskCalculateRequest(BaseModel):
    equity: float = Field(default=10000.0, gt=0)
    account_currency: str = Field(default="USC")
    entry_price: float = Field(default=2650.0, gt=0)
    atr_14: float = Field(default=3.5, gt=0)
    signal: str = Field(default="BUY")
    risk_percent: float = Field(default=0.5, gt=0, le=5.0)
    atr_multiplier: float = Field(default=1.5, gt=0)
    risk_reward_ratio: float = Field(default=2.0, ge=1.0)
    daily_loss_pct: float = Field(default=0.0, ge=0.0)
    drawdown_pct: float = Field(default=0.0, ge=0.0)
    daily_trades: int = Field(default=0, ge=0)
    consecutive_losses: int = Field(default=0, ge=0)


class AIPredictRequest(BaseModel):
    symbol: str = Field(default="XAUUSDc")
    timeframe: str = Field(default="M15")
    features: Optional[Dict[str, Any]] = None


class BacktestRunRequest(BaseModel):
    strategy_name: str = Field(default="StrategyA_TrendPullback")
    symbol: str = Field(default="XAUUSDc")
    timeframe: str = Field(default="M15")
    initial_balance: float = Field(default=10000.0, gt=0)
    account_type: str = Field(default="CENT")
    risk_percent: float = Field(default=0.5, gt=0, le=5.0)
    atr_multiplier: float = Field(default=1.5, gt=0)
    risk_reward_ratio: float = Field(default=2.0, ge=1.0)
    spread_points: float = Field(default=20.0, ge=0)
    commission_per_lot: float = Field(default=0.0, ge=0)
    slippage_points: float = Field(default=5.0, ge=0)
    bars: int = Field(default=300, ge=100, le=2000)


class SettingsUpdateRequest(BaseModel):
    settings: Dict[str, str]

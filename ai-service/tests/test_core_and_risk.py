import sys
from pathlib import Path

AI_DIR = Path(__file__).resolve().parent.parent
if str(AI_DIR) not in sys.path:
    sys.path.insert(0, str(AI_DIR))

from analysis.indicators import add_all_indicators  # noqa: E402
from connectors.mock_connector import MockMarketConnector  # noqa: E402
from core.exceptions import SafetyBlockError  # noqa: E402
from core.security import assert_execution_allowed  # noqa: E402
from risk.calculator import calculate_position_risk  # noqa: E402
from strategies.engine import evaluate_strategies  # noqa: E402
import pytest  # noqa: E402


def test_technical_indicators_computed():
    conn = MockMarketConnector()
    df = conn.get_candles("XAUUSDc", "M15", count=150)
    enriched = add_all_indicators(df)
    for col in ["ema_20", "ema_50", "ema_200", "rsi_14", "atr_14", "macd_main", "adx_14"]:
        assert col in enriched.columns
        assert enriched[col].notna().all()
    assert 0.0 <= float(enriched["rsi_14"].iloc[-1]) <= 100.0
    assert float(enriched["atr_14"].iloc[-1]) > 0.0


def test_strategy_signal_generation_structure():
    conn = MockMarketConnector()
    df_m15 = conn.get_candles("XAUUSDc", "M15", count=220)
    df_h1 = conn.get_candles("XAUUSDc", "H1", count=220)
    sig = evaluate_strategies(df_m15, df_h1)
    assert sig["signal"] in ("BUY", "SELL", "WAIT")
    assert 0 <= sig["score"] <= 100
    assert "strategy_name" in sig
    assert "market_regime" in sig


def test_cent_account_position_sizing_and_min_lot_rejection():
    # With 10,000 USC ($100), 0.5% risk = 50 USC. At SL dist 3.0 * 100 * 100 = 30,000 USC/lot -> 0.01 lot risks 300 USC > 50 USC
    rejected = calculate_position_risk(
        equity=10000.0,
        account_currency="USC",
        entry_price=2650.0,
        atr_14=2.0,
        risk_percent=0.5,
        atr_multiplier=1.5,
    )
    assert rejected["allowed"] is False
    assert "exceeds risk budget" in rejected["reason"]

    # With larger equity or tighter SL (e.g. 100,000 USC, 1% risk = 1000 USC, SL=1.0 -> 0.01 lot risks 100 USC)
    allowed = calculate_position_risk(
        equity=100000.0,
        account_currency="USC",
        entry_price=2650.0,
        atr_14=1.0,
        risk_percent=1.0,
        atr_multiplier=1.0,
    )
    assert allowed["allowed"] is True
    assert allowed["is_cent_account"] is True
    assert allowed["lot_size"] >= 0.01


def test_daily_loss_and_drawdown_protection():
    daily_blocked = calculate_position_risk(
        equity=100000.0,
        account_currency="USC",
        entry_price=2650.0,
        atr_14=1.0,
        daily_loss_pct=2.5,
        max_daily_loss_pct=2.0,
    )
    assert daily_blocked["allowed"] is False
    assert "Daily loss limit" in daily_blocked["reason"]

    dd_blocked = calculate_position_risk(
        equity=100000.0,
        account_currency="USC",
        entry_price=2650.0,
        atr_14=1.0,
        drawdown_pct=10.5,
        max_drawdown_pct=10.0,
    )
    assert dd_blocked["allowed"] is False
    assert "drawdown limit" in dd_blocked["reason"]


def test_real_account_execution_blocked():
    with pytest.raises(SafetyBlockError):
        assert_execution_allowed(operating_mode="DEMO", account_mode="REAL", allow_demo=True)

    with pytest.raises(SafetyBlockError):
        assert_execution_allowed(operating_mode="MONITORING", account_mode="DEMO", allow_demo=True)

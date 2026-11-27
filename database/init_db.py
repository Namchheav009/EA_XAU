"""Database initialization and clearly labeled development seed script."""

import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
AI_SERVICE_DIR = PROJECT_ROOT / "ai-service"
sys.path.insert(0, str(AI_SERVICE_DIR))

from repositories.database import SessionLocal, init_db  # noqa: E402
from repositories.models import (  # noqa: E402
    Account,
    EconomicEvent,
    Position,
    SettingRecord,
    Trade,
    TradingSession,
    TradingSignal,
)


def seed_database() -> None:
    init_db()
    db = SessionLocal()
    try:
        if db.query(Account).count() == 0:
            db.add(
                Account(
                    login=10000001,
                    broker="Exness",
                    server="Exness-MT5Trial-Mock",
                    account_type="CENT",
                    trade_mode="MOCK",
                    currency="USC",
                    balance=10000.0,
                    equity=10042.5,
                    is_mock=True,
                )
            )

        if db.query(TradingSession).count() == 0:
            db.add_all(
                [
                    TradingSession(name="ASIAN", start_hour_utc=0, end_hour_utc=8, enabled=False),
                    TradingSession(name="LONDON", start_hour_utc=7, end_hour_utc=16, enabled=True),
                    TradingSession(name="NEW_YORK", start_hour_utc=12, end_hour_utc=21, enabled=True),
                ]
            )

        now = datetime.now(timezone.utc)
        if db.query(EconomicEvent).count() == 0:
            db.add_all(
                [
                    EconomicEvent(
                        title="[MOCK] US Core CPI m/m",
                        currency="USD",
                        impact="HIGH",
                        event_time_utc=now + timedelta(hours=4),
                        forecast="0.3%",
                        previous="0.2%",
                        is_mock=True,
                    ),
                    EconomicEvent(
                        title="[MOCK] US Non-Farm Payrolls",
                        currency="USD",
                        impact="HIGH",
                        event_time_utc=now + timedelta(days=1, hours=2),
                        forecast="185K",
                        previous="172K",
                        is_mock=True,
                    ),
                    EconomicEvent(
                        title="[MOCK] FOMC Rate Decision",
                        currency="USD",
                        impact="HIGH",
                        event_time_utc=now + timedelta(days=2, hours=6),
                        forecast="4.50%",
                        previous="4.50%",
                        is_mock=True,
                    ),
                ]
            )

        if db.query(Trade).count() == 0:
            db.add_all(
                [
                    Trade(
                        ticket=9001,
                        symbol="XAUUSDc",
                        side="BUY",
                        strategy_name="StrategyA_TrendPullback",
                        volume=0.02,
                        entry_price=2645.50,
                        exit_price=2653.50,
                        stop_loss=2641.50,
                        take_profit=2653.50,
                        profit=16.00,
                        currency="USC",
                        commission=0.0,
                        slippage_cost=0.40,
                        is_mock=True,
                        opened_at_utc=now - timedelta(hours=18),
                        closed_at_utc=now - timedelta(hours=15),
                    ),
                    Trade(
                        ticket=9002,
                        symbol="XAUUSDc",
                        side="SELL",
                        strategy_name="StrategyB_Breakout",
                        volume=0.02,
                        entry_price=2658.00,
                        exit_price=2661.50,
                        stop_loss=2661.50,
                        take_profit=2651.00,
                        profit=-7.00,
                        currency="USC",
                        commission=0.0,
                        slippage_cost=0.30,
                        is_mock=True,
                        opened_at_utc=now - timedelta(hours=10),
                        closed_at_utc=now - timedelta(hours=8),
                    ),
                ]
            )

        if db.query(Position).count() == 0:
            db.add(
                Position(
                    ticket=9101,
                    symbol="XAUUSDc",
                    side="BUY",
                    volume=0.02,
                    entry_price=2654.20,
                    current_price=2656.32,
                    stop_loss=2649.80,
                    take_profit=2663.00,
                    floating_pnl=42.50,
                    currency="USC",
                    status="OPEN",
                    is_mock=True,
                    opened_at_utc=now - timedelta(minutes=45),
                )
            )

        if db.query(TradingSignal).count() == 0:
            db.add(
                TradingSignal(
                    symbol="XAUUSDc",
                    timeframe="M15",
                    signal="WAIT",
                    strategy_name="StrategyA_TrendPullback",
                    score=55,
                    regime="TRENDING_BULL",
                    ai_confirmed=False,
                    reasons="[MOCK SEED] H1 bullish trend; awaiting M15 pullback confirmation",
                    rejection_reason="Score 55 < min 65",
                    is_mock=True,
                )
            )

        if db.query(SettingRecord).count() == 0:
            defaults = {
                "symbol": "XAUUSDc",
                "account_type": "CENT",
                "data_mode": "MOCK",
                "operating_mode": "MONITORING",
                "risk_percent_per_trade": "0.5",
                "max_daily_loss_percent": "2.0",
                "max_drawdown_percent": "10.0",
            }
            for k, v in defaults.items():
                db.add(SettingRecord(key=k, value=v))

        db.commit()
        print("Database initialized and seeded with clearly labeled MOCK data.")
    finally:
        db.close()


if __name__ == "__main__":
    seed_database()

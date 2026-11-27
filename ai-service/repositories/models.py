from datetime import datetime, timezone
from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from repositories.database import Base


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Account(Base):
    __tablename__ = "accounts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    login: Mapped[int] = mapped_column(Integer, unique=True, nullable=False, index=True)
    broker: Mapped[str] = mapped_column(String(64), default="Exness")
    server: Mapped[str] = mapped_column(String(128), default="Exness-MT5Trial")
    account_type: Mapped[str] = mapped_column(String(16), default="CENT")  # CENT or STANDARD
    trade_mode: Mapped[str] = mapped_column(String(16), default="DEMO")    # MOCK, DEMO, REAL
    currency: Mapped[str] = mapped_column(String(8), default="USC")        # USC or USD
    balance: Mapped[float] = mapped_column(Float, default=10000.0)
    equity: Mapped[float] = mapped_column(Float, default=10000.0)
    is_mock: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at_utc: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at_utc: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    trades: Mapped[list["Trade"]] = relationship(back_populates="account")
    positions: Mapped[list["Position"]] = relationship(back_populates="account")


class MarketCandle(Base):
    __tablename__ = "market_candles"
    __table_args__ = (
        UniqueConstraint("symbol", "timeframe", "timestamp_utc", name="uq_candle_sym_tf_ts"),
        Index("ix_candle_lookup", "symbol", "timeframe", "timestamp_utc"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    symbol: Mapped[str] = mapped_column(String(32), nullable=False)
    timeframe: Mapped[str] = mapped_column(String(8), nullable=False)
    timestamp_utc: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    open: Mapped[float] = mapped_column(Float, nullable=False)
    high: Mapped[float] = mapped_column(Float, nullable=False)
    low: Mapped[float] = mapped_column(Float, nullable=False)
    close: Mapped[float] = mapped_column(Float, nullable=False)
    tick_volume: Mapped[int] = mapped_column(Integer, default=0)
    is_mock: Mapped[bool] = mapped_column(Boolean, default=True)


class TradingSignal(Base):
    __tablename__ = "trading_signals"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    symbol: Mapped[str] = mapped_column(String(32), index=True)
    timeframe: Mapped[str] = mapped_column(String(8), default="M15")
    signal: Mapped[str] = mapped_column(String(8), index=True)  # BUY, SELL, WAIT
    strategy_name: Mapped[str] = mapped_column(String(64))
    score: Mapped[int] = mapped_column(Integer, default=0)
    regime: Mapped[str] = mapped_column(String(32), default="RANGING")
    ai_confirmed: Mapped[bool] = mapped_column(Boolean, default=False)
    reasons: Mapped[str] = mapped_column(Text, default="")
    rejection_reason: Mapped[str] = mapped_column(Text, default="")
    is_mock: Mapped[bool] = mapped_column(Boolean, default=True)
    timestamp_utc: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, index=True)


class Trade(Base):
    __tablename__ = "trades"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    account_id: Mapped[int | None] = mapped_column(ForeignKey("accounts.id"), nullable=True)
    ticket: Mapped[int] = mapped_column(Integer, index=True)
    symbol: Mapped[str] = mapped_column(String(32), index=True)
    side: Mapped[str] = mapped_column(String(8))  # BUY or SELL
    strategy_name: Mapped[str] = mapped_column(String(64))
    volume: Mapped[float] = mapped_column(Float)
    entry_price: Mapped[float] = mapped_column(Float)
    exit_price: Mapped[float] = mapped_column(Float)
    stop_loss: Mapped[float] = mapped_column(Float)
    take_profit: Mapped[float] = mapped_column(Float)
    profit: Mapped[float] = mapped_column(Float)
    currency: Mapped[str] = mapped_column(String(8), default="USC")
    commission: Mapped[float] = mapped_column(Float, default=0.0)
    slippage_cost: Mapped[float] = mapped_column(Float, default=0.0)
    is_mock: Mapped[bool] = mapped_column(Boolean, default=True)
    opened_at_utc: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    closed_at_utc: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, index=True)

    account: Mapped["Account | None"] = relationship(back_populates="trades")


class Position(Base):
    __tablename__ = "positions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    account_id: Mapped[int | None] = mapped_column(ForeignKey("accounts.id"), nullable=True)
    ticket: Mapped[int] = mapped_column(Integer, unique=True, index=True)
    symbol: Mapped[str] = mapped_column(String(32))
    side: Mapped[str] = mapped_column(String(8))
    volume: Mapped[float] = mapped_column(Float)
    entry_price: Mapped[float] = mapped_column(Float)
    current_price: Mapped[float] = mapped_column(Float)
    stop_loss: Mapped[float] = mapped_column(Float)
    take_profit: Mapped[float] = mapped_column(Float)
    floating_pnl: Mapped[float] = mapped_column(Float, default=0.0)
    currency: Mapped[str] = mapped_column(String(8), default="USC")
    status: Mapped[str] = mapped_column(String(16), default="OPEN")
    is_mock: Mapped[bool] = mapped_column(Boolean, default=True)
    opened_at_utc: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    account: Mapped["Account | None"] = relationship(back_populates="positions")


class TradingSession(Base):
    __tablename__ = "trading_sessions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(32), unique=True)
    start_hour_utc: Mapped[int] = mapped_column(Integer)
    end_hour_utc: Mapped[int] = mapped_column(Integer)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)


class RiskEvent(Base):
    __tablename__ = "risk_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    event_type: Mapped[str] = mapped_column(String(64), index=True)
    severity: Mapped[str] = mapped_column(String(16), default="WARN")
    details: Mapped[str] = mapped_column(Text)
    currency: Mapped[str] = mapped_column(String(8), default="USC")
    value: Mapped[float] = mapped_column(Float, default=0.0)
    timestamp_utc: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, index=True)


class DailyPerformance(Base):
    __tablename__ = "daily_performance"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    date_utc: Mapped[str] = mapped_column(String(16), unique=True, index=True)
    starting_balance: Mapped[float] = mapped_column(Float)
    ending_balance: Mapped[float] = mapped_column(Float)
    net_pnl: Mapped[float] = mapped_column(Float)
    currency: Mapped[str] = mapped_column(String(8), default="USC")
    trades_count: Mapped[int] = mapped_column(Integer, default=0)
    win_count: Mapped[int] = mapped_column(Integer, default=0)
    max_drawdown_pct: Mapped[float] = mapped_column(Float, default=0.0)
    is_mock: Mapped[bool] = mapped_column(Boolean, default=True)


class EconomicEvent(Base):
    __tablename__ = "economic_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(128))
    currency: Mapped[str] = mapped_column(String(8), index=True)
    impact: Mapped[str] = mapped_column(String(16), index=True)  # HIGH, MEDIUM, LOW
    event_time_utc: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    forecast: Mapped[str] = mapped_column(String(32), default="")
    previous: Mapped[str] = mapped_column(String(32), default="")
    is_mock: Mapped[bool] = mapped_column(Boolean, default=True)


class AIModelRecord(Base):
    __tablename__ = "ai_models"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    model_name: Mapped[str] = mapped_column(String(64))
    version: Mapped[str] = mapped_column(String(32), unique=True, index=True)
    file_path: Mapped[str] = mapped_column(String(256))
    accuracy: Mapped[float] = mapped_column(Float, default=0.0)
    f1_macro: Mapped[float] = mapped_column(Float, default=0.0)
    brier_score: Mapped[float] = mapped_column(Float, default=0.0)
    is_active: Mapped[bool] = mapped_column(Boolean, default=False)
    trained_at_utc: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class AIPredictionRecord(Base):
    __tablename__ = "ai_predictions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    model_version: Mapped[str] = mapped_column(String(32), index=True)
    symbol: Mapped[str] = mapped_column(String(32))
    market_regime: Mapped[str] = mapped_column(String(32))
    buy_probability: Mapped[float] = mapped_column(Float)
    sell_probability: Mapped[float] = mapped_column(Float)
    wait_probability: Mapped[float] = mapped_column(Float)
    confidence: Mapped[float] = mapped_column(Float)
    reasons: Mapped[str] = mapped_column(Text, default="")
    feature_timestamp_utc: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    expires_at_utc: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class BacktestRun(Base):
    __tablename__ = "backtest_runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    strategy_name: Mapped[str] = mapped_column(String(64))
    symbol: Mapped[str] = mapped_column(String(32))
    timeframe: Mapped[str] = mapped_column(String(8))
    account_type: Mapped[str] = mapped_column(String(16), default="CENT")
    currency: Mapped[str] = mapped_column(String(8), default="USC")
    initial_balance: Mapped[float] = mapped_column(Float)
    final_balance: Mapped[float] = mapped_column(Float)
    net_profit: Mapped[float] = mapped_column(Float)
    total_return_pct: Mapped[float] = mapped_column(Float)
    win_rate_pct: Mapped[float] = mapped_column(Float)
    profit_factor: Mapped[float] = mapped_column(Float)
    max_drawdown_pct: Mapped[float] = mapped_column(Float)
    sharpe_ratio: Mapped[float] = mapped_column(Float)
    total_trades: Mapped[int] = mapped_column(Integer)
    metrics_json: Mapped[str] = mapped_column(Text, default="{}")
    created_at_utc: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    trades: Mapped[list["BacktestTrade"]] = relationship(back_populates="run", cascade="all, delete-orphan")


class BacktestTrade(Base):
    __tablename__ = "backtest_trades"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    run_id: Mapped[int] = mapped_column(ForeignKey("backtest_runs.id"), index=True)
    side: Mapped[str] = mapped_column(String(8))
    volume: Mapped[float] = mapped_column(Float)
    entry_price: Mapped[float] = mapped_column(Float)
    exit_price: Mapped[float] = mapped_column(Float)
    pnl: Mapped[float] = mapped_column(Float)
    exit_reason: Mapped[str] = mapped_column(String(32))
    opened_at_utc: Mapped[str] = mapped_column(String(32))
    closed_at_utc: Mapped[str] = mapped_column(String(32))

    run: Mapped["BacktestRun"] = relationship(back_populates="trades")


class SystemLog(Base):
    __tablename__ = "system_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    level: Mapped[str] = mapped_column(String(16), index=True)
    module: Mapped[str] = mapped_column(String(64))
    message: Mapped[str] = mapped_column(Text)
    timestamp_utc: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, index=True)


class SettingRecord(Base):
    __tablename__ = "settings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    key: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    value: Mapped[str] = mapped_column(Text)
    updated_at_utc: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

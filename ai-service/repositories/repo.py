from typing import List, Optional
from sqlalchemy.orm import Session
from repositories.models import (
    Account,
    AIModelRecord,
    AIPredictionRecord,
    BacktestRun,
    EconomicEvent,
    Position,
    RiskEvent,
    SettingRecord,
    SystemLog,
    Trade,
    TradingSignal,
)


class TradingRepository:
    """Data access layer for GoldAITrader SQLite persistence."""

    def __init__(self, db: Session):
        self.db = db

    def get_primary_account(self) -> Optional[Account]:
        return self.db.query(Account).order_by(Account.id.asc()).first()

    def get_recent_signals(self, limit: int = 25) -> List[TradingSignal]:
        return (
            self.db.query(TradingSignal)
            .order_by(TradingSignal.timestamp_utc.desc())
            .limit(limit)
            .all()
        )

    def save_signal(self, sig: TradingSignal) -> TradingSignal:
        self.db.add(sig)
        self.db.commit()
        self.db.refresh(sig)
        return sig

    def get_open_positions(self) -> List[Position]:
        return self.db.query(Position).filter(Position.status == "OPEN").all()

    def get_trades(
        self,
        side: Optional[str] = None,
        strategy: Optional[str] = None,
        outcome: Optional[str] = None,
        limit: int = 100,
    ) -> List[Trade]:
        q = self.db.query(Trade)
        if side:
            q = q.filter(Trade.side == side.upper())
        if strategy:
            q = q.filter(Trade.strategy_name == strategy)
        if outcome == "WIN":
            q = q.filter(Trade.profit > 0)
        elif outcome == "LOSS":
            q = q.filter(Trade.profit < 0)
        return q.order_by(Trade.closed_at_utc.desc()).limit(limit).all()

    def get_upcoming_news(self, limit: int = 20) -> List[EconomicEvent]:
        return (
            self.db.query(EconomicEvent)
            .order_by(EconomicEvent.event_time_utc.asc())
            .limit(limit)
            .all()
        )

    def get_risk_events(self, limit: int = 20) -> List[RiskEvent]:
        return (
            self.db.query(RiskEvent)
            .order_by(RiskEvent.timestamp_utc.desc())
            .limit(limit)
            .all()
        )

    def get_active_ai_model(self) -> Optional[AIModelRecord]:
        return (
            self.db.query(AIModelRecord)
            .filter(AIModelRecord.is_active.is_(True))
            .order_by(AIModelRecord.trained_at_utc.desc())
            .first()
        )

    def list_ai_models(self) -> List[AIModelRecord]:
        return self.db.query(AIModelRecord).order_by(AIModelRecord.trained_at_utc.desc()).all()

    def save_ai_prediction(self, pred: AIPredictionRecord) -> AIPredictionRecord:
        self.db.add(pred)
        self.db.commit()
        self.db.refresh(pred)
        return pred

    def list_backtest_runs(self, limit: int = 20) -> List[BacktestRun]:
        return self.db.query(BacktestRun).order_by(BacktestRun.created_at_utc.desc()).limit(limit).all()

    def get_backtest_run(self, run_id: int) -> Optional[BacktestRun]:
        return self.db.query(BacktestRun).filter(BacktestRun.id == run_id).first()

    def save_backtest_run(self, run: BacktestRun) -> BacktestRun:
        self.db.add(run)
        self.db.commit()
        self.db.refresh(run)
        return run

    def get_all_settings(self) -> dict[str, str]:
        rows = self.db.query(SettingRecord).all()
        return {r.key: r.value for r in rows}

    def upsert_setting(self, key: str, value: str) -> SettingRecord:
        row = self.db.query(SettingRecord).filter(SettingRecord.key == key).first()
        if row:
            row.value = value
        else:
            row = SettingRecord(key=key, value=value)
            self.db.add(row)
        self.db.commit()
        self.db.refresh(row)
        return row

    def add_log(self, level: str, module: str, message: str) -> None:
        self.db.add(SystemLog(level=level, module=module, message=message))
        self.db.commit()

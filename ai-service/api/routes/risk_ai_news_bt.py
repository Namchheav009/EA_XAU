import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from api.schemas.requests import AIPredictRequest, BacktestRunRequest, RiskCalculateRequest
from config import Settings, get_settings
from connectors.base import BaseMarketConnector
from connectors.factory import get_connector
from core.security import get_safety_state
from repositories.database import get_db
from repositories.models import BacktestRun, BacktestTrade
from repositories.repo import TradingRepository
from risk.calculator import calculate_position_risk
from services.ai_service import AIService

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backtesting.engine import run_backtest  # noqa: E402

router = APIRouter(prefix="/api/v1", tags=["risk", "ai", "news", "backtesting"])


@router.post("/risk/calculate")
def risk_calculate(payload: RiskCalculateRequest):
    return calculate_position_risk(
        equity=payload.equity,
        account_currency=payload.account_currency,
        entry_price=payload.entry_price,
        atr_14=payload.atr_14,
        signal=payload.signal,
        risk_percent=payload.risk_percent,
        atr_multiplier=payload.atr_multiplier,
        risk_reward_ratio=payload.risk_reward_ratio,
        daily_loss_pct=payload.daily_loss_pct,
        drawdown_pct=payload.drawdown_pct,
        daily_trades=payload.daily_trades,
        consecutive_losses=payload.consecutive_losses,
    )


@router.get("/risk/status")
def risk_status(cfg: Settings = Depends(get_settings), db: Session = Depends(get_db)):
    safety = get_safety_state()
    repo = TradingRepository(db)
    events = repo.get_risk_events(limit=10)
    return {
        "risk_percent_per_trade": cfg.risk_percent_per_trade,
        "max_daily_loss_percent": cfg.max_daily_loss_percent,
        "max_drawdown_percent": cfg.max_drawdown_percent,
        "max_daily_trades": cfg.max_daily_trades,
        "max_consecutive_losses": cfg.max_consecutive_losses,
        "emergency_stop": safety.emergency_stop,
        "emergency_reason": safety.emergency_reason,
        "recent_events": [
            {
                "id": e.id,
                "event_type": e.event_type,
                "severity": e.severity,
                "details": e.details,
                "timestamp_utc": e.timestamp_utc.isoformat(),
            }
            for e in events
        ],
    }


@router.get("/risk/drawdown")
def risk_drawdown(connector: BaseMarketConnector = Depends(get_connector)):
    acct = connector.get_account_info()
    bal = float(acct.get("balance", 10000.0))
    eq = float(acct.get("equity", bal))
    dd_pct = round(max(0.0, ((bal - eq) / bal) * 100.0), 2) if bal > 0 else 0.0
    return {
        "balance": bal,
        "equity": eq,
        "currency": acct.get("currency", "USC"),
        "current_drawdown_pct": dd_pct,
        "is_mock": acct.get("is_mock", True),
    }


@router.post("/ai/predict")
def ai_predict(
    payload: AIPredictRequest,
    connector: BaseMarketConnector = Depends(get_connector),
):
    df = connector.get_candles(payload.symbol, payload.timeframe, count=220)
    ai = AIService()
    return ai.predict(df, symbol=payload.symbol)


@router.get("/ai/status")
def ai_status():
    return AIService().get_status()


@router.get("/ai/metrics")
def ai_metrics(db: Session = Depends(get_db)):
    status = AIService().get_status()
    repo = TradingRepository(db)
    models = repo.list_ai_models()
    return {
        "active_model": status,
        "training_history": [
            {
                "version": m.version,
                "model_name": m.model_name,
                "accuracy": m.accuracy,
                "f1_macro": m.f1_macro,
                "brier_score": m.brier_score,
                "trained_at_utc": m.trained_at_utc.isoformat(),
            }
            for m in models
        ],
    }


@router.get("/news/upcoming")
def news_upcoming(db: Session = Depends(get_db)):
    repo = TradingRepository(db)
    events = repo.get_upcoming_news(limit=25)
    return {
        "count": len(events),
        "events": [
            {
                "id": e.id,
                "title": e.title,
                "currency": e.currency,
                "impact": e.impact,
                "event_time_utc": e.event_time_utc.isoformat(),
                "forecast": e.forecast,
                "previous": e.previous,
                "is_mock": e.is_mock,
            }
            for e in events
        ],
    }


@router.get("/news/status")
def news_status(before_min: int = Query(default=30), after_min: int = Query(default=30), db: Session = Depends(get_db)):
    repo = TradingRepository(db)
    events = repo.get_upcoming_news(limit=25)
    now = datetime.now(timezone.utc)
    active_blackout = None
    for e in events:
        if e.currency == "USD" and e.impact == "HIGH":
            evt_t = e.event_time_utc if e.event_time_utc.tzinfo else e.event_time_utc.replace(tzinfo=timezone.utc)
            diff_min = (evt_t - now).total_seconds() / 60.0
            if -after_min <= diff_min <= before_min:
                active_blackout = e.title
                break
    return {
        "in_blackout": active_blackout is not None,
        "active_event": active_blackout,
        "blackout_before_min": before_min,
        "blackout_after_min": after_min,
        "status_message": f"Blackout active: {active_blackout}" if active_blackout else "No USD high-impact news blackout active.",
    }


@router.post("/backtesting/run")
def backtesting_run(
    payload: BacktestRunRequest,
    connector: BaseMarketConnector = Depends(get_connector),
    db: Session = Depends(get_db),
):
    df = connector.get_candles(payload.symbol, payload.timeframe, count=payload.bars)
    result = run_backtest(
        df=df,
        strategy_name=payload.strategy_name,
        initial_balance=payload.initial_balance,
        account_type=payload.account_type,
        risk_percent=payload.risk_percent,
        atr_multiplier=payload.atr_multiplier,
        risk_reward_ratio=payload.risk_reward_ratio,
        spread_points=payload.spread_points,
        commission_per_lot=payload.commission_per_lot,
        slippage_points=payload.slippage_points,
    )

    run_row = BacktestRun(
        strategy_name=payload.strategy_name,
        symbol=payload.symbol,
        timeframe=payload.timeframe,
        account_type=payload.account_type,
        currency=result["currency"],
        initial_balance=result["initial_balance"],
        final_balance=result["final_balance"],
        net_profit=result["net_profit"],
        total_return_pct=result["total_return_pct"],
        win_rate_pct=result["win_rate_pct"],
        profit_factor=result["profit_factor"],
        max_drawdown_pct=result["max_drawdown_pct"],
        sharpe_ratio=result["sharpe_ratio"],
        total_trades=result["total_trades"],
        metrics_json=json.dumps({"equity_curve": result["equity_curve"], "limitations_note": result["limitations_note"]}),
    )
    for t in result["trades"]:
        run_row.trades.append(
            BacktestTrade(
                side=t["side"],
                volume=t["volume"],
                entry_price=t["entry_price"],
                exit_price=t["exit_price"],
                pnl=t["pnl"],
                exit_reason=t["exit_reason"],
                opened_at_utc=t["opened_at_utc"],
                closed_at_utc=t["closed_at_utc"],
            )
        )
    repo = TradingRepository(db)
    saved = repo.save_backtest_run(run_row)
    result["id"] = saved.id
    result["is_mock_data"] = connector.is_mock
    return result


@router.get("/backtesting/results")
def backtesting_results(db: Session = Depends(get_db)):
    repo = TradingRepository(db)
    runs = repo.list_backtest_runs()
    return {
        "runs": [
            {
                "id": r.id,
                "strategy_name": r.strategy_name,
                "symbol": r.symbol,
                "timeframe": r.timeframe,
                "account_type": r.account_type,
                "currency": r.currency,
                "initial_balance": r.initial_balance,
                "final_balance": r.final_balance,
                "net_profit": r.net_profit,
                "total_return_pct": r.total_return_pct,
                "win_rate_pct": r.win_rate_pct,
                "profit_factor": r.profit_factor,
                "max_drawdown_pct": r.max_drawdown_pct,
                "sharpe_ratio": r.sharpe_ratio,
                "total_trades": r.total_trades,
                "created_at_utc": r.created_at_utc.isoformat(),
            }
            for r in runs
        ]
    }


@router.get("/backtesting/results/{run_id}")
def backtesting_result_detail(run_id: int, db: Session = Depends(get_db)):
    repo = TradingRepository(db)
    r = repo.get_backtest_run(run_id)
    if r is None:
        raise HTTPException(status_code=404, detail="Backtest run not found.")
    extra = json.loads(r.metrics_json or "{}")
    return {
        "id": r.id,
        "strategy_name": r.strategy_name,
        "symbol": r.symbol,
        "timeframe": r.timeframe,
        "account_type": r.account_type,
        "currency": r.currency,
        "initial_balance": r.initial_balance,
        "final_balance": r.final_balance,
        "net_profit": r.net_profit,
        "total_return_pct": r.total_return_pct,
        "win_rate_pct": r.win_rate_pct,
        "profit_factor": r.profit_factor,
        "max_drawdown_pct": r.max_drawdown_pct,
        "sharpe_ratio": r.sharpe_ratio,
        "total_trades": r.total_trades,
        "equity_curve": extra.get("equity_curve", []),
        "limitations_note": extra.get("limitations_note", ""),
        "trades": [
            {
                "side": t.side,
                "volume": t.volume,
                "entry_price": t.entry_price,
                "exit_price": t.exit_price,
                "pnl": t.pnl,
                "exit_reason": t.exit_reason,
                "opened_at_utc": t.opened_at_utc,
                "closed_at_utc": t.closed_at_utc,
            }
            for t in r.trades
        ],
    }

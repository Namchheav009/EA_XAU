from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from analysis.indicators import add_all_indicators
from analysis.market_structure import detect_support_resistance
from analysis.trend_analysis import analyze_market
from connectors.base import BaseMarketConnector
from connectors.factory import get_connector
from repositories.database import get_db
from repositories.repo import TradingRepository
from strategies.engine import evaluate_strategies

router = APIRouter(prefix="/api/v1", tags=["market", "trading"])


@router.get("/market/price")
def market_price(
    symbol: str = Query(default="XAUUSDc"),
    connector: BaseMarketConnector = Depends(get_connector),
):
    return connector.get_price(symbol)


@router.get("/market/candles")
def market_candles(
    symbol: str = Query(default="XAUUSDc"),
    timeframe: str = Query(default="M15"),
    count: int = Query(default=200, ge=20, le=1000),
    connector: BaseMarketConnector = Depends(get_connector),
):
    df = connector.get_candles(symbol, timeframe, count=count)
    return {
        "symbol": symbol,
        "timeframe": timeframe,
        "is_mock": connector.is_mock,
        "candles": df.to_dict(orient="records"),
    }


@router.get("/market/indicators")
def market_indicators(
    symbol: str = Query(default="XAUUSDc"),
    timeframe: str = Query(default="M15"),
    connector: BaseMarketConnector = Depends(get_connector),
):
    df = connector.get_candles(symbol, timeframe, count=220)
    enriched = add_all_indicators(df)
    last = enriched.iloc[-1]
    return {
        "symbol": symbol,
        "timeframe": timeframe,
        "is_mock": connector.is_mock,
        "ema_20": round(float(last["ema_20"]), 2),
        "ema_50": round(float(last["ema_50"]), 2),
        "ema_200": round(float(last["ema_200"]), 2),
        "rsi_14": round(float(last["rsi_14"]), 2),
        "atr_14": round(float(last["atr_14"]), 3),
        "macd_main": round(float(last["macd_main"]), 4),
        "macd_signal": round(float(last["macd_signal"]), 4),
        "adx_14": round(float(last["adx_14"]), 2),
    }


@router.get("/market/trend")
def market_trend(
    symbol: str = Query(default="XAUUSDc"),
    connector: BaseMarketConnector = Depends(get_connector),
):
    df_m15 = connector.get_candles(symbol, "M15", count=220)
    df_h1 = connector.get_candles(symbol, "H1", count=220)
    res = analyze_market(df_m15, df_h1)
    return {
        "symbol": symbol,
        "is_mock": connector.is_mock,
        "trend_direction": res["trend_direction"],
        "market_regime": res["market_regime"],
        "h1_ema_50": res["h1_ema_50"],
        "h1_ema_200": res["h1_ema_200"],
        "adx_14": res["adx_14"],
    }


@router.get("/market/support-resistance")
def market_sr(
    symbol: str = Query(default="XAUUSDc"),
    timeframe: str = Query(default="M15"),
    connector: BaseMarketConnector = Depends(get_connector),
):
    df = connector.get_candles(symbol, timeframe, count=120)
    sr = detect_support_resistance(df)
    sr["symbol"] = symbol
    sr["timeframe"] = timeframe
    sr["is_mock"] = connector.is_mock
    return sr


@router.get("/market/analysis")
def market_analysis(
    symbol: str = Query(default="XAUUSDc"),
    timeframe: str = Query(default="M15"),
    connector: BaseMarketConnector = Depends(get_connector),
):
    df_entry = connector.get_candles(symbol, timeframe, count=220)
    df_h1 = connector.get_candles(symbol, "H1", count=220)
    sig = evaluate_strategies(df_entry, df_h1)
    sig["symbol"] = symbol
    sig["is_mock"] = connector.is_mock
    return sig


@router.get("/trading/signals")
def trading_signals(
    symbol: str = Query(default="XAUUSDc"),
    connector: BaseMarketConnector = Depends(get_connector),
    db: Session = Depends(get_db),
):
    df_entry = connector.get_candles(symbol, "M15", count=220)
    df_h1 = connector.get_candles(symbol, "H1", count=220)
    live_sig = evaluate_strategies(df_entry, df_h1)
    repo = TradingRepository(db)
    stored = repo.get_recent_signals(limit=20)
    return {
        "current_signal": live_sig,
        "history": [
            {
                "id": s.id,
                "symbol": s.symbol,
                "timeframe": s.timeframe,
                "signal": s.signal,
                "strategy_name": s.strategy_name,
                "score": s.score,
                "regime": s.regime,
                "ai_confirmed": s.ai_confirmed,
                "reasons": s.reasons,
                "rejection_reason": s.rejection_reason,
                "is_mock": s.is_mock,
                "timestamp_utc": s.timestamp_utc.isoformat(),
            }
            for s in stored
        ],
    }


@router.get("/trading/positions")
def trading_positions(db: Session = Depends(get_db)):
    repo = TradingRepository(db)
    positions = repo.get_open_positions()
    return {
        "count": len(positions),
        "positions": [
            {
                "id": p.id,
                "ticket": p.ticket,
                "symbol": p.symbol,
                "side": p.side,
                "volume": p.volume,
                "entry_price": p.entry_price,
                "current_price": p.current_price,
                "stop_loss": p.stop_loss,
                "take_profit": p.take_profit,
                "floating_pnl": p.floating_pnl,
                "currency": p.currency,
                "status": p.status,
                "is_mock": p.is_mock,
                "opened_at_utc": p.opened_at_utc.isoformat(),
            }
            for p in positions
        ],
    }


@router.get("/trading/history")
def trading_history(
    side: str | None = Query(default=None),
    strategy: str | None = Query(default=None),
    outcome: str | None = Query(default=None),
    db: Session = Depends(get_db),
):
    repo = TradingRepository(db)
    trades = repo.get_trades(side=side, strategy=strategy, outcome=outcome)
    return {
        "count": len(trades),
        "trades": [
            {
                "id": t.id,
                "ticket": t.ticket,
                "symbol": t.symbol,
                "side": t.side,
                "strategy_name": t.strategy_name,
                "volume": t.volume,
                "entry_price": t.entry_price,
                "exit_price": t.exit_price,
                "stop_loss": t.stop_loss,
                "take_profit": t.take_profit,
                "profit": t.profit,
                "currency": t.currency,
                "is_mock": t.is_mock,
                "opened_at_utc": t.opened_at_utc.isoformat(),
                "closed_at_utc": t.closed_at_utc.isoformat(),
            }
            for t in trades
        ],
    }


@router.get("/trading/performance")
def trading_performance(db: Session = Depends(get_db)):
    repo = TradingRepository(db)
    trades = repo.get_trades(limit=500)
    wins = [t.profit for t in trades if t.profit > 0]
    losses = [t.profit for t in trades if t.profit < 0]
    gross_profit = round(sum(wins), 2)
    gross_loss = round(abs(sum(losses)), 2)
    total = len(trades)
    return {
        "total_trades": total,
        "win_rate_pct": round((len(wins) / total) * 100.0, 2) if total > 0 else 0.0,
        "profit_factor": round(gross_profit / gross_loss, 2) if gross_loss > 0 else (99.0 if gross_profit > 0 else 0.0),
        "net_pnl": round(sum(t.profit for t in trades), 2),
        "gross_profit": gross_profit,
        "gross_loss": gross_loss,
        "currency": trades[0].currency if trades else "USC",
        "is_mock": all(t.is_mock for t in trades) if trades else True,
    }

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from api.schemas.requests import SettingsUpdateRequest
from config import Settings, get_settings
from connectors.base import BaseMarketConnector
from connectors.factory import get_connector
from core.security import get_safety_state
from repositories.database import get_db
from repositories.repo import TradingRepository

router = APIRouter()


@router.get("/")
def home(cfg: Settings = Depends(get_settings)):
    return {
        "project": "Gold AI Trader",
        "status": "running",
        "broker": cfg.broker_name,
        "platform": "MT5",
        "symbol": cfg.default_symbol,
        "data_mode": cfg.data_mode,
        "operating_mode": cfg.operating_mode,
        "trading_enabled": False,
    }


@router.get("/health")
def health():
    return {"status": "healthy"}


@router.get("/mt5/status")
def legacy_mt5_status(connector: BaseMarketConnector = Depends(get_connector)):
    return connector.get_status()


@router.get("/api/v1/system/status")
def system_status(
    cfg: Settings = Depends(get_settings),
    connector: BaseMarketConnector = Depends(get_connector),
):
    safety = get_safety_state()
    return {
        "project": cfg.project_name,
        "version": cfg.version,
        "data_mode": cfg.data_mode,
        "operating_mode": cfg.operating_mode,
        "allow_demo_trading": cfg.allow_demo_trading,
        "emergency_stop": safety.emergency_stop,
        "emergency_reason": safety.emergency_reason,
        "connector": connector.get_status(),
    }


@router.get("/api/v1/system/config")
def system_config(cfg: Settings = Depends(get_settings), db: Session = Depends(get_db)):
    repo = TradingRepository(db)
    return {
        "default_symbol": cfg.default_symbol,
        "account_type": cfg.account_type,
        "account_currency": cfg.account_currency,
        "initial_capital": cfg.initial_capital,
        "data_mode": cfg.data_mode,
        "operating_mode": cfg.operating_mode,
        "risk": {
            "risk_percent_per_trade": cfg.risk_percent_per_trade,
            "max_daily_loss_percent": cfg.max_daily_loss_percent,
            "max_drawdown_percent": cfg.max_drawdown_percent,
            "max_daily_trades": cfg.max_daily_trades,
            "max_simultaneous_positions": cfg.max_simultaneous_positions,
            "risk_reward_ratio": cfg.risk_reward_ratio,
            "max_consecutive_losses": cfg.max_consecutive_losses,
        },
        "persisted_settings": repo.get_all_settings(),
    }


@router.put("/api/v1/system/config")
def update_system_config(payload: SettingsUpdateRequest, db: Session = Depends(get_db)):
    repo = TradingRepository(db)
    for k, v in payload.settings.items():
        repo.upsert_setting(k, str(v))
    return {"updated": True, "settings": repo.get_all_settings()}


@router.post("/api/v1/system/emergency-stop")
def toggle_emergency_stop(active: bool = Query(...), reason: str = Query(default="Manual trigger")):
    safety = get_safety_state()
    safety.emergency_stop = active
    safety.emergency_reason = reason if active else ""
    return {"emergency_stop": safety.emergency_stop, "reason": safety.emergency_reason}


@router.get("/api/v1/mt5/status")
def v1_mt5_status(connector: BaseMarketConnector = Depends(get_connector)):
    return connector.get_status()


@router.get("/api/v1/mt5/account")
def v1_mt5_account(connector: BaseMarketConnector = Depends(get_connector)):
    return connector.get_account_info()


@router.get("/api/v1/mt5/symbols")
def v1_mt5_symbols(connector: BaseMarketConnector = Depends(get_connector)):
    return {"symbols": connector.get_symbols(), "is_mock": connector.is_mock}


@router.get("/api/v1/mt5/symbol-info")
def v1_mt5_symbol_info(
    symbol: str = Query(default="XAUUSDc"),
    connector: BaseMarketConnector = Depends(get_connector),
):
    return connector.get_symbol_info(symbol)

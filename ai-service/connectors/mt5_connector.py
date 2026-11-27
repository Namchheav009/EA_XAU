from datetime import datetime, timezone
from typing import Any, Dict, List
import pandas as pd
import MetaTrader5 as mt5
from connectors.base import BaseMarketConnector
from core.exceptions import ConnectorUnavailableError


MT5_TF_MAP = {
    "M5": mt5.TIMEFRAME_M5,
    "M15": mt5.TIMEFRAME_M15,
    "M30": mt5.TIMEFRAME_M30,
    "H1": mt5.TIMEFRAME_H1,
    "H4": mt5.TIMEFRAME_H4,
}


class MT5MarketConnector(BaseMarketConnector):
    """Live MetaTrader 5 desktop terminal connector."""

    def __init__(self, terminal_path: str = ""):
        self.terminal_path = terminal_path

    @property
    def is_mock(self) -> bool:
        return False

    def _init_mt5(self) -> bool:
        if self.terminal_path:
            return bool(mt5.initialize(self.terminal_path))
        return bool(mt5.initialize())

    def get_status(self) -> Dict[str, Any]:
        if not self._init_mt5():
            return {
                "connected": False,
                "is_mock": False,
                "mode": "MT5",
                "error": list(mt5.last_error()),
            }
        info = mt5.account_info()
        mt5.shutdown()
        return {
            "connected": True,
            "is_mock": False,
            "mode": "MT5",
            "account": info._asdict() if info else None,
        }

    def get_account_info(self) -> Dict[str, Any]:
        if not self._init_mt5():
            raise ConnectorUnavailableError(f"MT5 unavailable: {mt5.last_error()}")
        info = mt5.account_info()
        mt5.shutdown()
        if info is None:
            raise ConnectorUnavailableError("MT5 account_info returned None.")
        d = info._asdict()
        d["is_mock"] = False
        d["trade_mode"] = "DEMO" if info.trade_mode == mt5.ACCOUNT_TRADE_MODE_DEMO else "REAL"
        d["account_type"] = "CENT" if str(info.currency).upper() == "USC" else "STANDARD"
        return d

    def get_symbols(self) -> List[str]:
        if not self._init_mt5():
            raise ConnectorUnavailableError(f"MT5 unavailable: {mt5.last_error()}")
        syms = [s.name for s in (mt5.symbols_get() or []) if "XAU" in s.name or "GOLD" in s.name]
        mt5.shutdown()
        return syms

    def get_symbol_info(self, symbol: str) -> Dict[str, Any]:
        if not self._init_mt5():
            raise ConnectorUnavailableError(f"MT5 unavailable: {mt5.last_error()}")
        info = mt5.symbol_info(symbol)
        mt5.shutdown()
        if info is None:
            raise ConnectorUnavailableError(f"Symbol {symbol} not found in MT5.")
        return {
            "symbol": info.name,
            "digits": info.digits,
            "point": info.point,
            "contract_size": info.trade_contract_size,
            "volume_min": info.volume_min,
            "volume_max": info.volume_max,
            "volume_step": info.volume_step,
            "spread": info.spread,
            "currency_profit": info.currency_profit,
            "is_cent_symbol": info.name.endswith("c"),
            "is_mock": False,
        }

    def get_price(self, symbol: str) -> Dict[str, Any]:
        if not self._init_mt5():
            raise ConnectorUnavailableError(f"MT5 unavailable: {mt5.last_error()}")
        tick = mt5.symbol_info_tick(symbol)
        mt5.shutdown()
        if tick is None:
            raise ConnectorUnavailableError(f"Failed to read tick for {symbol}.")
        return {
            "symbol": symbol,
            "bid": tick.bid,
            "ask": tick.ask,
            "spread_points": round((tick.ask - tick.bid) / 0.01),
            "timestamp_utc": datetime.fromtimestamp(tick.time, tz=timezone.utc).isoformat(),
            "is_mock": False,
        }

    def get_candles(self, symbol: str, timeframe: str = "M15", count: int = 200) -> pd.DataFrame:
        if not self._init_mt5():
            raise ConnectorUnavailableError(f"MT5 unavailable: {mt5.last_error()}")
        tf = MT5_TF_MAP.get(timeframe.upper(), mt5.TIMEFRAME_M15)
        rates = mt5.copy_rates_from_pos(symbol, tf, 0, count)
        mt5.shutdown()
        if rates is None or len(rates) == 0:
            raise ConnectorUnavailableError(f"No candles returned for {symbol} {timeframe}.")
        df = pd.DataFrame(rates)
        df["timestamp"] = pd.to_datetime(df["time"], unit="s", utc=True).dt.strftime("%Y-%m-%dT%H:%M:%SZ")
        df["is_mock"] = False
        return df[["timestamp", "open", "high", "low", "close", "tick_volume", "is_mock"]]

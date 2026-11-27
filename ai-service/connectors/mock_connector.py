from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List
import numpy as np
import pandas as pd
from connectors.base import BaseMarketConnector


TIMEFRAME_MINUTES = {
    "M5": 5,
    "M15": 15,
    "M30": 30,
    "H1": 60,
    "H4": 240,
}


class MockMarketConnector(BaseMarketConnector):
    """Deterministic mock data connector for development without MT5."""

    def __init__(self, initial_capital: float = 10000.0, currency: str = "USC"):
        self.initial_capital = initial_capital
        self.currency = currency

    @property
    def is_mock(self) -> bool:
        return True

    def get_status(self) -> Dict[str, Any]:
        return {
            "connected": True,
            "is_mock": True,
            "mode": "MOCK",
            "message": "Running with clearly labeled MOCK development data (MT5 not required).",
            "terminal_found": False,
        }

    def get_account_info(self) -> Dict[str, Any]:
        return {
            "login": 10000001,
            "broker": "Exness",
            "server": "Exness-MT5Trial-Mock",
            "account_type": "CENT",
            "trade_mode": "DEMO",
            "currency": self.currency,
            "balance": self.initial_capital,
            "equity": round(self.initial_capital + 42.50, 2),
            "margin": 120.0,
            "margin_free": round(self.initial_capital - 77.50, 2),
            "leverage": 2000,
            "is_mock": True,
        }

    def get_symbols(self) -> List[str]:
        return ["XAUUSDc", "XAUUSD", "XAUUSDm"]

    def get_symbol_info(self, symbol: str) -> Dict[str, Any]:
        return {
            "symbol": symbol,
            "digits": 2,
            "point": 0.01,
            "contract_size": 100.0,
            "volume_min": 0.01,
            "volume_max": 100.0,
            "volume_step": 0.01,
            "spread": 20,
            "currency_profit": "USD",
            "is_cent_symbol": symbol.endswith("c"),
            "is_mock": True,
        }

    def get_price(self, symbol: str) -> Dict[str, Any]:
        df = self.get_candles(symbol, "M15", count=5)
        last_close = float(df["close"].iloc[-1])
        return {
            "symbol": symbol,
            "bid": round(last_close, 2),
            "ask": round(last_close + 0.20, 2),
            "spread_points": 20,
            "timestamp_utc": datetime.now(timezone.utc).isoformat(),
            "is_mock": True,
        }

    def get_candles(self, symbol: str, timeframe: str = "M15", count: int = 200) -> pd.DataFrame:
        tf_min = TIMEFRAME_MINUTES.get(timeframe.upper(), 15)
        now = datetime.now(timezone.utc).replace(second=0, microsecond=0)
        aligned = now - timedelta(minutes=now.minute % tf_min)
        timestamps = [aligned - timedelta(minutes=tf_min * i) for i in range(count - 1, -1, -1)]

        rng = np.random.default_rng(seed=42 + tf_min)
        base_price = 2640.0
        trend = np.linspace(0.0, 22.0, count)
        wave = 6.0 * np.sin(np.linspace(0, 6 * np.pi, count))
        noise = rng.normal(0.0, 1.4, size=count)
        closes = base_price + trend + wave + noise

        opens = np.roll(closes, 1)
        opens[0] = closes[0] - 0.8
        spread_hi = np.abs(rng.normal(1.6, 0.7, size=count))
        spread_lo = np.abs(rng.normal(1.5, 0.7, size=count))
        highs = np.maximum(opens, closes) + spread_hi
        lows = np.minimum(opens, closes) - spread_lo
        volumes = rng.integers(150, 950, size=count)

        return pd.DataFrame(
            {
                "timestamp": [ts.isoformat() for ts in timestamps],
                "open": np.round(opens, 2),
                "high": np.round(highs, 2),
                "low": np.round(lows, 2),
                "close": np.round(closes, 2),
                "tick_volume": volumes.astype(int),
                "is_mock": True,
            }
        )

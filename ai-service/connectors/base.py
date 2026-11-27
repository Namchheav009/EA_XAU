from abc import ABC, abstractmethod
from typing import Any, Dict, List
import pandas as pd


class BaseMarketConnector(ABC):
    """Abstract interface for MT5 and Mock market data connectors."""

    @property
    @abstractmethod
    def is_mock(self) -> bool:
        pass

    @abstractmethod
    def get_status(self) -> Dict[str, Any]:
        pass

    @abstractmethod
    def get_account_info(self) -> Dict[str, Any]:
        pass

    @abstractmethod
    def get_symbols(self) -> List[str]:
        pass

    @abstractmethod
    def get_symbol_info(self, symbol: str) -> Dict[str, Any]:
        pass

    @abstractmethod
    def get_price(self, symbol: str) -> Dict[str, Any]:
        pass

    @abstractmethod
    def get_candles(self, symbol: str, timeframe: str, count: int = 200) -> pd.DataFrame:
        pass

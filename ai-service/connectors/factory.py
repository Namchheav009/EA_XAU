from config import Settings, get_settings
from connectors.base import BaseMarketConnector
from connectors.mock_connector import MockMarketConnector
from connectors.mt5_connector import MT5MarketConnector


def get_connector(settings: Settings | None = None) -> BaseMarketConnector:
    cfg = settings or get_settings()
    if cfg.data_mode.upper() == "MT5":
        return MT5MarketConnector(terminal_path=cfg.mt5_terminal_path)
    return MockMarketConnector(initial_capital=cfg.initial_capital, currency=cfg.account_currency)

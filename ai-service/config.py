from functools import lru_cache
from pathlib import Path
from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict


BASE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BASE_DIR.parent
DEFAULT_DB_PATH = (PROJECT_ROOT / "database" / "goldaitrader.db").resolve()


class Settings(BaseSettings):
    """Centralized configuration loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=str(BASE_DIR / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    project_name: str = "Gold AI Trader API"
    version: str = "1.0.0"

    data_mode: str = "MOCK"  # MOCK or MT5
    operating_mode: str = "MONITORING"  # MONITORING or DEMO
    allow_demo_trading: bool = False

    host: str = "127.0.0.1"
    port: int = 8000
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"

    database_url: str = f"sqlite:///{DEFAULT_DB_PATH.as_posix()}"

    broker_name: str = "Exness"
    account_type: str = "CENT"
    account_currency: str = "USC"
    initial_capital: float = 10000.0
    default_symbol: str = "XAUUSDc"
    mt5_terminal_path: str = ""

    risk_percent_per_trade: float = 0.5
    max_daily_loss_percent: float = 2.0
    max_drawdown_percent: float = 10.0
    max_daily_trades: int = 3
    max_simultaneous_positions: int = 1
    risk_reward_ratio: float = 2.0
    max_consecutive_losses: int = 3

    ai_model_dir: str = str((BASE_DIR / "models").resolve())
    ai_min_confidence: float = 0.55
    ai_prediction_ttl_seconds: int = 900

    @property
    def cors_origin_list(self) -> List[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()

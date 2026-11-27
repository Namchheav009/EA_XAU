from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routes.market_trading import router as market_trading_router
from api.routes.risk_ai_news_bt import router as risk_ai_news_bt_router
from api.routes.system_mt5 import router as system_mt5_router
from config import get_settings
from core.logging import get_logger
from repositories.database import init_db

logger = get_logger("main")


@asynccontextmanager
async def lifespan(_: FastAPI):
    init_db()
    logger.info("GoldAITrader backend initialized (database ready).")
    yield


def create_app() -> FastAPI:
    cfg = get_settings()
    application = FastAPI(
        title=cfg.project_name,
        description="Automated Gold Trading System (Monitoring & Demo Testing Default)",
        version=cfg.version,
        lifespan=lifespan,
    )

    application.add_middleware(
        CORSMiddleware,
        allow_origins=cfg.cors_origin_list,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT"],
        allow_headers=["*"],
    )

    application.include_router(system_mt5_router)
    application.include_router(market_trading_router)
    application.include_router(risk_ai_news_bt_router)
    return application


app = create_app()

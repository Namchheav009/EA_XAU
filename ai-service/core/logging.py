import logging
import sys
from typing import Optional


def setup_logging(level: int = logging.INFO) -> logging.Logger:
    logger = logging.getLogger("goldaitrader")
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter(
            "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
            datefmt="%Y-%m-%dT%H:%M:%SZ",
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    logger.setLevel(level)
    return logger


def get_logger(name: Optional[str] = None) -> logging.Logger:
    setup_logging()
    return logging.getLogger(f"goldaitrader.{name}" if name else "goldaitrader")

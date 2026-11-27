from fastapi import HTTPException, status


class GoldAITraderError(Exception):
    """Base domain exception."""


class ConnectorUnavailableError(GoldAITraderError):
    """Raised when MT5 or market data connector is unavailable."""


class SafetyBlockError(HTTPException):
    """Raised when an operation violates trading safety rules."""

    def __init__(self, detail: str):
        super().__init__(status_code=status.HTTP_403_FORBIDDEN, detail=detail)

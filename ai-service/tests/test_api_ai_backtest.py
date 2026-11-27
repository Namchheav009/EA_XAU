import sys
from pathlib import Path
from fastapi.testclient import TestClient

AI_DIR = Path(__file__).resolve().parent.parent
ROOT_DIR = AI_DIR.parent
for p in (AI_DIR, ROOT_DIR):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

from backtesting.engine import run_backtest  # noqa: E402
from connectors.mock_connector import MockMarketConnector  # noqa: E402
from main import app  # noqa: E402
from services.ai_service import AIService  # noqa: E402
from training.features import build_feature_matrix  # noqa: E402

client = TestClient(app)


def test_ai_features_and_missing_model_returns_wait(tmp_path):
    conn = MockMarketConnector()
    df = conn.get_candles("XAUUSDc", "M15", count=100)
    feats = build_feature_matrix(df)
    assert len(feats) == 100
    assert not feats.isna().any().any()

    ai = AIService(model_dir=str(tmp_path))
    pred = ai.predict(df)
    assert pred["model_available"] is False
    assert pred["recommended_signal"] == "WAIT"
    assert pred["wait_probability"] == 1.0


def test_backtest_engine_conservative_and_metrics():
    conn = MockMarketConnector()
    df = conn.get_candles("XAUUSDc", "M15", count=250)
    res = run_backtest(
        df=df,
        initial_balance=100000.0,
        account_type="CENT",
        risk_percent=1.0,
        spread_points=20.0,
        commission_per_lot=0.5,
        slippage_points=5.0,
    )
    assert res["currency"] == "USC"
    assert "max_drawdown_pct" in res
    assert "sharpe_ratio" in res
    assert "limitations_note" in res


def test_api_endpoints_and_mock_data():
    assert client.get("/").status_code == 200
    assert client.get("/health").status_code == 200
    assert client.get("/mt5/status").status_code == 200

    acct = client.get("/api/v1/mt5/account")
    assert acct.status_code == 200
    assert acct.json()["is_mock"] is True

    candles = client.get("/api/v1/market/candles?symbol=XAUUSDc&timeframe=M15&count=50")
    assert candles.status_code == 200
    assert len(candles.json()["candles"]) == 50

    risk_resp = client.post(
        "/api/v1/risk/calculate",
        json={"equity": 100000.0, "account_currency": "USC", "entry_price": 2650.0, "atr_14": 1.0},
    )
    assert risk_resp.status_code == 200
    assert risk_resp.json()["is_cent_account"] is True

    news_resp = client.get("/api/v1/news/status")
    assert news_resp.status_code == 200
    assert "in_blackout" in news_resp.json()

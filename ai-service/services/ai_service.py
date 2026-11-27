from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, Optional
import joblib
import numpy as np
import pandas as pd

from config import get_settings
from training.features import FEATURE_COLUMNS, build_feature_matrix


class AIService:
    """Loads versioned joblib models, monitors drift, and produces calibrated predictions."""

    def __init__(self, model_dir: str | None = None):
        cfg = get_settings()
        self.model_dir = Path(model_dir or cfg.ai_model_dir)
        self.ttl_seconds = cfg.ai_prediction_ttl_seconds

    def _latest_artifact_path(self) -> Optional[Path]:
        if not self.model_dir.exists():
            return None
        files = sorted(self.model_dir.glob("gold_ai_*.joblib"), key=lambda p: p.stat().st_mtime, reverse=True)
        return files[0] if files else None

    def get_status(self) -> Dict[str, Any]:
        path = self._latest_artifact_path()
        if path is None:
            return {
                "model_available": False,
                "status": "unavailable",
                "model_version": None,
                "model_name": None,
                "message": "No trained model artifact found. AI filter will return WAIT when required.",
            }
        try:
            art = joblib.load(path)
            return {
                "model_available": True,
                "status": "available",
                "model_version": art.get("version"),
                "model_name": art.get("model_name"),
                "trained_at_utc": art.get("trained_at_utc"),
                "metrics": art.get("metrics", {}),
                "feature_importance": art.get("feature_importance", {}),
                "artifact_path": str(path),
            }
        except Exception as exc:
            return {
                "model_available": False,
                "status": "invalid",
                "message": f"Failed to load model artifact: {exc}",
            }

    def predict(
        self,
        df: pd.DataFrame,
        market_regime: str = "RANGING",
        symbol: str = "XAUUSDc",
    ) -> Dict[str, Any]:
        now = datetime.now(timezone.utc)
        expires = now + timedelta(seconds=self.ttl_seconds)
        path = self._latest_artifact_path()

        if path is None:
            return {
                "model_available": False,
                "status": "unavailable",
                "model_version": "unavailable",
                "symbol": symbol,
                "market_regime": market_regime,
                "recommended_signal": "WAIT",
                "buy_probability": 0.0,
                "sell_probability": 0.0,
                "wait_probability": 1.0,
                "confidence": 0.0,
                "feature_timestamp_utc": now.isoformat(),
                "prediction_expiration_utc": expires.isoformat(),
                "drift_detected": False,
                "reasons": ["No trained AI model available; returning fail-safe WAIT."],
            }

        art = joblib.load(path)
        model = art["model"]
        feat_df = build_feature_matrix(df)
        latest = feat_df[FEATURE_COLUMNS].iloc[[-1]]

        # Drift check (z-score > 4.0 on any feature vs training distribution)
        means = art.get("feature_means", {})
        stds = art.get("feature_stds", {})
        drift_features = []
        for col in FEATURE_COLUMNS:
            m = means.get(col, 0.0)
            s = stds.get(col, 1.0) or 1.0
            z = abs(float(latest[col].iloc[0]) - m) / s
            if z > 4.0:
                drift_features.append(col)

        probs = model.predict_proba(latest)[0]
        classes = list(model.classes_)
        prob_map = {int(c): float(p) for c, p in zip(classes, probs)}
        wait_p = round(prob_map.get(0, 0.0), 4)
        buy_p = round(prob_map.get(1, 0.0), 4)
        sell_p = round(prob_map.get(2, 0.0), 4)

        best_class = max(prob_map, key=prob_map.get) if prob_map else 0
        rec = {0: "WAIT", 1: "BUY", 2: "SELL"}.get(best_class, "WAIT")
        conf = round(max(buy_p, sell_p, wait_p), 4)

        reasons = [
            f"Model {art.get('model_name')} ({art.get('version')}) evaluated {len(FEATURE_COLUMNS)} features.",
            f"Regime={market_regime}, Probabilities BUY={buy_p}, SELL={sell_p}, WAIT={wait_p}.",
        ]
        if drift_features:
            reasons.append(f"Feature drift detected on: {', '.join(drift_features)}")

        return {
            "model_available": True,
            "status": "available",
            "model_version": art.get("version", "unknown"),
            "symbol": symbol,
            "market_regime": market_regime,
            "recommended_signal": rec,
            "buy_probability": buy_p,
            "sell_probability": sell_p,
            "wait_probability": wait_p,
            "confidence": conf,
            "feature_timestamp_utc": now.isoformat(),
            "prediction_expiration_utc": expires.isoformat(),
            "drift_detected": len(drift_features) > 0,
            "reasons": reasons,
        }

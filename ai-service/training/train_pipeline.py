from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict
import joblib
import numpy as np
import pandas as pd
from sklearn.calibration import CalibratedClassifierCV
from sklearn.ensemble import GradientBoostingClassifier, RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, brier_score_loss, f1_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from training.features import FEATURE_COLUMNS, build_feature_matrix, chronological_split, create_labels


def train_and_evaluate(
    df: pd.DataFrame,
    model_dir: str,
    version: str | None = None,
) -> Dict[str, Any]:
    """Train LR, RF, and GB models with chronological split and save best artifact."""
    X = build_feature_matrix(df)
    y = create_labels(df, horizon=4, tx_cost_pct=0.0005)

    # Drop trailing horizon rows where future return is unknown
    valid_mask = df.index[:-4]
    X = X.loc[valid_mask]
    y = y.loc[valid_mask]

    X_train, X_val, X_test, y_train, y_val, y_test = chronological_split(X, y)
    if len(X_train) < 30 or len(X_test) < 10 or y_train.nunique() < 2:
        raise ValueError("Insufficient data or class diversity for chronological training.")

    candidates = {
        "logistic_regression": Pipeline(
            [("scaler", StandardScaler()), ("clf", LogisticRegression(max_iter=500, random_state=42))]
        ),
        "random_forest": RandomForestClassifier(n_estimators=120, max_depth=6, random_state=42),
        "gradient_boosting": GradientBoostingClassifier(n_estimators=100, max_depth=3, random_state=42),
    }

    results: Dict[str, Dict[str, Any]] = {}
    best_name = ""
    best_f1 = -1.0
    best_model = None

    for name, base_est in candidates.items():
        # Calibrate probabilities when enough samples exist
        if y_train.value_counts().min() >= 3:
            model = CalibratedClassifierCV(base_est, cv=3, method="sigmoid")
        else:
            model = base_est
        model.fit(X_train, y_train)
        preds = model.predict(X_test)
        acc = float(accuracy_score(y_test, preds))
        f1 = float(f1_score(y_test, preds, average="macro", zero_division=0))

        probs = model.predict_proba(X_test)
        # Multi-class Brier proxy on class 0 (WAIT)
        brier = float(brier_score_loss((y_test == 0).astype(int), probs[:, 0])) if probs.shape[1] >= 1 else 0.0

        results[name] = {
            "accuracy": round(acc, 4),
            "f1_macro": round(f1, 4),
            "brier_score": round(brier, 4),
        }
        if f1 > best_f1:
            best_f1 = f1
            best_name = name
            best_model = model

    # Feature importance from Random Forest for explainability
    rf_explain = RandomForestClassifier(n_estimators=80, max_depth=5, random_state=42)
    rf_explain.fit(X_train, y_train)
    importances = {
        col: round(float(imp), 4)
        for col, imp in sorted(zip(FEATURE_COLUMNS, rf_explain.feature_importances_), key=lambda x: x[1], reverse=True)
    }

    ver = version or datetime.now(timezone.utc).strftime("v%Y%m%d_%H%M%S")
    out_dir = Path(model_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    artifact_path = out_dir / f"gold_ai_{ver}.joblib"

    artifact = {
        "model": best_model,
        "model_name": best_name,
        "version": ver,
        "feature_columns": FEATURE_COLUMNS,
        "feature_means": X_train.mean().to_dict(),
        "feature_stds": X_train.std().replace(0.0, 1.0).to_dict(),
        "feature_importance": importances,
        "metrics": results[best_name],
        "all_candidates": results,
        "trained_at_utc": datetime.now(timezone.utc).isoformat(),
    }
    joblib.dump(artifact, artifact_path)
    return {
        "version": ver,
        "best_model": best_name,
        "artifact_path": str(artifact_path),
        "metrics": results[best_name],
        "all_candidates": results,
        "feature_importance": importances,
    }

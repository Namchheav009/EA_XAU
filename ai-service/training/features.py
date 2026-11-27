from typing import List, Tuple
import numpy as np
import pandas as pd
from analysis.indicators import add_all_indicators

FEATURE_COLUMNS: List[str] = [
    "ema_20_50_diff",
    "ema_50_200_diff",
    "rsi_14",
    "macd_main",
    "macd_signal",
    "macd_hist",
    "atr_14",
    "adx_14",
    "body_ratio",
    "upper_wick_ratio",
    "lower_wick_ratio",
    "return_1",
    "hist_vol_20",
    "tick_volume_norm",
]


def build_feature_matrix(df: pd.DataFrame) -> pd.DataFrame:
    """Build ML feature matrix strictly from past/current completed bars (no future leakage)."""
    enriched = add_all_indicators(df)
    close = enriched["close"].replace(0.0, np.nan)

    feat = pd.DataFrame(index=enriched.index)
    feat["ema_20_50_diff"] = (enriched["ema_20"] - enriched["ema_50"]) / close
    feat["ema_50_200_diff"] = (enriched["ema_50"] - enriched["ema_200"]) / close
    feat["rsi_14"] = enriched["rsi_14"] / 100.0
    feat["macd_main"] = enriched["macd_main"] / close
    feat["macd_signal"] = enriched["macd_signal"] / close
    feat["macd_hist"] = enriched["macd_hist"] / close
    feat["atr_14"] = enriched["atr_14"] / close
    feat["adx_14"] = enriched["adx_14"] / 100.0
    feat["body_ratio"] = enriched["body_ratio"]
    feat["upper_wick_ratio"] = enriched["upper_wick_ratio"]
    feat["lower_wick_ratio"] = enriched["lower_wick_ratio"]
    feat["return_1"] = enriched["return_1"]
    feat["hist_vol_20"] = enriched["return_1"].rolling(20).std().fillna(0.0)
    vol_mean = enriched["tick_volume"].rolling(20).mean().replace(0.0, 1.0).fillna(1.0)
    feat["tick_volume_norm"] = (enriched["tick_volume"] / vol_mean).fillna(1.0)

    return feat.replace([np.inf, -np.inf], 0.0).fillna(0.0)


def create_labels(df: pd.DataFrame, horizon: int = 4, tx_cost_pct: float = 0.0005) -> pd.Series:
    """Label future return net of transaction costs: 1=BUY, 2=SELL, 0=WAIT."""
    future_ret = (df["close"].shift(-horizon) - df["close"]) / df["close"]
    labels = pd.Series(0, index=df.index, dtype=int)
    labels[future_ret > tx_cost_pct] = 1
    labels[future_ret < -tx_cost_pct] = 2
    return labels


def chronological_split(
    X: pd.DataFrame, y: pd.Series, train_ratio: float = 0.6, val_ratio: float = 0.2
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.Series, pd.Series, pd.Series]:
    n = len(X)
    train_end = int(n * train_ratio)
    val_end = int(n * (train_ratio + val_ratio))
    return (
        X.iloc[:train_end],
        X.iloc[train_end:val_end],
        X.iloc[val_end:],
        y.iloc[:train_end],
        y.iloc[train_end:val_end],
        y.iloc[val_end:],
    )

from typing import Dict, Any
import numpy as np
import pandas as pd


def analyze_volatility(df: pd.DataFrame) -> Dict[str, Any]:
    close = float(df["close"].iloc[-1])
    atr = float(df["atr_14"].iloc[-1])
    atr_pct = (atr / close) * 100.0 if close > 0 else 0.0
    returns = df["close"].pct_change().dropna()
    hist_vol = float(returns.tail(20).std() * np.sqrt(96) * 100.0) if len(returns) >= 20 else 0.0

    if atr_pct > 0.65:
        vol_regime = "HIGH"
    elif atr_pct < 0.12:
        vol_regime = "LOW"
    else:
        vol_regime = "NORMAL"

    return {
        "atr_14": round(atr, 3),
        "atr_percent": round(atr_pct, 4),
        "historical_volatility_pct": round(hist_vol, 3),
        "volatility_regime": vol_regime,
    }

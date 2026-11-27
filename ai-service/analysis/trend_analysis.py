from typing import Any, Dict
import pandas as pd
from analysis.indicators import add_all_indicators
from analysis.market_structure import detect_support_resistance
from analysis.volatility import analyze_volatility


def analyze_market(df_entry: pd.DataFrame, df_trend: pd.DataFrame | None = None) -> Dict[str, Any]:
    enriched = add_all_indicators(df_entry)
    last = enriched.iloc[-1]

    if df_trend is not None and len(df_trend) >= 5:
        trend_df = add_all_indicators(df_trend)
        h1_last = trend_df.iloc[-1]
        h1_ema50 = float(h1_last["ema_50"])
        h1_ema200 = float(h1_last["ema_200"])
        h1_close = float(h1_last["close"])
    else:
        h1_ema50 = float(last["ema_50"])
        h1_ema200 = float(last["ema_200"])
        h1_close = float(last["close"])

    sr = detect_support_resistance(enriched)
    vol = analyze_volatility(enriched)

    adx = float(last["adx_14"])
    if vol["volatility_regime"] == "HIGH":
        regime = "HIGH_VOLATILITY"
        trend_dir = "VOLATILE"
    elif adx >= 20.0 and h1_ema50 > h1_ema200 and h1_close > h1_ema50:
        regime = "TRENDING_BULL"
        trend_dir = "BULLISH"
    elif adx >= 20.0 and h1_ema50 < h1_ema200 and h1_close < h1_ema50:
        regime = "TRENDING_BEAR"
        trend_dir = "BEARISH"
    else:
        regime = "RANGING"
        trend_dir = "SIDEWAYS"

    return {
        "close": round(float(last["close"]), 2),
        "ema_20": round(float(last["ema_20"]), 2),
        "ema_50": round(float(last["ema_50"]), 2),
        "ema_200": round(float(last["ema_200"]), 2),
        "rsi_14": round(float(last["rsi_14"]), 2),
        "atr_14": round(float(last["atr_14"]), 3),
        "macd_main": round(float(last["macd_main"]), 4),
        "macd_signal": round(float(last["macd_signal"]), 4),
        "adx_14": round(adx, 2),
        "plus_di": round(float(last["plus_di"]), 2),
        "minus_di": round(float(last["minus_di"]), 2),
        "h1_ema_50": round(h1_ema50, 2),
        "h1_ema_200": round(h1_ema200, 2),
        "trend_direction": trend_dir,
        "market_regime": regime,
        "support_resistance": sr,
        "volatility": vol,
    }

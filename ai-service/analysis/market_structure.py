from typing import Any, Dict, List
import pandas as pd


def detect_support_resistance(df: pd.DataFrame, lookback: int = 60) -> Dict[str, Any]:
    recent = df.tail(lookback)
    highs = recent["high"].tolist()
    lows = recent["low"].tolist()

    swing_highs: List[float] = []
    swing_lows: List[float] = []

    for i in range(2, len(recent) - 2):
        if highs[i] > highs[i - 1] and highs[i] > highs[i - 2] and highs[i] > highs[i + 1] and highs[i] > highs[i + 2]:
            swing_highs.append(round(float(highs[i]), 2))
        if lows[i] < lows[i - 1] and lows[i] < lows[i - 2] and lows[i] < lows[i + 1] and lows[i] < lows[i + 2]:
            swing_lows.append(round(float(lows[i]), 2))

    nearest_res = round(float(recent["high"].tail(20).max()), 2)
    nearest_sup = round(float(recent["low"].tail(20).min()), 2)

    structure = "SIDEWAYS"
    if len(swing_highs) >= 2 and len(swing_lows) >= 2:
        if swing_highs[-1] > swing_highs[-2] and swing_lows[-1] > swing_lows[-2]:
            structure = "BULLISH_HH_HL"
        elif swing_highs[-1] < swing_highs[-2] and swing_lows[-1] < swing_lows[-2]:
            structure = "BEARISH_LH_LL"

    return {
        "nearest_support": nearest_sup,
        "nearest_resistance": nearest_res,
        "swing_highs": swing_highs[-5:],
        "swing_lows": swing_lows[-5:],
        "market_structure": structure,
    }

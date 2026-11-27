from datetime import datetime, timezone
from typing import Any, Dict, List
import pandas as pd
from analysis.indicators import add_all_indicators
from analysis.trend_analysis import analyze_market


def evaluate_strategies(
    df_entry: pd.DataFrame,
    df_trend: pd.DataFrame | None = None,
    strategy_mode: str = "HYBRID",
    min_score: int = 65,
) -> Dict[str, Any]:
    """Evaluate Strategy A (Pullback), Strategy B (Breakout), and Strategy C (Regime Filter)."""
    enriched = add_all_indicators(df_entry)
    analysis = analyze_market(df_entry, df_trend)
    regime = analysis["market_regime"]

    # Use completed candle (-2) if live, or last completed bar (-1)
    bar = enriched.iloc[-1]
    prev = enriched.iloc[-2] if len(enriched) >= 2 else bar

    candle_range = max(float(bar["high"] - bar["low"]), 0.01)
    body_ratio = abs(float(bar["close"] - bar["open"])) / candle_range
    bull_candle = float(bar["close"]) > float(bar["open"]) and body_ratio >= 0.40
    bear_candle = float(bar["close"]) < float(bar["open"]) and body_ratio >= 0.40

    reasons: List[str] = []
    rejection_reasons: List[str] = []
    signal = "WAIT"
    score = 0
    selected_strategy = "StrategyA_TrendPullback"

    if regime == "HIGH_VOLATILITY":
        rejection_reasons.append("Strategy C Regime Filter blocked entry due to HIGH_VOLATILITY.")
        return _build_signal(signal, score, selected_strategy, analysis, reasons, rejection_reasons)

    # Strategy A: Trend-Following Pullback
    if strategy_mode in ("PULLBACK", "HYBRID") and regime in ("TRENDING_BULL", "TRENDING_BEAR"):
        selected_strategy = "StrategyA_TrendPullback"
        if regime == "TRENDING_BULL" and (float(prev["low"]) <= float(bar["ema_20"]) or float(bar["low"]) <= float(bar["ema_20"])) and bull_candle:
            score = 45
            reasons.append("H1 bullish trend (EMA50 > EMA200) & M15 EMA20 pullback")
            if 40.0 <= float(bar["rsi_14"]) <= 70.0:
                score += 20
                reasons.append(f"RSI14={bar['rsi_14']:.1f} in bullish zone")
            if float(bar["macd_main"]) > float(bar["macd_signal"]):
                score += 20
                reasons.append("MACD bullish crossover/momentum")
            if float(bar["close"]) > float(bar["ema_50"]):
                score += 15
                reasons.append("Price above M15 EMA50")
            if score >= min_score:
                signal = "BUY"
            else:
                rejection_reasons.append(f"Score {score} below threshold {min_score}")
            return _build_signal(signal, score, selected_strategy, analysis, reasons, rejection_reasons)

        if regime == "TRENDING_BEAR" and (float(prev["high"]) >= float(bar["ema_20"]) or float(bar["high"]) >= float(bar["ema_20"])) and bear_candle:
            score = 45
            reasons.append("H1 bearish trend (EMA50 < EMA200) & M15 EMA20 pullback")
            if 30.0 <= float(bar["rsi_14"]) <= 60.0:
                score += 20
                reasons.append(f"RSI14={bar['rsi_14']:.1f} in bearish zone")
            if float(bar["macd_main"]) < float(bar["macd_signal"]):
                score += 20
                reasons.append("MACD bearish momentum")
            if float(bar["close"]) < float(bar["ema_50"]):
                score += 15
                reasons.append("Price below M15 EMA50")
            if score >= min_score:
                signal = "SELL"
            else:
                rejection_reasons.append(f"Score {score} below threshold {min_score}")
            return _build_signal(signal, score, selected_strategy, analysis, reasons, rejection_reasons)

    # Strategy B: Breakout
    if strategy_mode in ("BREAKOUT", "HYBRID"):
        selected_strategy = "StrategyB_Breakout"
        res_lvl = analysis["support_resistance"]["nearest_resistance"]
        sup_lvl = analysis["support_resistance"]["nearest_support"]

        if float(prev["close"]) <= res_lvl < float(bar["close"]) and bull_candle:
            score = 50
            reasons.append(f"Bullish breakout above resistance {res_lvl}")
            if float(bar["adx_14"]) >= 20.0 and float(bar["plus_di"]) > float(bar["minus_di"]):
                score += 25
                reasons.append("ADX confirms bullish breakout strength")
            if float(bar["macd_main"]) > float(bar["macd_signal"]):
                score += 25
                reasons.append("MACD confirms momentum")
            if score >= min_score:
                signal = "BUY"
            else:
                rejection_reasons.append(f"Score {score} below threshold {min_score}")
            return _build_signal(signal, score, selected_strategy, analysis, reasons, rejection_reasons)

        if float(prev["close"]) >= sup_lvl > float(bar["close"]) and bear_candle:
            score = 50
            reasons.append(f"Bearish breakout below support {sup_lvl}")
            if float(bar["adx_14"]) >= 20.0 and float(bar["minus_di"]) > float(bar["plus_di"]):
                score += 25
                reasons.append("ADX confirms bearish breakout strength")
            if float(bar["macd_main"]) < float(bar["macd_signal"]):
                score += 25
                reasons.append("MACD confirms momentum")
            if score >= min_score:
                signal = "SELL"
            else:
                rejection_reasons.append(f"Score {score} below threshold {min_score}")
            return _build_signal(signal, score, selected_strategy, analysis, reasons, rejection_reasons)

    rejection_reasons.append("No confirmed pullback or breakout setup on completed candle.")
    return _build_signal("WAIT", score, selected_strategy, analysis, reasons, rejection_reasons)


def _build_signal(
    signal: str,
    score: int,
    strategy_name: str,
    analysis: Dict[str, Any],
    reasons: List[str],
    rejection_reasons: List[str],
) -> Dict[str, Any]:
    return {
        "signal": signal,
        "score": min(100, max(0, score)),
        "strategy_name": strategy_name,
        "timeframe": "M15",
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "market_regime": analysis["market_regime"],
        "reasons": reasons,
        "rejection_reasons": rejection_reasons,
        "analysis": analysis,
    }

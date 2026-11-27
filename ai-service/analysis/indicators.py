import numpy as np
import pandas as pd


def compute_ema(series: pd.Series, period: int) -> pd.Series:
    return series.ewm(span=period, adjust=False).mean()


def compute_rsi(series: pd.Series, period: int = 14) -> pd.Series:
    delta = series.diff()
    gain = delta.clip(lower=0.0)
    loss = -delta.clip(upper=0.0)
    avg_gain = gain.ewm(alpha=1.0 / period, min_periods=period, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1.0 / period, min_periods=period, adjust=False).mean()
    rs = avg_gain / avg_loss.replace(0.0, np.nan)
    rsi = 100.0 - (100.0 / (1.0 + rs))
    return rsi.fillna(50.0)


def compute_atr(df: pd.DataFrame, period: int = 14) -> pd.Series:
    high = df["high"]
    low = df["low"]
    prev_close = df["close"].shift(1)
    tr = pd.concat(
        [
            high - low,
            (high - prev_close).abs(),
            (low - prev_close).abs(),
        ],
        axis=1,
    ).max(axis=1)
    return tr.ewm(alpha=1.0 / period, min_periods=1, adjust=False).mean().fillna(0.0)


def compute_macd(series: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9) -> tuple[pd.Series, pd.Series, pd.Series]:
    ema_fast = compute_ema(series, fast)
    ema_slow = compute_ema(series, slow)
    macd_line = ema_fast - ema_slow
    signal_line = compute_ema(macd_line, signal)
    hist = macd_line - signal_line
    return macd_line, signal_line, hist


def compute_adx(df: pd.DataFrame, period: int = 14) -> tuple[pd.Series, pd.Series, pd.Series]:
    high = df["high"]
    low = df["low"]
    up_move = high.diff()
    down_move = -low.diff()

    plus_dm = np.where((up_move > down_move) & (up_move > 0), up_move, 0.0)
    minus_dm = np.where((down_move > up_move) & (down_move > 0), down_move, 0.0)

    atr = compute_atr(df, period).replace(0.0, np.nan)
    plus_di = 100.0 * pd.Series(plus_dm, index=df.index).ewm(alpha=1.0 / period, adjust=False).mean() / atr
    minus_di = 100.0 * pd.Series(minus_dm, index=df.index).ewm(alpha=1.0 / period, adjust=False).mean() / atr

    dx = 100.0 * (plus_di - minus_di).abs() / (plus_di + minus_di).replace(0.0, np.nan)
    adx = dx.ewm(alpha=1.0 / period, adjust=False).mean().fillna(20.0)
    return adx, plus_di.fillna(20.0), minus_di.fillna(20.0)


def add_all_indicators(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out["ema_20"] = compute_ema(out["close"], 20)
    out["ema_50"] = compute_ema(out["close"], 50)
    out["ema_200"] = compute_ema(out["close"], 200)
    out["rsi_14"] = compute_rsi(out["close"], 14)
    out["atr_14"] = compute_atr(out, 14)
    macd_main, macd_sig, macd_hist = compute_macd(out["close"])
    out["macd_main"] = macd_main
    out["macd_signal"] = macd_sig
    out["macd_hist"] = macd_hist
    adx, plus_di, minus_di = compute_adx(out, 14)
    out["adx_14"] = adx
    out["plus_di"] = plus_di
    out["minus_di"] = minus_di

    candle_range = (out["high"] - out["low"]).replace(0.0, 1e-6)
    out["body_ratio"] = (out["close"] - out["open"]).abs() / candle_range
    out["upper_wick_ratio"] = (out["high"] - out[["open", "close"]].max(axis=1)) / candle_range
    out["lower_wick_ratio"] = (out[["open", "close"]].min(axis=1) - out["low"]) / candle_range
    out["return_1"] = out["close"].pct_change().fillna(0.0)
    return out

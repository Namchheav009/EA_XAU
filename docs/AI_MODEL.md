# Hybrid AI Model Pipeline

## Role of AI
The AI service acts strictly as a **confirmation filter**. It cannot override `RiskManager` or execute orders directly. If no trained model exists, or the model is stale/invalid, it returns `WAIT`.

## Pipeline (`ai-service/training/`)
1. **Features (`features.py`)**: Normalized EMA differences (`20-50`, `50-200`), RSI(14), MACD, ATR(14), ADX(14), candle body/wick ratios, returns, 20-bar historical volatility, normalized tick volume.
2. **Labeling**: Future `horizon=4` bar return net of transaction costs (`1=BUY`, `2=SELL`, `0=WAIT`).
3. **Splitting**: Chronological 60% train / 20% validation / 20% test (no random shuffling to prevent future leakage).
4. **Models (`train_pipeline.py`)**: Logistic Regression (baseline), Random Forest, and Gradient Boosting with probability calibration (`CalibratedClassifierCV`).
5. **Monitoring (`services/ai_service.py`)**: Feature drift detection (`z-score > 4.0`) and prediction TTL expiration.

//+------------------------------------------------------------------+
//|                                               StrategyEngine.mqh |
//|                                    GoldAITrader Strategy Engine  |
//|  Implements Strategy A (Pullback), B (Breakout), C (Regime)      |
//|  with 0-100 explainable scoring and rejection reasons            |
//+------------------------------------------------------------------+
#property copyright "GoldAITrader"
#property strict

#include "Config.mqh"
#include "MarketAnalysis.mqh"

struct SStrategySignal
{
   ENUM_SIGNAL_TYPE signal;
   int              score;          // 0 to 100
   string           strategyName;
   ENUM_TIMEFRAMES  timeframe;
   datetime         barTime;
   string           reasons;
   string           rejectionReason;
};

class CStrategyEngine
{
private:
   SStrategySignal EvaluatePullback(const SMarketSnapshot &s, const STraderConfig &cfg) const
   {
      SStrategySignal res;
      res.signal          = SIGNAL_WAIT;
      res.score           = 0;
      res.strategyName    = "StrategyA_TrendPullback";
      res.timeframe       = cfg.entryTimeframe;
      res.barTime         = s.barTime;
      res.reasons         = "";
      res.rejectionReason = "";

      if(s.regime == REGIME_RANGING || s.regime == REGIME_HIGH_VOLATILITY)
      {
         res.rejectionReason = "Regime filter blocked pullback (ranging or high volatility).";
         return res;
      }

      // Bullish Pullback
      if(s.regime == REGIME_TRENDING_BULL && s.isBullishPullback)
      {
         int score = 40; // H1 trend + pullback base
         string reasons = "H1 bullish trend (EMA50>EMA200); M15 EMA20 pullback";
         if(s.rsi14 > 40.0 && s.rsi14 < cfg.rsiBuyMax)
         {
            score += 20;
            reasons += StringFormat("; RSI14=%.1f favorable", s.rsi14);
         }
         if(s.macdMain > s.macdSignal)
         {
            score += 20;
            reasons += "; MACD bullish";
         }
         if(s.closePrice > s.ema50)
         {
            score += 20;
            reasons += "; Price above M15 EMA50";
         }

         res.score = score;
         res.reasons = reasons;
         if(score >= cfg.minSignalScore)
            res.signal = SIGNAL_BUY;
         else
            res.rejectionReason = StringFormat("Score %d < min %d", score, cfg.minSignalScore);
         return res;
      }

      // Bearish Pullback
      if(s.regime == REGIME_TRENDING_BEAR && s.isBearishPullback)
      {
         int score = 40;
         string reasons = "H1 bearish trend (EMA50<EMA200); M15 EMA20 pullback";
         if(s.rsi14 < 60.0 && s.rsi14 > cfg.rsiSellMin)
         {
            score += 20;
            reasons += StringFormat("; RSI14=%.1f favorable", s.rsi14);
         }
         if(s.macdMain < s.macdSignal)
         {
            score += 20;
            reasons += "; MACD bearish";
         }
         if(s.closePrice < s.ema50)
         {
            score += 20;
            reasons += "; Price below M15 EMA50";
         }

         res.score = score;
         res.reasons = reasons;
         if(score >= cfg.minSignalScore)
            res.signal = SIGNAL_SELL;
         else
            res.rejectionReason = StringFormat("Score %d < min %d", score, cfg.minSignalScore);
         return res;
      }

      res.rejectionReason = "No valid pullback setup on completed candle.";
      return res;
   }

   SStrategySignal EvaluateBreakout(const SMarketSnapshot &s, const STraderConfig &cfg) const
   {
      SStrategySignal res;
      res.signal          = SIGNAL_WAIT;
      res.score           = 0;
      res.strategyName    = "StrategyB_Breakout";
      res.timeframe       = cfg.entryTimeframe;
      res.barTime         = s.barTime;
      res.reasons         = "";
      res.rejectionReason = "";

      if(s.regime == REGIME_HIGH_VOLATILITY)
      {
         res.rejectionReason = "Regime filter blocked breakout (extreme volatility).";
         return res;
      }

      if(s.isBullishBreakout)
      {
         int score = 45;
         string reasons = StringFormat("Bullish breakout above %.2f", s.nearestResistance);
         if(s.adx14 >= cfg.adxTrendThreshold && s.plusDI > s.minusDI)
         {
            score += 25;
            reasons += StringFormat("; ADX=%.1f (+DI>-DI)", s.adx14);
         }
         if(s.h1Ema50 > s.h1Ema200)
         {
            score += 15;
            reasons += "; H1 trend aligned";
         }
         if(s.macdMain > s.macdSignal)
         {
            score += 15;
            reasons += "; MACD momentum confirmed";
         }
         res.score = score;
         res.reasons = reasons;
         if(score >= cfg.minSignalScore)
            res.signal = SIGNAL_BUY;
         else
            res.rejectionReason = StringFormat("Score %d < min %d", score, cfg.minSignalScore);
         return res;
      }

      if(s.isBearishBreakout)
      {
         int score = 45;
         string reasons = StringFormat("Bearish breakout below %.2f", s.nearestSupport);
         if(s.adx14 >= cfg.adxTrendThreshold && s.minusDI > s.plusDI)
         {
            score += 25;
            reasons += StringFormat("; ADX=%.1f (-DI>+DI)", s.adx14);
         }
         if(s.h1Ema50 < s.h1Ema200)
         {
            score += 15;
            reasons += "; H1 trend aligned";
         }
         if(s.macdMain < s.macdSignal)
         {
            score += 15;
            reasons += "; MACD momentum confirmed";
         }
         res.score = score;
         res.reasons = reasons;
         if(score >= cfg.minSignalScore)
            res.signal = SIGNAL_SELL;
         else
            res.rejectionReason = StringFormat("Score %d < min %d", score, cfg.minSignalScore);
         return res;
      }

      res.rejectionReason = "No valid S/R breakout on completed candle.";
      return res;
   }

public:
   SStrategySignal Evaluate(const SMarketSnapshot &snap, const STraderConfig &cfg) const
   {
      if(!snap.valid)
      {
         SStrategySignal invalid;
         invalid.signal = SIGNAL_WAIT;
         invalid.score = 0;
         invalid.strategyName = "None";
         invalid.timeframe = cfg.entryTimeframe;
         invalid.barTime = snap.barTime;
         invalid.rejectionReason = "Market snapshot invalid.";
         return invalid;
      }

      if(cfg.strategyType == STRATEGY_PULLBACK)
         return EvaluatePullback(snap, cfg);

      if(cfg.strategyType == STRATEGY_BREAKOUT)
         return EvaluateBreakout(snap, cfg);

      // STRATEGY_HYBRID: Use Regime Filter (Strategy C) to route
      if(snap.regime == REGIME_TRENDING_BULL || snap.regime == REGIME_TRENDING_BEAR)
      {
         SStrategySignal pullback = EvaluatePullback(snap, cfg);
         if(pullback.signal != SIGNAL_WAIT)
            return pullback;
         return EvaluateBreakout(snap, cfg);
      }

      return EvaluateBreakout(snap, cfg);
   }
};
//+------------------------------------------------------------------+

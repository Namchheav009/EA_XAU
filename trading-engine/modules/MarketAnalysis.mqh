//+------------------------------------------------------------------+
//|                                               MarketAnalysis.mqh |
//|                                    GoldAITrader Market Analysis  |
//|  Multi-timeframe EMA/RSI/ATR/MACD/ADX, S/R, structure, scoring   |
//|  Uses ONLY completed candles (shift >= 1) to prevent look-ahead  |
//+------------------------------------------------------------------+
#property copyright "GoldAITrader"
#property strict

#include "Config.mqh"

struct SMarketSnapshot
{
   string             symbol;
   datetime           barTime;
   double             closePrice;
   double             highPrice;
   double             lowPrice;
   double             openPrice;

   // Entry timeframe (M15) indicators
   double             ema20;
   double             ema50;
   double             ema200;
   double             rsi14;
   double             atr14;
   double             macdMain;
   double             macdSignal;
   double             adx14;
   double             plusDI;
   double             minusDI;

   // Trend timeframe (H1) indicators
   double             h1Ema50;
   double             h1Ema200;
   double             h1Close;

   // Structure & S/R
   double             nearestSupport;
   double             nearestResistance;
   double             lastSwingHigh;
   double             lastSwingLow;
   ENUM_MARKET_REGIME regime;
   bool               isBullishBreakout;
   bool               isBearishBreakout;
   bool               isBullishPullback;
   bool               isBearishPullback;
   bool               bullishCandleConfirmed;
   bool               bearishCandleConfirmed;
   bool               valid;
};

class CMarketAnalysis
{
private:
   string          m_symbol;
   ENUM_TIMEFRAMES m_entryTf;
   ENUM_TIMEFRAMES m_trendTf;

   int m_hEma20;
   int m_hEma50;
   int m_hEma200;
   int m_hRsi;
   int m_hAtr;
   int m_hMacd;
   int m_hAdx;
   int m_hH1Ema50;
   int m_hH1Ema200;

   bool ReadBuffer(const int handle, const int bufferNum, const int shift, double &outVal) const
   {
      if(handle == INVALID_HANDLE)
         return false;
      double buf[];
      ArraySetAsSeries(buf, true);
      if(CopyBuffer(handle, bufferNum, shift, 1, buf) != 1)
         return false;
      outVal = buf[0];
      return MathIsValidNumber(outVal);
   }

   void DetectSwingsAndSR(const int lookback, double &swingHigh, double &swingLow, double &support, double &resistance) const
   {
      double highs[], lows[];
      ArraySetAsSeries(highs, true);
      ArraySetAsSeries(lows, true);

      int copiedH = CopyHigh(m_symbol, m_entryTf, 1, lookback, highs);
      int copiedL = CopyLow(m_symbol, m_entryTf, 1, lookback, lows);
      if(copiedH < 10 || copiedL < 10)
      {
         swingHigh = 0.0; swingLow = 0.0; support = 0.0; resistance = 0.0;
         return;
      }

      swingHigh = highs[0];
      swingLow  = lows[0];
      for(int i = 2; i < copiedH - 2; i++)
      {
         if(highs[i] > highs[i - 1] && highs[i] > highs[i - 2] &&
            highs[i] > highs[i + 1] && highs[i] > highs[i + 2])
         {
            swingHigh = highs[i];
            break;
         }
      }
      for(int i = 2; i < copiedL - 2; i++)
      {
         if(lows[i] < lows[i - 1] && lows[i] < lows[i - 2] &&
            lows[i] < lows[i + 1] && lows[i] < lows[i + 2])
         {
            swingLow = lows[i];
            break;
         }
      }

      resistance = highs[ArrayMaximum(highs, 0, MathMin(20, copiedH))];
      support    = lows[ArrayMinimum(lows, 0, MathMin(20, copiedL))];
   }

public:
   CMarketAnalysis()
      : m_symbol(""), m_entryTf(PERIOD_M15), m_trendTf(PERIOD_H1),
        m_hEma20(INVALID_HANDLE), m_hEma50(INVALID_HANDLE), m_hEma200(INVALID_HANDLE),
        m_hRsi(INVALID_HANDLE), m_hAtr(INVALID_HANDLE), m_hMacd(INVALID_HANDLE),
        m_hAdx(INVALID_HANDLE), m_hH1Ema50(INVALID_HANDLE), m_hH1Ema200(INVALID_HANDLE) {}

   bool Init(const string symbol, const STraderConfig &cfg)
   {
      m_symbol  = symbol;
      m_entryTf = cfg.entryTimeframe;
      m_trendTf = cfg.trendTimeframe;

      m_hEma20    = iMA(m_symbol, m_entryTf, cfg.emaFastPeriod, 0, MODE_EMA, PRICE_CLOSE);
      m_hEma50    = iMA(m_symbol, m_entryTf, cfg.emaMidPeriod, 0, MODE_EMA, PRICE_CLOSE);
      m_hEma200   = iMA(m_symbol, m_entryTf, cfg.emaSlowPeriod, 0, MODE_EMA, PRICE_CLOSE);
      m_hRsi      = iRSI(m_symbol, m_entryTf, cfg.rsiPeriod, PRICE_CLOSE);
      m_hAtr      = iATR(m_symbol, m_entryTf, cfg.atrPeriod);
      m_hMacd     = iMACD(m_symbol, m_entryTf, 12, 26, 9, PRICE_CLOSE);
      m_hAdx      = iADX(m_symbol, m_entryTf, cfg.adxPeriod);
      m_hH1Ema50  = iMA(m_symbol, m_trendTf, cfg.emaMidPeriod, 0, MODE_EMA, PRICE_CLOSE);
      m_hH1Ema200 = iMA(m_symbol, m_trendTf, cfg.emaSlowPeriod, 0, MODE_EMA, PRICE_CLOSE);

      return (m_hEma20 != INVALID_HANDLE && m_hEma50 != INVALID_HANDLE && m_hEma200 != INVALID_HANDLE &&
              m_hRsi != INVALID_HANDLE && m_hAtr != INVALID_HANDLE && m_hMacd != INVALID_HANDLE &&
              m_hAdx != INVALID_HANDLE && m_hH1Ema50 != INVALID_HANDLE && m_hH1Ema200 != INVALID_HANDLE);
   }

   void Release()
   {
      int handles[] = {m_hEma20, m_hEma50, m_hEma200, m_hRsi, m_hAtr, m_hMacd, m_hAdx, m_hH1Ema50, m_hH1Ema200};
      for(int i = 0; i < ArraySize(handles); i++)
      {
         if(handles[i] != INVALID_HANDLE)
            IndicatorRelease(handles[i]);
      }
      m_hEma20 = m_hEma50 = m_hEma200 = m_hRsi = m_hAtr = m_hMacd = m_hAdx = m_hH1Ema50 = m_hH1Ema200 = INVALID_HANDLE;
   }

   //+------------------------------------------------------------------+
   //| Analyze completed bar (shift=1) to avoid look-ahead bias         |
   //+------------------------------------------------------------------+
   bool AnalyzeCompletedBar(const STraderConfig &cfg, SMarketSnapshot &snap) const
   {
      ZeroMemory(snap);
      snap.symbol = m_symbol;
      snap.valid  = false;

      MqlRates rates[];
      ArraySetAsSeries(rates, true);
      if(CopyRates(m_symbol, m_entryTf, 1, 3, rates) < 3)
         return false;

      snap.barTime    = rates[0].time;
      snap.openPrice  = rates[0].open;
      snap.highPrice  = rates[0].high;
      snap.lowPrice   = rates[0].low;
      snap.closePrice = rates[0].close;

      if(!ReadBuffer(m_hEma20, 0, 1, snap.ema20) ||
         !ReadBuffer(m_hEma50, 0, 1, snap.ema50) ||
         !ReadBuffer(m_hEma200, 0, 1, snap.ema200) ||
         !ReadBuffer(m_hRsi, 0, 1, snap.rsi14) ||
         !ReadBuffer(m_hAtr, 0, 1, snap.atr14) ||
         !ReadBuffer(m_hMacd, 0, 1, snap.macdMain) ||
         !ReadBuffer(m_hMacd, 1, 1, snap.macdSignal) ||
         !ReadBuffer(m_hAdx, 0, 1, snap.adx14) ||
         !ReadBuffer(m_hAdx, 1, 1, snap.plusDI) ||
         !ReadBuffer(m_hAdx, 2, 1, snap.minusDI) ||
         !ReadBuffer(m_hH1Ema50, 0, 1, snap.h1Ema50) ||
         !ReadBuffer(m_hH1Ema200, 0, 1, snap.h1Ema200))
      {
         return false;
      }

      snap.h1Close = iClose(m_symbol, m_trendTf, 1);

      DetectSwingsAndSR(60, snap.lastSwingHigh, snap.lastSwingLow, snap.nearestSupport, snap.nearestResistance);

      // Market Regime Classification
      double atrPct = (snap.closePrice > 0.0) ? (snap.atr14 / snap.closePrice) * 100.0 : 0.0;
      if(atrPct > 0.65)
         snap.regime = REGIME_HIGH_VOLATILITY;
      else if(snap.adx14 >= cfg.adxTrendThreshold && snap.h1Ema50 > snap.h1Ema200 && snap.h1Close > snap.h1Ema50)
         snap.regime = REGIME_TRENDING_BULL;
      else if(snap.adx14 >= cfg.adxTrendThreshold && snap.h1Ema50 < snap.h1Ema200 && snap.h1Close < snap.h1Ema50)
         snap.regime = REGIME_TRENDING_BEAR;
      else
         snap.regime = REGIME_RANGING;

      // Candle Confirmation on completed bar
      double body  = MathAbs(rates[0].close - rates[0].open);
      double range = MathMax(rates[0].high - rates[0].low, _Point);
      snap.bullishCandleConfirmed = (rates[0].close > rates[0].open) && (body / range >= 0.45);
      snap.bearishCandleConfirmed = (rates[0].close < rates[0].open) && (body / range >= 0.45);

      // Pullback & Breakout Detection
      snap.isBullishPullback = (rates[1].low <= snap.ema20 || rates[0].low <= snap.ema20) &&
                               (rates[0].close > snap.ema20) && snap.bullishCandleConfirmed;
      snap.isBearishPullback = (rates[1].high >= snap.ema20 || rates[0].high >= snap.ema20) &&
                               (rates[0].close < snap.ema20) && snap.bearishCandleConfirmed;

      snap.isBullishBreakout = (snap.nearestResistance > 0.0) &&
                               (rates[1].close <= snap.nearestResistance) &&
                               (rates[0].close > snap.nearestResistance) && snap.bullishCandleConfirmed;
      snap.isBearishBreakout = (snap.nearestSupport > 0.0) &&
                               (rates[1].close >= snap.nearestSupport) &&
                               (rates[0].close < snap.nearestSupport) && snap.bearishCandleConfirmed;

      snap.valid = true;
      return true;
   }
};
//+------------------------------------------------------------------+

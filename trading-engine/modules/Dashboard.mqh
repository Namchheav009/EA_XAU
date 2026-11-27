//+------------------------------------------------------------------+
//|                                                    Dashboard.mqh |
//|                                    GoldAITrader Chart Dashboard  |
//|  Displays live EA status, regime, signals, risk, and safety info |
//+------------------------------------------------------------------+
#property copyright "GoldAITrader"
#property strict

#include "Config.mqh"
#include "MarketAnalysis.mqh"
#include "StrategyEngine.mqh"
#include "RiskManager.mqh"
#include "SessionFilter.mqh"
#include "NewsFilter.mqh"
#include "AIClient.mqh"

class CDashboard
{
private:
   string SignalToStr(const ENUM_SIGNAL_TYPE sig) const
   {
      if(sig == SIGNAL_BUY)  return "BUY";
      if(sig == SIGNAL_SELL) return "SELL";
      return "WAIT";
   }

   string RegimeToStr(const ENUM_MARKET_REGIME reg) const
   {
      switch(reg)
      {
         case REGIME_TRENDING_BULL:   return "TRENDING_BULL";
         case REGIME_TRENDING_BEAR:   return "TRENDING_BEAR";
         case REGIME_HIGH_VOLATILITY: return "HIGH_VOLATILITY";
         default:                     return "RANGING";
      }
   }

public:
   void Render(const STraderConfig &cfg,
               const SMarketSnapshot &snap,
               const SStrategySignal &sig,
               const SSessionStatus &sess,
               const SNewsStatus &news,
               const SAiPrediction &ai,
               const CRiskManager &risk,
               const int openPositions,
               const string lastAction) const
   {
      string modeStr = (cfg.operatingMode == MODE_MONITORING) ? "MONITORING (NO ORDERS)" : "DEMO_ONLY";
      string acctType = risk.IsCentAccount() ? "CENT" : "STANDARD";
      string text = StringFormat(
         "=== GoldAITrader v1.0 ===\n"
         "Mode: %s | Symbol: %s | Account: %s (%s)\n"
         "Equity: %.2f | Drawdown: %.2f%% | Daily Loss: %.2f%%\n"
         "Trades Today: %d/%d | Consec Losses: %d/%d | Open: %d\n"
         "Regime: %s | RSI14: %.1f | ATR14: %.2f | ADX14: %.1f\n"
         "Strategy: %s | Signal: %s (Score: %d/100)\n"
         "Session: %s | News: %s\n"
         "AI Filter: %s\n"
         "Last Action: %s",
         modeStr, snap.symbol, acctType, AccountInfoString(ACCOUNT_CURRENCY),
         AccountInfoDouble(ACCOUNT_EQUITY), risk.GetCurrentDrawdownPercent(), risk.GetDailyLossPercent(),
         risk.GetDailyTradeCount(), cfg.maxDailyTrades, risk.GetConsecutiveLosses(), cfg.maxConsecutiveLosses, openPositions,
         RegimeToStr(snap.regime), snap.rsi14, snap.atr14, snap.adx14,
         sig.strategyName, SignalToStr(sig.signal), sig.score,
         sess.activeSession, (news.inBlackout ? "BLACKOUT" : "CLEAR"),
         ai.reason,
         lastAction
      );
      Comment(text);
   }
};
//+------------------------------------------------------------------+

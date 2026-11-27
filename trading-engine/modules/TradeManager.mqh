//+------------------------------------------------------------------+
//|                                                 TradeManager.mqh |
//|                                    GoldAITrader Trade Manager    |
//|  Order execution gated by SafetyManager and RiskManager,         |
//|  filling-mode detection, stop-level checks, retcode validation   |
//+------------------------------------------------------------------+
#property copyright "GoldAITrader"
#property strict

#include <Trade/Trade.mqh>
#include "Config.mqh"
#include "Logger.mqh"
#include "SafetyManager.mqh"
#include "RiskManager.mqh"
#include "PositionManager.mqh"

class CTradeManager
{
private:
   string   m_symbol;
   ulong    m_magic;
   CTrade   m_trade;
   CLogger *m_logger;
   datetime m_lastOrderBarTime;

   ENUM_ORDER_TYPE_FILLING DetectFillingMode() const
   {
      long filling = SymbolInfoInteger(m_symbol, SYMBOL_FILLING_MODE);
      if((filling & SYMBOL_FILLING_FOK) != 0)
         return ORDER_FILLING_FOK;
      if((filling & SYMBOL_FILLING_IOC) != 0)
         return ORDER_FILLING_IOC;
      return ORDER_FILLING_RETURN;
   }

   bool ValidateStops(const ENUM_SIGNAL_TYPE signal, const double entry, const double sl, const double tp, string &reason) const
   {
      long stopLevelPts = SymbolInfoInteger(m_symbol, SYMBOL_TRADE_STOPS_LEVEL);
      double minDist    = stopLevelPts * SymbolInfoDouble(m_symbol, SYMBOL_POINT);

      if(signal == SIGNAL_BUY)
      {
         if(sl >= entry || tp <= entry)
         {
            reason = "Invalid BUY SL/TP orientation.";
            return false;
         }
         if((entry - sl) < minDist || (tp - entry) < minDist)
         {
            reason = "BUY SL/TP closer than broker SYMBOL_TRADE_STOPS_LEVEL.";
            return false;
         }
      }
      else if(signal == SIGNAL_SELL)
      {
         if(sl <= entry || tp >= entry)
         {
            reason = "Invalid SELL SL/TP orientation.";
            return false;
         }
         if((sl - entry) < minDist || (entry - tp) < minDist)
         {
            reason = "SELL SL/TP closer than broker SYMBOL_TRADE_STOPS_LEVEL.";
            return false;
         }
      }
      reason = "";
      return true;
   }

public:
   CTradeManager() : m_symbol(""), m_magic(0), m_logger(NULL), m_lastOrderBarTime(0) {}

   void Init(const string symbol, const ulong magic, const int slippagePts, CLogger *logger)
   {
      m_symbol = symbol;
      m_magic  = magic;
      m_logger = logger;
      m_trade.SetExpertMagicNumber(magic);
      m_trade.SetDeviationInPoints(slippagePts);
      m_trade.SetTypeFilling(DetectFillingMode());
   }

   bool ExecuteSignal(const ENUM_SIGNAL_TYPE signal,
                      const datetime barTime,
                      const string commentTag,
                      const STraderConfig &cfg,
                      const CSafetyManager &safety,
                      CRiskManager &riskMgr,
                      const CPositionManager &posMgr,
                      const double atrValue,
                      string &outStatus)
   {
      if(signal == SIGNAL_WAIT)
      {
         outStatus = "WAIT";
         return false;
      }

      // Duplicate order protection per bar
      if(barTime == m_lastOrderBarTime)
      {
         outStatus = "Duplicate order blocked on same bar.";
         return false;
      }

      // Max simultaneous positions check (also safe for netting)
      if(posMgr.CountOpenPositions() >= cfg.maxSimultaneousPositions)
      {
         outStatus = "Max simultaneous positions already open.";
         return false;
      }

      // Safety guard (monitoring default & real-account block)
      string safetyReason;
      if(!safety.IsExecutionPermitted(cfg, safetyReason))
      {
         outStatus = safetyReason;
         return false;
      }

      // Risk validation & broker-aware sizing
      SRiskCheckResult risk = riskMgr.EvaluateAndSize(signal, atrValue, cfg);
      if(!risk.allowed)
      {
         outStatus = "Risk rejected: " + risk.reason;
         return false;
      }

      double entry = (signal == SIGNAL_BUY) ? SymbolInfoDouble(m_symbol, SYMBOL_ASK) : SymbolInfoDouble(m_symbol, SYMBOL_BID);
      string stopErr;
      if(!ValidateStops(signal, entry, risk.stopLoss, risk.takeProfit, stopErr))
      {
         outStatus = stopErr;
         return false;
      }

      bool sent = false;
      if(signal == SIGNAL_BUY)
         sent = m_trade.Buy(risk.lotSize, m_symbol, entry, risk.stopLoss, risk.takeProfit, commentTag);
      else
         sent = m_trade.Sell(risk.lotSize, m_symbol, entry, risk.stopLoss, risk.takeProfit, commentTag);

      uint retcode = m_trade.ResultRetcode();
      if(!sent || (retcode != TRADE_RETCODE_DONE && retcode != TRADE_RETCODE_PLACED))
      {
         outStatus = StringFormat("Order failed retcode=%u (%s)", retcode, m_trade.ResultRetcodeDescription());
         if(m_logger != NULL)
            m_logger.Error("TradeManager", outStatus);
         return false;
      }

      m_lastOrderBarTime = barTime;
      riskMgr.RecordTradeOpened();
      outStatus = StringFormat("Demo order executed: %s %.2f lots @ %.2f SL=%.2f TP=%.2f",
                               (signal == SIGNAL_BUY ? "BUY" : "SELL"), risk.lotSize, entry, risk.stopLoss, risk.takeProfit);
      if(m_logger != NULL)
         m_logger.Info("TradeManager", outStatus);
      return true;
   }
};
//+------------------------------------------------------------------+

//+------------------------------------------------------------------+
//|                                                SafetyManager.mqh |
//|                                    GoldAITrader Safety Guard     |
//|  Enforces monitoring default, blocks real-account execution,     |
//|  and checks stale data, emergency stop, and terminal permissions |
//+------------------------------------------------------------------+
#property copyright "GoldAITrader"
#property strict

#include "Config.mqh"
#include "Logger.mqh"

class CSafetyManager
{
private:
   bool     m_emergencyStop;
   string   m_emergencyReason;
   CLogger *m_logger;

public:
   CSafetyManager() : m_emergencyStop(false), m_emergencyReason(""), m_logger(NULL) {}

   void Init(CLogger *logger)
   {
      m_logger = logger;
      m_emergencyStop = false;
      m_emergencyReason = "";
   }

   void TriggerEmergencyStop(const string reason)
   {
      m_emergencyStop = true;
      m_emergencyReason = reason;
      if(m_logger != NULL)
         m_logger.Error("SafetyManager", "EMERGENCY STOP TRIGGERED: " + reason);
   }

   void ResetEmergencyStop()
   {
      m_emergencyStop = false;
      m_emergencyReason = "";
   }

   bool IsEmergencyStopped() const { return m_emergencyStop; }
   string GetEmergencyReason() const { return m_emergencyReason; }

   //+------------------------------------------------------------------+
   //| Block all real-account automated execution in initial release    |
   //+------------------------------------------------------------------+
   bool IsExecutionPermitted(const STraderConfig &cfg, string &blockReason) const
   {
      if(m_emergencyStop)
      {
         blockReason = "Emergency stop active: " + m_emergencyReason;
         return false;
      }

      if(cfg.operatingMode == MODE_MONITORING)
      {
         blockReason = "Monitoring mode enabled (order execution disabled).";
         return false;
      }

      if(!cfg.allowDemoTrading)
      {
         blockReason = "Demo trading is not explicitly enabled.";
         return false;
      }

      ENUM_ACCOUNT_TRADE_MODE tradeMode = (ENUM_ACCOUNT_TRADE_MODE)AccountInfoInteger(ACCOUNT_TRADE_MODE);
      if(tradeMode == ACCOUNT_TRADE_MODE_REAL)
      {
         blockReason = "SAFETY BLOCK: Real-account automated execution is disabled in this version.";
         return false;
      }

      if(!TerminalInfoInteger(TERMINAL_TRADE_ALLOWED) || !MQLInfoInteger(MQL_TRADE_ALLOWED))
      {
         blockReason = "AutoTrading is disabled in MT5 terminal or EA properties.";
         return false;
      }

      blockReason = "";
      return true;
   }

   //+------------------------------------------------------------------+
   //| Protect against stale market ticks (> maxAgeSeconds)             |
   //+------------------------------------------------------------------+
   bool IsMarketDataFresh(const string symbol, const int maxAgeSeconds, string &reason) const
   {
      MqlTick tick;
      if(!SymbolInfoTick(symbol, tick))
      {
         reason = "Failed to fetch latest tick for " + symbol;
         return false;
      }

      long age = (long)TimeCurrent() - (long)tick.time;
      if(age > maxAgeSeconds)
      {
         reason = StringFormat("Stale market data (%d seconds old > %d allowed).", age, maxAgeSeconds);
         return false;
      }
      reason = "";
      return true;
   }
};
//+------------------------------------------------------------------+

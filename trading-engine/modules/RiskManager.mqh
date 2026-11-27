//+------------------------------------------------------------------+
//|                                                  RiskManager.mqh |
//|                                    GoldAITrader Risk Manager     |
//|  Broker-aware position sizing via OrderCalcProfit & Margin,      |
//|  Standard/Cent detection, daily loss/drawdown persistence        |
//|                                                                  |
//|  NOTE ON PLANNED RISK VS ACTUAL LOSSES:                          |
//|  Lot sizing bounds planned risk at the stop-loss price assuming  |
//|  exact fill. Actual realized losses may exceed planned risk due  |
//|  to price gaps, spread widening, commissions, and slippage.      |
//+------------------------------------------------------------------+
#property copyright "GoldAITrader"
#property strict

#include "Config.mqh"
#include "Logger.mqh"

struct SRiskCheckResult
{
   bool   allowed;
   double lotSize;
   double stopLoss;
   double takeProfit;
   double plannedRiskAmount;
   string accountCurrency;
   bool   isCentAccount;
   string reason;
};

class CRiskManager
{
private:
   string   m_symbol;
   ulong    m_magic;
   CLogger *m_logger;

   double   m_peakEquity;
   double   m_dayStartBalance;
   int      m_currentDayOfYear;
   int      m_dailyTradeCount;
   int      m_consecutiveLosses;
   bool     m_emergencyStopped;

   string GvKey(const string suffix) const
   {
      return StringFormat("GAT_%I64u_%s", m_magic, suffix);
   }

   void LoadState()
   {
      double equity  = AccountInfoDouble(ACCOUNT_EQUITY);
      double balance = AccountInfoDouble(ACCOUNT_BALANCE);
      MqlDateTime dt;
      TimeGMT(dt);

      m_peakEquity       = GlobalVariableCheck(GvKey("PEAK_EQ")) ? GlobalVariableGet(GvKey("PEAK_EQ")) : equity;
      if(equity > m_peakEquity) m_peakEquity = equity;

      int savedDay = GlobalVariableCheck(GvKey("DAY")) ? (int)GlobalVariableGet(GvKey("DAY")) : -1;
      if(savedDay != dt.day_of_year)
      {
         m_currentDayOfYear = dt.day_of_year;
         m_dayStartBalance  = balance;
         m_dailyTradeCount  = 0;
         SaveState();
      }
      else
      {
         m_currentDayOfYear = savedDay;
         m_dayStartBalance  = GlobalVariableCheck(GvKey("DAY_BAL")) ? GlobalVariableGet(GvKey("DAY_BAL")) : balance;
         m_dailyTradeCount  = GlobalVariableCheck(GvKey("DAY_TRADES")) ? (int)GlobalVariableGet(GvKey("DAY_TRADES")) : 0;
      }

      m_consecutiveLosses = GlobalVariableCheck(GvKey("CONSEC_LOSS")) ? (int)GlobalVariableGet(GvKey("CONSEC_LOSS")) : 0;
      m_emergencyStopped  = GlobalVariableCheck(GvKey("EMERG_STOP")) ? (GlobalVariableGet(GvKey("EMERG_STOP")) > 0.5) : false;
   }

   void SaveState() const
   {
      GlobalVariableSet(GvKey("PEAK_EQ"), m_peakEquity);
      GlobalVariableSet(GvKey("DAY"), (double)m_currentDayOfYear);
      GlobalVariableSet(GvKey("DAY_BAL"), m_dayStartBalance);
      GlobalVariableSet(GvKey("DAY_TRADES"), (double)m_dailyTradeCount);
      GlobalVariableSet(GvKey("CONSEC_LOSS"), (double)m_consecutiveLosses);
      GlobalVariableSet(GvKey("EMERG_STOP"), m_emergencyStopped ? 1.0 : 0.0);
   }

public:
   CRiskManager() : m_symbol(""), m_magic(0), m_logger(NULL), m_peakEquity(0), m_dayStartBalance(0),
                    m_currentDayOfYear(-1), m_dailyTradeCount(0), m_consecutiveLosses(0), m_emergencyStopped(false) {}

   void Init(const string symbol, const ulong magic, CLogger *logger)
   {
      m_symbol = symbol;
      m_magic  = magic;
      m_logger = logger;
      LoadState();
   }

   bool IsCentAccount() const
   {
      string curr = AccountInfoString(ACCOUNT_CURRENCY);
      if(curr == "USC" || curr == "EUC" || curr == "GBC")
         return true;
      if(StringFind(m_symbol, "c") == StringLen(m_symbol) - 1)
         return true;
      return false;
   }

   void OnNewDayCheck()
   {
      MqlDateTime dt;
      TimeGMT(dt);
      if(dt.day_of_year != m_currentDayOfYear)
      {
         m_currentDayOfYear = dt.day_of_year;
         m_dayStartBalance  = AccountInfoDouble(ACCOUNT_BALANCE);
         m_dailyTradeCount  = 0;
         SaveState();
      }
      double eq = AccountInfoDouble(ACCOUNT_EQUITY);
      if(eq > m_peakEquity)
      {
         m_peakEquity = eq;
         SaveState();
      }
   }

   void RecordTradeOpened()
   {
      m_dailyTradeCount++;
      SaveState();
   }

   void RecordTradeClosed(const double profit)
   {
      if(profit < 0.0)
         m_consecutiveLosses++;
      else if(profit > 0.0)
         m_consecutiveLosses = 0;
      SaveState();
   }

   void SetEmergencyStop(const bool stopped)
   {
      m_emergencyStopped = stopped;
      SaveState();
   }

   double GetCurrentDrawdownPercent() const
   {
      if(m_peakEquity <= 0.0) return 0.0;
      double eq = AccountInfoDouble(ACCOUNT_EQUITY);
      return MathMax(0.0, ((m_peakEquity - eq) / m_peakEquity) * 100.0);
   }

   double GetDailyLossPercent() const
   {
      if(m_dayStartBalance <= 0.0) return 0.0;
      double eq = AccountInfoDouble(ACCOUNT_EQUITY);
      double loss = m_dayStartBalance - eq;
      return (loss > 0.0) ? (loss / m_dayStartBalance) * 100.0 : 0.0;
   }

   int GetDailyTradeCount() const { return m_dailyTradeCount; }
   int GetConsecutiveLosses() const { return m_consecutiveLosses; }

   //+------------------------------------------------------------------+
   //| Validate all risk constraints and calculate broker-aware lot     |
   //+------------------------------------------------------------------+
   SRiskCheckResult EvaluateAndSize(const ENUM_SIGNAL_TYPE signal, const double atrValue, const STraderConfig &cfg)
   {
      OnNewDayCheck();

      SRiskCheckResult res;
      ZeroMemory(res);
      res.allowed         = false;
      res.accountCurrency = AccountInfoString(ACCOUNT_CURRENCY);
      res.isCentAccount   = IsCentAccount();

      if(signal == SIGNAL_WAIT)
      {
         res.reason = "Signal is WAIT.";
         return res;
      }

      if(m_emergencyStopped)
      {
         res.reason = "Emergency stop is active.";
         return res;
      }

      double dailyLossPct = GetDailyLossPercent();
      if(dailyLossPct >= cfg.maxDailyLossPercent)
      {
         res.reason = StringFormat("Daily loss limit reached (%.2f%% >= %.2f%%).", dailyLossPct, cfg.maxDailyLossPercent);
         return res;
      }

      double ddPct = GetCurrentDrawdownPercent();
      if(ddPct >= cfg.maxDrawdownPercent)
      {
         m_emergencyStopped = true;
         SaveState();
         res.reason = StringFormat("Max drawdown limit reached (%.2f%% >= %.2f%%). Emergency stop activated.", ddPct, cfg.maxDrawdownPercent);
         return res;
      }

      if(m_dailyTradeCount >= cfg.maxDailyTrades)
      {
         res.reason = StringFormat("Max daily trades reached (%d/%d).", m_dailyTradeCount, cfg.maxDailyTrades);
         return res;
      }

      if(m_consecutiveLosses >= cfg.maxConsecutiveLosses)
      {
         res.reason = StringFormat("Max consecutive losses reached (%d/%d).", m_consecutiveLosses, cfg.maxConsecutiveLosses);
         return res;
      }

      double spreadPts = (double)SymbolInfoInteger(m_symbol, SYMBOL_SPREAD);
      if(spreadPts > cfg.maxSpreadPoints)
      {
         res.reason = StringFormat("Spread too high (%.0f > %.0f points).", spreadPts, cfg.maxSpreadPoints);
         return res;
      }

      if(atrValue <= 0.0)
      {
         res.reason = "Invalid ATR value for stop loss calculation.";
         return res;
      }

      int digits    = (int)SymbolInfoInteger(m_symbol, SYMBOL_DIGITS);
      double ask    = SymbolInfoDouble(m_symbol, SYMBOL_ASK);
      double bid    = SymbolInfoDouble(m_symbol, SYMBOL_BID);
      double slDist = atrValue * cfg.atrStopMultiplier;
      double tpDist = slDist * cfg.riskRewardRatio;

      ENUM_ORDER_TYPE orderType = (signal == SIGNAL_BUY) ? ORDER_TYPE_BUY : ORDER_TYPE_SELL;
      double entryPrice = (signal == SIGNAL_BUY) ? ask : bid;
      double slPrice    = NormalizeDouble((signal == SIGNAL_BUY) ? (entryPrice - slDist) : (entryPrice + slDist), digits);
      double tpPrice    = NormalizeDouble((signal == SIGNAL_BUY) ? (entryPrice + tpDist) : (entryPrice - tpDist), digits);

      // Use broker's OrderCalcProfit for 1.0 lot to determine exact loss in account currency
      double oneLotProfit = 0.0;
      if(!OrderCalcProfit(orderType, m_symbol, 1.0, entryPrice, slPrice, oneLotProfit) || oneLotProfit >= 0.0)
      {
         res.reason = "OrderCalcProfit failed or returned non-negative SL profit.";
         return res;
      }

      double lossPerLot  = MathAbs(oneLotProfit);
      double equity      = AccountInfoDouble(ACCOUNT_EQUITY);
      double riskBudget  = equity * (cfg.riskPercentPerTrade / 100.0);
      double rawLots     = riskBudget / lossPerLot;

      double minVol  = SymbolInfoDouble(m_symbol, SYMBOL_VOLUME_MIN);
      double maxVol  = SymbolInfoDouble(m_symbol, SYMBOL_VOLUME_MAX);
      double volStep = SymbolInfoDouble(m_symbol, SYMBOL_VOLUME_STEP);

      // Reject if minimum allowed volume exceeds configured risk budget
      double minLotRisk = minVol * lossPerLot;
      if(minLotRisk > riskBudget * 1.05) // 5% rounding tolerance
      {
         res.reason = StringFormat("Min volume %.2f risk (%.2f %s) exceeds risk budget (%.2f %s).",
                                   minVol, minLotRisk, res.accountCurrency, riskBudget, res.accountCurrency);
         return res;
      }

      double steps = MathFloor(rawLots / volStep);
      double lots  = NormalizeDouble(steps * volStep, 2);
      lots = MathMax(minVol, MathMin(maxVol, lots));

      // Verify free margin via OrderCalcMargin
      double reqMargin = 0.0;
      if(!OrderCalcMargin(orderType, m_symbol, lots, entryPrice, reqMargin))
      {
         res.reason = "OrderCalcMargin failed.";
         return res;
      }

      double freeMargin = AccountInfoDouble(ACCOUNT_MARGIN_FREE);
      if(reqMargin > freeMargin * 0.80)
      {
         res.reason = StringFormat("Insufficient free margin (required=%.2f, free=%.2f).", reqMargin, freeMargin);
         return res;
      }

      res.allowed           = true;
      res.lotSize           = lots;
      res.stopLoss          = slPrice;
      res.takeProfit        = tpPrice;
      res.plannedRiskAmount = lots * lossPerLot;
      res.reason            = "Risk checks passed.";
      return res;
   }
};
//+------------------------------------------------------------------+

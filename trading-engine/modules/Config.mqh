//+------------------------------------------------------------------+
//|                                                       Config.mqh |
//|                                    GoldAITrader Configuration    |
//|         Centralized configuration, enums, and symbol resolution  |
//+------------------------------------------------------------------+
#property copyright "GoldAITrader"
#property strict

enum ENUM_OPERATING_MODE
{
   MODE_MONITORING = 0, // Monitoring Only (No Orders)
   MODE_DEMO_ONLY  = 1  // Demo Account Execution Only
};

enum ENUM_STRATEGY_TYPE
{
   STRATEGY_PULLBACK = 0, // Strategy A: Trend-Following Pullback
   STRATEGY_BREAKOUT = 1, // Strategy B: Breakout
   STRATEGY_HYBRID   = 2  // Auto-select via Regime Filter
};

enum ENUM_SIGNAL_TYPE
{
   SIGNAL_WAIT = 0,
   SIGNAL_BUY  = 1,
   SIGNAL_SELL = 2
};

enum ENUM_MARKET_REGIME
{
   REGIME_RANGING         = 0,
   REGIME_TRENDING_BULL   = 1,
   REGIME_TRENDING_BEAR   = 2,
   REGIME_HIGH_VOLATILITY = 3
};

struct STraderConfig
{
   // Operating & Execution Safety
   ENUM_OPERATING_MODE operatingMode;
   bool                allowDemoTrading;
   ulong               magicNumber;
   string              symbolOverride;
   int                 maxSlippagePoints;

   // Timeframes
   ENUM_TIMEFRAMES     entryTimeframe;
   ENUM_TIMEFRAMES     trendTimeframe;

   // Strategy
   ENUM_STRATEGY_TYPE  strategyType;
   int                 minSignalScore;
   int                 emaFastPeriod;
   int                 emaMidPeriod;
   int                 emaSlowPeriod;
   int                 rsiPeriod;
   int                 atrPeriod;
   int                 adxPeriod;
   double              adxTrendThreshold;
   double              rsiBuyMax;
   double              rsiSellMin;

   // Risk Management (Defaults: 0.5% risk, 2% daily loss, 10% max DD, 3 trades/day)
   double              riskPercentPerTrade;
   double              maxDailyLossPercent;
   double              maxDrawdownPercent;
   int                 maxDailyTrades;
   int                 maxSimultaneousPositions;
   double              riskRewardRatio;
   int                 maxConsecutiveLosses;
   double              atrStopMultiplier;
   double              maxSpreadPoints;
   bool                useBreakEven;
   double              breakEvenTriggerRR;
   bool                useAtrTrailing;
   double              atrTrailMultiplier;
   bool                usePartialClose;
   double              partialCloseRatio;
   double              partialCloseTriggerRR;

   // Session & News Filters
   bool                enableSessionFilter;
   int                 brokerUtcOffsetHours;
   bool                useDstAdjustment;
   bool                allowAsianSession;
   bool                allowLondonSession;
   bool                allowNewYorkSession;
   bool                closeBeforeWeekend;
   int                 fridayCloseHourUtc;
   bool                enableNewsFilter;
   int                 newsBlackoutBeforeMin;
   int                 newsBlackoutAfterMin;
   string              newsCsvFileName;

   // AI Service Integration
   bool                enableAiFilter;
   string              aiServiceUrl;
   int                 aiTimeoutMs;
   double              aiMinConfidence;
   bool                requireAiConfirmation;
};

//+------------------------------------------------------------------+
//| Resolve gold symbol (XAUUSDc, XAUUSD, or broker suffix)          |
//+------------------------------------------------------------------+
string ResolveGoldSymbol(const string overrideSymbol)
{
   if(StringLen(overrideSymbol) > 0 && SymbolSelect(overrideSymbol, true))
      return overrideSymbol;

   string candidates[] = {"XAUUSDc", "XAUUSD", "XAUUSDm", "XAUUSD.a", "GOLD"};
   for(int i = 0; i < ArraySize(candidates); i++)
   {
      if(SymbolSelect(candidates[i], true))
         return candidates[i];
   }

   int total = SymbolsTotal(false);
   for(int i = 0; i < total; i++)
   {
      string name = SymbolName(i, false);
      if(StringFind(name, "XAUUSD") >= 0)
      {
         SymbolSelect(name, true);
         return name;
      }
   }
   return Symbol();
}

//+------------------------------------------------------------------+
//| Validate configuration parameters                                |
//+------------------------------------------------------------------+
bool ValidateTraderConfig(const STraderConfig &cfg, string &errorReason)
{
   if(cfg.riskPercentPerTrade <= 0.0 || cfg.riskPercentPerTrade > 5.0)
   {
      errorReason = "RiskPercentPerTrade must be between 0.01% and 5.0%.";
      return false;
   }
   if(cfg.maxDailyLossPercent <= 0.0 || cfg.maxDailyLossPercent > 20.0)
   {
      errorReason = "MaxDailyLossPercent must be between 0.1% and 20.0%.";
      return false;
   }
   if(cfg.maxDrawdownPercent <= 0.0 || cfg.maxDrawdownPercent > 50.0)
   {
      errorReason = "MaxDrawdownPercent must be between 1.0% and 50.0%.";
      return false;
   }
   if(cfg.riskRewardRatio < 1.0)
   {
      errorReason = "RiskRewardRatio must be >= 1.0.";
      return false;
   }
   if(cfg.maxDailyTrades < 1 || cfg.maxSimultaneousPositions < 1)
   {
      errorReason = "MaxDailyTrades and MaxSimultaneousPositions must be >= 1.";
      return false;
   }
   if(cfg.atrStopMultiplier <= 0.0)
   {
      errorReason = "AtrStopMultiplier must be > 0.";
      return false;
   }
   errorReason = "";
   return true;
}
//+------------------------------------------------------------------+

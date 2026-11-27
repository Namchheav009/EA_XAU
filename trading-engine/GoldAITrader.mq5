//+------------------------------------------------------------------+
//|                                                 GoldAITrader.mq5 |
//|                                    GoldAITrader Main EA          |
//|  Pipeline: Market Data -> Technical Analysis -> Strategy Signal  |
//|  -> Session Filter -> News Filter -> AI Filter -> Risk           |
//|  -> Demo Order Execution -> Position Management -> Logging       |
//+------------------------------------------------------------------+
#property copyright "GoldAITrader"
#property version   "1.00"
#property strict

#include "modules/Config.mqh"
#include "modules/Logger.mqh"
#include "modules/SafetyManager.mqh"
#include "modules/MarketAnalysis.mqh"
#include "modules/StrategyEngine.mqh"
#include "modules/RiskManager.mqh"
#include "modules/PositionManager.mqh"
#include "modules/TradeManager.mqh"
#include "modules/NewsFilter.mqh"
#include "modules/SessionFilter.mqh"
#include "modules/AIClient.mqh"
#include "modules/Dashboard.mqh"

//--- Input Parameters (Monitoring Mode is default)
input ENUM_OPERATING_MODE InpOperatingMode          = MODE_MONITORING;
input bool                InpAllowDemoTrading        = false;
input ulong               InpMagicNumber             = 20261127;
input string              InpSymbolOverride          = "";
input ENUM_STRATEGY_TYPE  InpStrategyType            = STRATEGY_HYBRID;
input int                 InpMinSignalScore          = 65;

input double              InpRiskPercentPerTrade     = 0.5;
input double              InpMaxDailyLossPercent     = 2.0;
input double              InpMaxDrawdownPercent      = 10.0;
input int                 InpMaxDailyTrades          = 3;
input int                 InpMaxSimultaneousPos      = 1;
input double              InpRiskRewardRatio         = 2.0;
input int                 InpMaxConsecutiveLosses    = 3;
input double              InpAtrStopMultiplier       = 1.5;
input double              InpMaxSpreadPoints         = 45.0;

input bool                InpEnableSessionFilter     = true;
input bool                InpAllowAsianSession       = false;
input bool                InpAllowLondonSession      = true;
input bool                InpAllowNewYorkSession     = true;
input bool                InpCloseBeforeWeekend      = true;
input int                 InpFridayCloseHourUtc      = 20;

input bool                InpEnableNewsFilter        = true;
input int                 InpNewsBlackoutBeforeMin   = 30;
input int                 InpNewsBlackoutAfterMin    = 30;
input string              InpNewsCsvFile             = "economic_news.csv";

input bool                InpEnableAiFilter          = true;
input string              InpAiServiceUrl            = "http://127.0.0.1:8000";
input int                 InpAiTimeoutMs             = 2000;
input double              InpAiMinConfidence           = 0.55;
input bool                InpRequireAiConfirmation   = false;

//--- Global Modules
STraderConfig    g_cfg;
string           g_symbol;
datetime         g_lastBarTime = 0;
string           g_lastAction  = "Initialized";

CLogger          g_logger;
CSafetyManager   g_safety;
CMarketAnalysis  g_market;
CStrategyEngine  g_strategy;
CRiskManager     g_risk;
CPositionManager g_positions;
CTradeManager    g_trade;
CNewsFilter      g_news;
CSessionFilter   g_session;
CAiClient        g_ai;
CDashboard       g_dashboard;

//+------------------------------------------------------------------+
//| Populate configuration struct from inputs                        |
//+------------------------------------------------------------------+
void LoadConfig()
{
   g_cfg.operatingMode            = InpOperatingMode;
   g_cfg.allowDemoTrading         = InpAllowDemoTrading;
   g_cfg.magicNumber              = InpMagicNumber;
   g_cfg.symbolOverride           = InpSymbolOverride;
   g_cfg.maxSlippagePoints        = 30;
   g_cfg.entryTimeframe           = PERIOD_M15;
   g_cfg.trendTimeframe           = PERIOD_H1;
   g_cfg.strategyType             = InpStrategyType;
   g_cfg.minSignalScore           = InpMinSignalScore;
   g_cfg.emaFastPeriod            = 20;
   g_cfg.emaMidPeriod             = 50;
   g_cfg.emaSlowPeriod            = 200;
   g_cfg.rsiPeriod                = 14;
   g_cfg.atrPeriod                = 14;
   g_cfg.adxPeriod                = 14;
   g_cfg.adxTrendThreshold        = 20.0;
   g_cfg.rsiBuyMax                = 70.0;
   g_cfg.rsiSellMin               = 30.0;

   g_cfg.riskPercentPerTrade      = InpRiskPercentPerTrade;
   g_cfg.maxDailyLossPercent      = InpMaxDailyLossPercent;
   g_cfg.maxDrawdownPercent       = InpMaxDrawdownPercent;
   g_cfg.maxDailyTrades           = InpMaxDailyTrades;
   g_cfg.maxSimultaneousPositions = InpMaxSimultaneousPos;
   g_cfg.riskRewardRatio          = InpRiskRewardRatio;
   g_cfg.maxConsecutiveLosses     = InpMaxConsecutiveLosses;
   g_cfg.atrStopMultiplier        = InpAtrStopMultiplier;
   g_cfg.maxSpreadPoints          = InpMaxSpreadPoints;
   g_cfg.useBreakEven             = true;
   g_cfg.breakEvenTriggerRR       = 1.0;
   g_cfg.useAtrTrailing           = true;
   g_cfg.atrTrailMultiplier       = 1.2;
   g_cfg.usePartialClose          = true;
   g_cfg.partialCloseRatio        = 0.5;
   g_cfg.partialCloseTriggerRR    = 1.5;

   g_cfg.enableSessionFilter      = InpEnableSessionFilter;
   g_cfg.brokerUtcOffsetHours     = 0;
   g_cfg.useDstAdjustment         = true;
   g_cfg.allowAsianSession        = InpAllowAsianSession;
   g_cfg.allowLondonSession       = InpAllowLondonSession;
   g_cfg.allowNewYorkSession      = InpAllowNewYorkSession;
   g_cfg.closeBeforeWeekend       = InpCloseBeforeWeekend;
   g_cfg.fridayCloseHourUtc       = InpFridayCloseHourUtc;
   g_cfg.enableNewsFilter         = InpEnableNewsFilter;
   g_cfg.newsBlackoutBeforeMin    = InpNewsBlackoutBeforeMin;
   g_cfg.newsBlackoutAfterMin     = InpNewsBlackoutAfterMin;
   g_cfg.newsCsvFileName          = InpNewsCsvFile;

   g_cfg.enableAiFilter           = InpEnableAiFilter;
   g_cfg.aiServiceUrl             = InpAiServiceUrl;
   g_cfg.aiTimeoutMs              = InpAiTimeoutMs;
   g_cfg.aiMinConfidence          = InpAiMinConfidence;
   g_cfg.requireAiConfirmation    = InpRequireAiConfirmation;
}

//+------------------------------------------------------------------+
//| Expert initialization function                                   |
//+------------------------------------------------------------------+
int OnInit()
{
   LoadConfig();
   g_logger.Init(LOG_INFO, "GoldAITrader_audit.log", true);

   string cfgErr;
   if(!ValidateTraderConfig(g_cfg, cfgErr))
   {
      g_logger.Error("GoldAITrader", "Invalid config: " + cfgErr);
      return INIT_PARAMETERS_INCORRECT;
   }

   g_symbol = ResolveGoldSymbol(g_cfg.symbolOverride);
   g_safety.Init(&g_logger);

   if(!g_market.Init(g_symbol, g_cfg))
   {
      g_logger.Error("GoldAITrader", "Failed to initialize indicator handles.");
      return INIT_FAILED;
   }

   g_risk.Init(g_symbol, g_cfg.magicNumber, &g_logger);
   g_positions.Init(g_symbol, g_cfg.magicNumber, g_cfg.maxSlippagePoints, &g_logger);
   g_trade.Init(g_symbol, g_cfg.magicNumber, g_cfg.maxSlippagePoints, &g_logger);
   g_news.Init(&g_logger);
   g_ai.Init(&g_logger);

   EventSetTimer(15);
   g_logger.Info("GoldAITrader", "Initialized on " + g_symbol);
   return INIT_SUCCEEDED;
}

//+------------------------------------------------------------------+
//| Expert deinitialization function                                 |
//+------------------------------------------------------------------+
void OnDeinit(const int reason)
{
   EventKillTimer();
   g_market.Release();
   Comment("");
   g_logger.Info("GoldAITrader", StringFormat("Deinitialized (reason=%d)", reason));
}

//+------------------------------------------------------------------+
//| Timer handler for position management and EOD checks             |
//+------------------------------------------------------------------+
void OnTimer()
{
   g_risk.OnNewDayCheck();
   SSessionStatus sess = g_session.Evaluate(g_cfg);
   if(sess.shouldCloseEod)
      g_positions.CloseAllManagedPositions("Friday/EOD session close");
}

//+------------------------------------------------------------------+
//| Track closed trade profit for consecutive loss protection        |
//+------------------------------------------------------------------+
void OnTradeTransaction(const MqlTradeTransaction &trans,
                        const MqlTradeRequest &request,
                        const MqlTradeResult &result)
{
   if(trans.type == TRADE_TRANSACTION_DEAL_ADD && trans.symbol == g_symbol)
   {
      if(HistoryDealSelect(trans.deal))
      {
         long entry = HistoryDealGetInteger(trans.deal, DEAL_ENTRY);
         ulong magic = (ulong)HistoryDealGetInteger(trans.deal, DEAL_MAGIC);
         if(magic == g_cfg.magicNumber && entry == DEAL_ENTRY_OUT)
         {
            double profit = HistoryDealGetDouble(trans.deal, DEAL_PROFIT) +
                            HistoryDealGetDouble(trans.deal, DEAL_SWAP) +
                            HistoryDealGetDouble(trans.deal, DEAL_COMMISSION);
            g_risk.RecordTradeClosed(profit);
         }
      }
   }
}

//+------------------------------------------------------------------+
//| Expert tick function                                             |
//+------------------------------------------------------------------+
void OnTick()
{
   string freshReason;
   if(!g_safety.IsMarketDataFresh(g_symbol, 120, freshReason))
      return;

   datetime currentBarTime = iTime(g_symbol, g_cfg.entryTimeframe, 0);
   if(currentBarTime == 0 || currentBarTime == g_lastBarTime)
      return;
   g_lastBarTime = currentBarTime;

   // 1. Market Data & Technical Analysis (completed candle shift=1)
   SMarketSnapshot snap;
   if(!g_market.AnalyzeCompletedBar(g_cfg, snap))
      return;

   // Manage open positions using latest ATR
   g_positions.ManageOpenPositions(snap.atr14, g_cfg);

   // 2. Strategy Signal
   SStrategySignal sig = g_strategy.Evaluate(snap, g_cfg);

   // 3. Session Filter
   SSessionStatus sess = g_session.Evaluate(g_cfg);
   if(!sess.tradingAllowed && sig.signal != SIGNAL_WAIT)
   {
      sig.signal = SIGNAL_WAIT;
      sig.rejectionReason = sess.reason;
   }

   // 4. News Filter
   SNewsStatus news = g_news.CheckStatus(g_cfg);
   if(news.inBlackout && sig.signal != SIGNAL_WAIT)
   {
      sig.signal = SIGNAL_WAIT;
      sig.rejectionReason = news.reason;
   }

   // 5. AI Filter
   SAiPrediction ai = g_ai.RequestPrediction(snap, g_cfg);
   if(g_cfg.enableAiFilter && sig.signal != SIGNAL_WAIT)
   {
      if(!ai.available && g_cfg.requireAiConfirmation)
      {
         sig.signal = SIGNAL_WAIT;
         sig.rejectionReason = "AI confirmation required but model unavailable.";
      }
      else if(ai.available && ai.recommendedSignal != sig.signal && g_cfg.requireAiConfirmation)
      {
         sig.signal = SIGNAL_WAIT;
         sig.rejectionReason = "AI filter disagreed: " + ai.reason;
      }
   }

   // 6. Risk Validation & Demo Order Execution + Logging
   string execStatus = "WAIT";
   if(sig.signal != SIGNAL_WAIT)
      g_trade.ExecuteSignal(sig.signal, snap.barTime, sig.strategyName, g_cfg, g_safety, g_risk, g_positions, snap.atr14, execStatus);
   else
      execStatus = (StringLen(sig.rejectionReason) > 0) ? sig.rejectionReason : "WAIT";

   g_lastAction = execStatus;
   g_logger.Info("Pipeline", StringFormat("Bar=%s Signal=%d Score=%d Status=%s",
                 TimeToString(snap.barTime, TIME_DATE | TIME_MINUTES), sig.signal, sig.score, execStatus));

   g_dashboard.Render(g_cfg, snap, sig, sess, news, ai, g_risk, g_positions.CountOpenPositions(), g_lastAction);
}
//+------------------------------------------------------------------+

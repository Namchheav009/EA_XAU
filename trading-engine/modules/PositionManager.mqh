//+------------------------------------------------------------------+
//|                                              PositionManager.mqh |
//|                                    GoldAITrader Position Manager |
//|  Position tracking, break-even, ATR trailing, partial close, EOD |
//|  Safe handling for both Hedging and Netting account modes        |
//+------------------------------------------------------------------+
#property copyright "GoldAITrader"
#property strict

#include <Trade/Trade.mqh>
#include "Config.mqh"
#include "Logger.mqh"

class CPositionManager
{
private:
   string   m_symbol;
   ulong    m_magic;
   CTrade   m_trade;
   CLogger *m_logger;

   bool IsManagedPosition(const int index) const
   {
      ulong ticket = PositionGetTicket(index);
      if(ticket == 0) return false;
      if(PositionGetString(POSITION_SYMBOL) != m_symbol) return false;
      if((ulong)PositionGetInteger(POSITION_MAGIC) != m_magic) return false;
      return true;
   }

public:
   CPositionManager() : m_symbol(""), m_magic(0), m_logger(NULL) {}

   void Init(const string symbol, const ulong magic, const int slippagePts, CLogger *logger)
   {
      m_symbol = symbol;
      m_magic  = magic;
      m_logger = logger;
      m_trade.SetExpertMagicNumber(magic);
      m_trade.SetDeviationInPoints(slippagePts);
   }

   int CountOpenPositions() const
   {
      int count = 0;
      for(int i = PositionsTotal() - 1; i >= 0; i--)
      {
         if(IsManagedPosition(i))
            count++;
      }
      return count;
   }

   void ManageOpenPositions(const double atrValue, const STraderConfig &cfg)
   {
      int digits    = (int)SymbolInfoInteger(m_symbol, SYMBOL_DIGITS);
      double volMin = SymbolInfoDouble(m_symbol, SYMBOL_VOLUME_MIN);
      double volStep= SymbolInfoDouble(m_symbol, SYMBOL_VOLUME_STEP);

      for(int i = PositionsTotal() - 1; i >= 0; i--)
      {
         if(!IsManagedPosition(i)) continue;

         ulong  ticket   = PositionGetTicket(i);
         long   posType  = PositionGetInteger(POSITION_TYPE);
         double openPrc  = PositionGetDouble(POSITION_PRICE_OPEN);
         double sl       = PositionGetDouble(POSITION_SL);
         double tp       = PositionGetDouble(POSITION_TP);
         double vol      = PositionGetDouble(POSITION_VOLUME);
         double curPrice = (posType == POSITION_TYPE_BUY) ? SymbolInfoDouble(m_symbol, SYMBOL_BID) : SymbolInfoDouble(m_symbol, SYMBOL_ASK);

         double initialRisk = (sl > 0.0) ? MathAbs(openPrc - sl) : (atrValue * cfg.atrStopMultiplier);
         if(initialRisk <= 0.0) continue;

         double profitDist = (posType == POSITION_TYPE_BUY) ? (curPrice - openPrc) : (openPrc - curPrice);
         double currentRR  = profitDist / initialRisk;

         // 1. Break-even management
         if(cfg.useBreakEven && currentRR >= cfg.breakEvenTriggerRR)
         {
            double bePrice = NormalizeDouble(openPrc, digits);
            bool needsBe = (posType == POSITION_TYPE_BUY && (sl < bePrice || sl == 0.0)) ||
                           (posType == POSITION_TYPE_SELL && (sl > bePrice || sl == 0.0));
            if(needsBe)
            {
               if(m_trade.PositionModify(ticket, bePrice, tp) && m_logger != NULL)
                  m_logger.Info("PositionManager", StringFormat("Moved ticket %I64u to Break-Even at %.2f", ticket, bePrice));
            }
         }

         // 2. Partial close with volume validation
         if(cfg.usePartialClose && currentRR >= cfg.partialCloseTriggerRR && vol > volMin)
         {
            double closeVol = MathFloor((vol * cfg.partialCloseRatio) / volStep) * volStep;
            closeVol = NormalizeDouble(closeVol, 2);
            if(closeVol >= volMin && (vol - closeVol) >= volMin)
            {
               if(m_trade.PositionClosePartial(ticket, closeVol) && m_logger != NULL)
                  m_logger.Info("PositionManager", StringFormat("Partial close %.2f lots on ticket %I64u", closeVol, ticket));
            }
         }

         // 3. ATR-based trailing stop
         if(cfg.useAtrTrailing && atrValue > 0.0 && currentRR >= 1.0)
         {
            double trailDist = atrValue * cfg.atrTrailMultiplier;
            double newSl = (posType == POSITION_TYPE_BUY)
                           ? NormalizeDouble(curPrice - trailDist, digits)
                           : NormalizeDouble(curPrice + trailDist, digits);

            bool improves = (posType == POSITION_TYPE_BUY && newSl > sl + _Point * 10) ||
                            (posType == POSITION_TYPE_SELL && (sl == 0.0 || newSl < sl - _Point * 10));
            if(improves)
               m_trade.PositionModify(ticket, newSl, tp);
         }
      }
   }

   void CloseAllManagedPositions(const string reason)
   {
      for(int i = PositionsTotal() - 1; i >= 0; i--)
      {
         if(!IsManagedPosition(i)) continue;
         ulong ticket = PositionGetTicket(i);
         if(m_trade.PositionClose(ticket))
         {
            if(m_logger != NULL)
               m_logger.Info("PositionManager", StringFormat("Closed ticket %I64u: %s", ticket, reason));
         }
      }
   }
};
//+------------------------------------------------------------------+

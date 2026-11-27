//+------------------------------------------------------------------+
//|                                                SessionFilter.mqh |
//|                                    GoldAITrader Session Filter   |
//|  Asian, London, New York & overlap sessions, UTC/DST handling,   |
//|  weekend & Friday closing protection                             |
//+------------------------------------------------------------------+
#property copyright "GoldAITrader"
#property strict

#include "Config.mqh"

struct SSessionStatus
{
   bool   tradingAllowed;
   bool   shouldCloseEod;
   string activeSession;
   string reason;
};

class CSessionFilter
{
private:
   bool IsUsDst(const MqlDateTime &utcDt) const
   {
      if(utcDt.mon > 3 && utcDt.mon < 11) return true;
      if(utcDt.mon < 3 || utcDt.mon > 11) return false;
      int firstSun = (7 - (utcDt.day_of_week - (utcDt.day - 1) % 7 + 7) % 7) % 7 + 1;
      if(utcDt.mon == 3)  return utcDt.day >= (firstSun + 7);
      return utcDt.day < firstSun;
   }

public:
   SSessionStatus Evaluate(const STraderConfig &cfg) const
   {
      SSessionStatus st;
      st.tradingAllowed = false;
      st.shouldCloseEod = false;
      st.activeSession  = "NONE";
      st.reason         = "";

      datetime utcNow = TimeGMT();
      MqlDateTime dt;
      TimeToStruct(utcNow, dt);

      if(cfg.useDstAdjustment && IsUsDst(dt))
      {
         // NY session shifts 1h earlier in UTC during US DST
      }

      // Weekend protection
      if(dt.day_of_week == 0 || dt.day_of_week == 6)
      {
         st.reason = "Weekend protection active.";
         return st;
      }

      // Friday close protection
      if(cfg.closeBeforeWeekend && dt.day_of_week == 5 && dt.hour >= cfg.fridayCloseHourUtc)
      {
         st.shouldCloseEod = true;
         st.reason = StringFormat("Friday closing protection active (>= %02d:00 UTC).", cfg.fridayCloseHourUtc);
         return st;
      }

      if(!cfg.enableSessionFilter)
      {
         st.tradingAllowed = true;
         st.activeSession  = "ALL";
         st.reason         = "Session filter disabled.";
         return st;
      }

      int h = dt.hour;
      bool inAsian   = (h >= 0 && h < 8);
      bool inLondon  = (h >= 7 && h < 16);
      bool inNewYork = (h >= 12 && h < 21);
      bool inOverlap = (h >= 12 && h < 16);

      if(inOverlap)       st.activeSession = "LONDON_NY_OVERLAP";
      else if(inLondon)   st.activeSession = "LONDON";
      else if(inNewYork)  st.activeSession = "NEW_YORK";
      else if(inAsian)    st.activeSession = "ASIAN";
      else                st.activeSession = "OFF_HOURS";

      if((inAsian && cfg.allowAsianSession) ||
         (inLondon && cfg.allowLondonSession) ||
         (inNewYork && cfg.allowNewYorkSession))
      {
         st.tradingAllowed = true;
         st.reason = "Active session permitted: " + st.activeSession;
      }
      else
      {
         st.reason = "Session not permitted: " + st.activeSession;
      }

      return st;
   }
};
//+------------------------------------------------------------------+

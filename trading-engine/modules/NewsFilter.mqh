//+------------------------------------------------------------------+
//|                                                   NewsFilter.mqh |
//|                                    GoldAITrader News Filter      |
//|  MT5 Economic Calendar USD high-impact detection + CSV fallback  |
//|  for backtesting; fail-safe when calendar is unavailable         |
//+------------------------------------------------------------------+
#property copyright "GoldAITrader"
#property strict

#include "Config.mqh"
#include "Logger.mqh"

struct SNewsStatus
{
   bool   inBlackout;
   bool   calendarAvailable;
   string activeEvent;
   string reason;
};

class CNewsFilter
{
private:
   CLogger *m_logger;

   bool IsHighImpactUsdEvent(const MqlCalendarEvent &evt, const MqlCalendarCountry &country) const
   {
      if(country.currency != "USD")
         return false;
      if(evt.importance == CALENDAR_IMPORTANCE_HIGH)
         return true;
      string nameUpper = evt.name;
      StringToUpper(nameUpper);
      return (StringFind(nameUpper, "CPI") >= 0 ||
              StringFind(nameUpper, "NONFARM") >= 0 ||
              StringFind(nameUpper, "NFP") >= 0 ||
              StringFind(nameUpper, "FOMC") >= 0 ||
              StringFind(nameUpper, "INTEREST RATE") >= 0);
   }

   bool CheckCsvFallback(const string csvFile, const int beforeMin, const int afterMin, SNewsStatus &status) const
   {
      if(StringLen(csvFile) == 0 || !FileIsExist(csvFile))
         return false;

      int handle = FileOpen(csvFile, FILE_READ | FILE_CSV | FILE_ANSI, ',');
      if(handle == INVALID_HANDLE)
         return false;

      datetime nowGmt = TimeGMT();
      while(!FileIsEnding(handle))
      {
         string tsStr    = FileReadString(handle);
         string currency = FileReadString(handle);
         string impact   = FileReadString(handle);
         string title    = FileReadString(handle);

         if(tsStr == "timestamp_utc" || StringLen(tsStr) == 0)
            continue;

         if(currency == "USD" && impact == "HIGH")
         {
            datetime evtTime = StringToTime(tsStr);
            if(nowGmt >= (evtTime - beforeMin * 60) && nowGmt <= (evtTime + afterMin * 60))
            {
               status.inBlackout = true;
               status.calendarAvailable = true;
               status.activeEvent = title;
               status.reason = "Historical CSV USD high-impact news blackout: " + title;
               FileClose(handle);
               return true;
            }
         }
      }
      FileClose(handle);
      status.calendarAvailable = true;
      status.inBlackout = false;
      status.reason = "No CSV news blackout active.";
      return true;
   }

public:
   CNewsFilter() : m_logger(NULL) {}

   void Init(CLogger *logger) { m_logger = logger; }

   SNewsStatus CheckStatus(const STraderConfig &cfg) const
   {
      SNewsStatus status;
      status.inBlackout        = false;
      status.calendarAvailable = false;
      status.activeEvent       = "";
      status.reason            = "";

      if(!cfg.enableNewsFilter)
      {
         status.calendarAvailable = true;
         status.reason = "News filter disabled by config.";
         return status;
      }

      if(MQLInfoInteger(MQL_TESTER))
      {
         if(CheckCsvFallback(cfg.newsCsvFileName, cfg.newsBlackoutBeforeMin, cfg.newsBlackoutAfterMin, status))
            return status;
         status.calendarAvailable = false;
         status.inBlackout = false;
         status.reason = "Tester mode without CSV news file; continuing with caution.";
         return status;
      }

      datetime nowServer = TimeTradeServer();
      datetime fromTime  = nowServer - cfg.newsBlackoutAfterMin * 60;
      datetime toTime    = nowServer + cfg.newsBlackoutBeforeMin * 60;

      MqlCalendarValue values[];
      ResetLastError();
      int count = CalendarValueHistory(values, fromTime, toTime, NULL, "USD");
      if(count < 0)
      {
         // Fail-safe: block new entries when live calendar is unavailable
         status.calendarAvailable = false;
         status.inBlackout        = true;
         status.reason            = StringFormat("Fail-safe blackout: MT5 calendar unavailable (err=%d).", GetLastError());
         return status;
      }

      status.calendarAvailable = true;
      for(int i = 0; i < count; i++)
      {
         MqlCalendarEvent evt;
         MqlCalendarCountry country;
         if(CalendarEventById(values[i].event_id, evt) && CalendarCountryById(evt.country_id, country))
         {
            if(IsHighImpactUsdEvent(evt, country))
            {
               status.inBlackout  = true;
               status.activeEvent = evt.name;
               status.reason      = "USD High-Impact News Blackout: " + evt.name;
               return status;
            }
         }
      }

      status.reason = "No USD high-impact news in blackout window.";
      return status;
   }
};
//+------------------------------------------------------------------+

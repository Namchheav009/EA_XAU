//+------------------------------------------------------------------+
//|                                                     AIClient.mqh |
//|                                    GoldAITrader AI HTTP Client   |
//|  Queries Python FastAPI /api/v1/ai/predict via WebRequest        |
//|  Fail-safe: returns WAIT when AI service is unavailable          |
//+------------------------------------------------------------------+
#property copyright "GoldAITrader"
#property strict

#include "Config.mqh"
#include "MarketAnalysis.mqh"
#include "Logger.mqh"

struct SAiPrediction
{
   bool             available;
   ENUM_SIGNAL_TYPE recommendedSignal;
   double           buyProb;
   double           sellProb;
   double           waitProb;
   double           confidence;
   string           modelVersion;
   string           marketRegime;
   string           reason;
};

class CAiClient
{
private:
   CLogger *m_logger;

   double ExtractJsonDouble(const string json, const string key, const double defaultVal) const
   {
      string pattern = "\"" + key + "\":";
      int pos = StringFind(json, pattern);
      if(pos < 0) return defaultVal;
      int start = pos + StringLen(pattern);
      while(start < StringLen(json) && (StringGetCharacter(json, start) == ' '))
         start++;
      string numStr = "";
      for(int i = start; i < StringLen(json); i++)
      {
         ushort c = StringGetCharacter(json, i);
         if((c >= '0' && c <= '9') || c == '.' || c == '-')
            numStr += ShortToString(c);
         else
            break;
      }
      return (StringLen(numStr) > 0) ? StringToDouble(numStr) : defaultVal;
   }

   string ExtractJsonString(const string json, const string key, const string defaultVal) const
   {
      string pattern = "\"" + key + "\":\"";
      int pos = StringFind(json, pattern);
      if(pos < 0) return defaultVal;
      int start = pos + StringLen(pattern);
      int end   = StringFind(json, "\"", start);
      if(end < 0) return defaultVal;
      return StringSubstr(json, start, end - start);
   }

public:
   CAiClient() : m_logger(NULL) {}
   void Init(CLogger *logger) { m_logger = logger; }

   SAiPrediction RequestPrediction(const SMarketSnapshot &snap, const STraderConfig &cfg) const
   {
      SAiPrediction res;
      res.available         = false;
      res.recommendedSignal = SIGNAL_WAIT;
      res.buyProb           = 0.0;
      res.sellProb          = 0.0;
      res.waitProb          = 1.0;
      res.confidence        = 0.0;
      res.modelVersion      = "unavailable";
      res.marketRegime      = "UNKNOWN";
      res.reason            = "";

      if(!cfg.enableAiFilter)
      {
         res.available = true;
         res.reason    = "AI filter disabled in config.";
         return res;
      }

      if(MQLInfoInteger(MQL_TESTER))
      {
         res.reason = "WebRequest unavailable in Strategy Tester; AI filter bypassed/WAIT.";
         return res;
      }

      string url = cfg.aiServiceUrl + "/api/v1/ai/predict";
      string payload = StringFormat(
         "{\"symbol\":\"%s\",\"timeframe\":\"M15\",\"features\":{\"ema_20\":%.5f,\"ema_50\":%.5f,\"ema_200\":%.5f,\"rsi_14\":%.2f,\"atr_14\":%.5f,\"macd_main\":%.5f,\"macd_signal\":%.5f,\"adx_14\":%.2f,\"close\":%.5f}}",
         snap.symbol, snap.ema20, snap.ema50, snap.ema200, snap.rsi14, snap.atr14,
         snap.macdMain, snap.macdSignal, snap.adx14, snap.closePrice
      );

      char postData[];
      char resultData[];
      string resultHeaders;
      StringToCharArray(payload, postData, 0, StringLen(payload));

      ResetLastError();
      int httpCode = WebRequest("POST", url, "Content-Type: application/json\r\n", cfg.aiTimeoutMs, postData, resultData, resultHeaders);
      if(httpCode != 200)
      {
         res.reason = StringFormat("AI service HTTP=%d err=%d", httpCode, GetLastError());
         return res;
      }

      string body = CharArrayToString(resultData);
      string availStr = ExtractJsonString(body, "status", "unavailable");
      res.available    = (availStr == "available" || StringFind(body, "\"model_available\":true") >= 0);
      res.buyProb      = ExtractJsonDouble(body, "buy_probability", 0.0);
      res.sellProb     = ExtractJsonDouble(body, "sell_probability", 0.0);
      res.waitProb     = ExtractJsonDouble(body, "wait_probability", 1.0);
      res.confidence   = ExtractJsonDouble(body, "confidence", 0.0);
      res.modelVersion = ExtractJsonString(body, "model_version", "unknown");
      res.marketRegime = ExtractJsonString(body, "market_regime", "UNKNOWN");

      if(!res.available)
      {
         res.recommendedSignal = SIGNAL_WAIT;
         res.reason = "AI model unavailable or stale.";
         return res;
      }

      if(res.confidence >= cfg.aiMinConfidence)
      {
         if(res.buyProb > res.sellProb && res.buyProb > res.waitProb)
            res.recommendedSignal = SIGNAL_BUY;
         else if(res.sellProb > res.buyProb && res.sellProb > res.waitProb)
            res.recommendedSignal = SIGNAL_SELL;
      }
      res.reason = StringFormat("AI %s conf=%.2f (B:%.2f S:%.2f W:%.2f)", res.modelVersion, res.confidence, res.buyProb, res.sellProb, res.waitProb);
      return res;
   }
};
//+------------------------------------------------------------------+

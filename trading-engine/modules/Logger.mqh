//+------------------------------------------------------------------+
//|                                                       Logger.mqh |
//|                                    GoldAITrader Audit Logger     |
//|         Structured console and CSV/file logging for MQL5 EA      |
//+------------------------------------------------------------------+
#property copyright "GoldAITrader"
#property strict

enum ENUM_LOG_LEVEL
{
   LOG_DEBUG = 0,
   LOG_INFO  = 1,
   LOG_WARN  = 2,
   LOG_ERROR = 3
};

class CLogger
{
private:
   ENUM_LOG_LEVEL m_minLevel;
   string         m_logFile;
   bool           m_writeToFile;

   string LevelToString(const ENUM_LOG_LEVEL level) const
   {
      switch(level)
      {
         case LOG_DEBUG: return "DEBUG";
         case LOG_INFO:  return "INFO";
         case LOG_WARN:  return "WARN";
         case LOG_ERROR: return "ERROR";
      }
      return "INFO";
   }

public:
   CLogger() : m_minLevel(LOG_INFO), m_logFile("GoldAITrader_audit.log"), m_writeToFile(true) {}

   void Init(const ENUM_LOG_LEVEL minLevel = LOG_INFO, const string logFile = "GoldAITrader_audit.log", const bool writeToFile = true)
   {
      m_minLevel    = minLevel;
      m_logFile     = logFile;
      m_writeToFile = writeToFile;
   }

   void Log(const ENUM_LOG_LEVEL level, const string moduleName, const string message)
   {
      if(level < m_minLevel)
         return;

      string ts = TimeToString(TimeGMT(), TIME_DATE | TIME_SECONDS);
      string line = StringFormat("[%s UTC] [%s] [%s] %s", ts, LevelToString(level), moduleName, message);
      Print(line);

      if(m_writeToFile)
      {
         int handle = FileOpen(m_logFile, FILE_READ | FILE_WRITE | FILE_TXT | FILE_ANSI | FILE_SHARE_READ | FILE_SHARE_WRITE);
         if(handle != INVALID_HANDLE)
         {
            FileSeek(handle, 0, SEEK_END);
            FileWriteString(handle, line + "\r\n");
            FileClose(handle);
         }
      }
   }

   void Info(const string moduleName, const string message)  { Log(LOG_INFO, moduleName, message); }
   void Warn(const string moduleName, const string message)  { Log(LOG_WARN, moduleName, message); }
   void Error(const string moduleName, const string message) { Log(LOG_ERROR, moduleName, message); }
   void Debug(const string moduleName, const string message) { Log(LOG_DEBUG, moduleName, message); }
};
//+------------------------------------------------------------------+

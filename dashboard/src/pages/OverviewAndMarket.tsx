import { useEffect, useState } from 'react';
import { apiGet } from '../api/client';
import { CandlestickChart, CandlePoint } from '../components/CandlestickChart';
import { MetricCard, Panel, StatusBadge } from '../components/UI';

export function OverviewPage() {
  const [sys, setSys] = useState<any>(null);
  const [acct, setAcct] = useState<any>(null);
  const [perf, setPerf] = useState<any>(null);
  const [ai, setAi] = useState<any>(null);
  const [positions, setPositions] = useState<any[]>([]);
  const [error, setError] = useState('');

  useEffect(() => {
    Promise.all([
      apiGet('/api/v1/system/status'),
      apiGet('/api/v1/mt5/account'),
      apiGet('/api/v1/trading/performance'),
      apiGet('/api/v1/ai/status'),
      apiGet('/api/v1/trading/positions'),
    ])
      .then(([s, a, p, m, pos]: any[]) => {
        setSys(s);
        setAcct(a);
        setPerf(p);
        setAi(m);
        setPositions(pos.positions || []);
      })
      .catch((e) => setError(e.message));
  }, []);

  if (error) return <div className="text-rose-400 p-4">Error loading overview: {error}</div>;
  if (!sys || !acct) return <div className="text-slate-400 p-4">Loading terminal overview...</div>;

  const curr = acct.currency || 'USC';
  const modeLabel = acct.is_mock ? 'MOCK' : acct.trade_mode || 'DEMO';

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center gap-2">
        <StatusBadge label={`MODE: ${modeLabel}`} tone={acct.is_mock ? 'amber' : 'green'} />
        <StatusBadge label={`ENGINE: ${sys.operating_mode}`} tone="gold" />
        <StatusBadge label={`MT5: ${sys.connector?.connected ? 'CONNECTED' : 'DISCONNECTED'}`} tone={sys.connector?.connected ? 'green' : 'red'} />
        <StatusBadge label={`AI: ${ai?.model_available ? ai.model_version : 'UNAVAILABLE (WAIT)'}`} tone={ai?.model_available ? 'green' : 'amber'} />
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <MetricCard title="Account Balance" value={`${acct.balance} ${curr}`} sub={`${acct.account_type} Account`} accent="gold" />
        <MetricCard title="Equity" value={`${acct.equity} ${curr}`} sub={`Free Margin: ${acct.margin_free} ${curr}`} />
        <MetricCard title="Net PnL" value={`${perf?.net_pnl ?? 0} ${curr}`} sub={`Win Rate: ${perf?.win_rate_pct ?? 0}%`} accent={(perf?.net_pnl ?? 0) >= 0 ? 'green' : 'red'} />
        <MetricCard title="Profit Factor" value={`${perf?.profit_factor ?? 0}`} sub={`Open Positions: ${positions.length}`} />
      </div>

      <Panel title="System & Safety Summary">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm text-slate-300">
          <div>
            <span className="text-slate-400">Broker:</span> Exness ({acct.server})
          </div>
          <div>
            <span className="text-slate-400">Emergency Stop:</span>{' '}
            <span className={sys.emergency_stop ? 'text-rose-400 font-semibold' : 'text-emerald-400'}>
              {sys.emergency_stop ? 'ACTIVE' : 'CLEAR'}
            </span>
          </div>
          <div>
            <span className="text-slate-400">Data Source:</span> {sys.data_mode}
          </div>
        </div>
      </Panel>
    </div>
  );
}

export function MarketAnalysisPage() {
  const [timeframe, setTimeframe] = useState('M15');
  const [candles, setCandles] = useState<CandlePoint[]>([]);
  const [analysis, setAnalysis] = useState<any>(null);
  const [price, setPrice] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    Promise.all([
      apiGet<{ candles: CandlePoint[] }>(`/api/v1/market/candles?symbol=XAUUSDc&timeframe=${timeframe}&count=150`),
      apiGet(`/api/v1/market/analysis?symbol=XAUUSDc&timeframe=${timeframe}`),
      apiGet('/api/v1/market/price?symbol=XAUUSDc'),
    ])
      .then(([c, a, p]) => {
        setCandles(c.candles || []);
        setAnalysis(a);
        setPrice(p);
      })
      .finally(() => setLoading(false));
  }, [timeframe]);

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <div className="flex items-center gap-2">
          {['M5', 'M15', 'M30', 'H1', 'H4'].map((tf) => (
            <button
              key={tf}
              onClick={() => setTimeframe(tf)}
              className={`px-3 py-1.5 rounded-lg text-xs font-medium border ${
                timeframe === tf
                  ? 'bg-amber-500 text-slate-950 border-amber-400'
                  : 'bg-slate-900 text-slate-300 border-slate-700 hover:border-slate-500'
              }`}
            >
              {tf}
            </button>
          ))}
        </div>
        {price && (
          <div className="text-sm text-slate-300">
            XAUUSDc Bid: <span className="text-amber-400 font-semibold">{price.bid}</span> | Ask:{' '}
            <span className="text-amber-400 font-semibold">{price.ask}</span>
            {price.is_mock && <span className="ml-2 text-xs text-yellow-400">(MOCK)</span>}
          </div>
        )}
      </div>

      <Panel title={`XAUUSDc (${timeframe}) Candlestick Chart`}>
        {loading ? (
          <div className="h-[360px] flex items-center justify-center text-slate-400">Loading chart...</div>
        ) : (
          <CandlestickChart
            candles={candles}
            support={analysis?.analysis?.support_resistance?.nearest_support}
            resistance={analysis?.analysis?.support_resistance?.nearest_resistance}
          />
        )}
      </Panel>

      {analysis && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <Panel title="Technical Indicators & Regime">
            <div className="grid grid-cols-2 gap-2 text-sm text-slate-300">
              <div>EMA 20 / 50: {analysis.analysis.ema_20} / {analysis.analysis.ema_50}</div>
              <div>EMA 200: {analysis.analysis.ema_200}</div>
              <div>RSI (14): {analysis.analysis.rsi_14}</div>
              <div>ATR (14): {analysis.analysis.atr_14}</div>
              <div>MACD: {analysis.analysis.macd_main}</div>
              <div>ADX (14): {analysis.analysis.adx_14}</div>
              <div>Trend: {analysis.analysis.trend_direction}</div>
              <div>Regime: {analysis.market_regime}</div>
            </div>
          </Panel>
          <Panel title="Strategy Signal & Explanation">
            <div className="space-y-2 text-sm">
              <div className="flex items-center gap-2">
                <StatusBadge
                  label={`${analysis.signal} (${analysis.score}/100)`}
                  tone={analysis.signal === 'BUY' ? 'green' : analysis.signal === 'SELL' ? 'red' : 'amber'}
                />
                <span className="text-slate-400">{analysis.strategy_name}</span>
              </div>
              <div className="text-slate-300">
                {(analysis.reasons || []).map((r: string, i: number) => (
                  <div key={i}>• {r}</div>
                ))}
                {(analysis.rejection_reasons || []).map((r: string, i: number) => (
                  <div key={i} className="text-amber-400">• {r}</div>
                ))}
              </div>
            </div>
          </Panel>
        </div>
      )}
    </div>
  );
}

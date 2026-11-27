import { useEffect, useState } from 'react';
import { apiGet, apiPost } from '../api/client';
import { MetricCard, Panel, StatusBadge } from '../components/UI';

export function RiskManagementPage() {
  const [riskStatus, setRiskStatus] = useState<any>(null);
  const [equity, setEquity] = useState(10000);
  const [currency, setCurrency] = useState('USC');
  const [atr, setAtr] = useState(3.5);
  const [riskPct, setRiskPct] = useState(0.5);
  const [calcResult, setCalcResult] = useState<any>(null);

  useEffect(() => {
    apiGet('/api/v1/risk/status').then(setRiskStatus);
  }, []);

  const handleCalculate = async () => {
    const res = await apiPost('/api/v1/risk/calculate', {
      equity,
      account_currency: currency,
      entry_price: 2650,
      atr_14: atr,
      risk_percent: riskPct,
    });
    setCalcResult(res);
  };

  return (
    <div className="space-y-4">
      {riskStatus && (
        <div className="grid grid-cols-1 sm:grid-cols-4 gap-4">
          <MetricCard title="Risk / Trade" value={`${riskStatus.risk_percent_per_trade}%`} accent="gold" />
          <MetricCard title="Daily Loss Limit" value={`${riskStatus.max_daily_loss_percent}%`} />
          <MetricCard title="Max Drawdown" value={`${riskStatus.max_drawdown_percent}%`} />
          <MetricCard
            title="Emergency Stop"
            value={riskStatus.emergency_stop ? 'ACTIVE' : 'CLEAR'}
            accent={riskStatus.emergency_stop ? 'red' : 'green'}
          />
        </div>
      )}

      <Panel title="Cent / Standard Lot & Risk Calculator">
        <div className="grid grid-cols-1 sm:grid-cols-4 gap-3 mb-4 text-sm">
          <label className="block">
            <span className="text-slate-400 text-xs">Equity</span>
            <input type="number" value={equity} onChange={(e) => setEquity(Number(e.target.value))} className="mt-1 w-full bg-slate-800 border border-slate-700 rounded px-3 py-1.5" />
          </label>
          <label className="block">
            <span className="text-slate-400 text-xs">Currency</span>
            <select value={currency} onChange={(e) => setCurrency(e.target.value)} className="mt-1 w-full bg-slate-800 border border-slate-700 rounded px-3 py-1.5">
              <option value="USC">USC (Cent)</option>
              <option value="USD">USD (Standard)</option>
            </select>
          </label>
          <label className="block">
            <span className="text-slate-400 text-xs">ATR (14)</span>
            <input type="number" step="0.1" value={atr} onChange={(e) => setAtr(Number(e.target.value))} className="mt-1 w-full bg-slate-800 border border-slate-700 rounded px-3 py-1.5" />
          </label>
          <label className="block">
            <span className="text-slate-400 text-xs">Risk %</span>
            <input type="number" step="0.1" value={riskPct} onChange={(e) => setRiskPct(Number(e.target.value))} className="mt-1 w-full bg-slate-800 border border-slate-700 rounded px-3 py-1.5" />
          </label>
        </div>
        <button onClick={handleCalculate} className="bg-amber-500 text-slate-950 font-medium text-sm px-4 py-2 rounded-lg">
          Calculate Position Size
        </button>

        {calcResult && (
          <div className="mt-4 p-3 rounded-lg bg-slate-800/70 text-sm space-y-1">
            <div>
              Status:{' '}
              <StatusBadge label={calcResult.allowed ? 'ALLOWED' : 'REJECTED'} tone={calcResult.allowed ? 'green' : 'red'} />
            </div>
            <div>Lot Size: {calcResult.lot_size} | Planned Risk: {calcResult.planned_risk_amount} {calcResult.account_currency}</div>
            <div>SL: {calcResult.stop_loss} | TP: {calcResult.take_profit}</div>
            <div className="text-slate-400">{calcResult.reason}</div>
          </div>
        )}
      </Panel>
    </div>
  );
}

export function AIAnalysisPage() {
  const [aiStatus, setAiStatus] = useState<any>(null);
  const [prediction, setPrediction] = useState<any>(null);

  useEffect(() => {
    apiGet('/api/v1/ai/status').then(setAiStatus);
    apiPost('/api/v1/ai/predict', { symbol: 'XAUUSDc', timeframe: 'M15' }).then(setPrediction);
  }, []);

  return (
    <div className="space-y-4">
      <Panel title="Hybrid AI Model Status">
        {aiStatus ? (
          <div className="space-y-2 text-sm text-slate-300">
            <StatusBadge label={aiStatus.model_available ? `AVAILABLE (${aiStatus.model_version})` : 'UNAVAILABLE'} tone={aiStatus.model_available ? 'green' : 'amber'} />
            <div className="text-slate-400">{aiStatus.message || `Model: ${aiStatus.model_name}`}</div>
          </div>
        ) : (
          <div className="text-slate-400 text-sm">Checking AI status...</div>
        )}
      </Panel>

      {prediction && (
        <Panel title="Latest AI Filter Output">
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-sm mb-3">
            <MetricCard title="Recommended" value={prediction.recommended_signal} accent="gold" />
            <MetricCard title="BUY Prob" value={`${(prediction.buy_probability * 100).toFixed(1)}%`} />
            <MetricCard title="SELL Prob" value={`${(prediction.sell_probability * 100).toFixed(1)}%`} />
            <MetricCard title="WAIT Prob" value={`${(prediction.wait_probability * 100).toFixed(1)}%`} />
          </div>
          <div className="text-xs text-slate-400 space-y-1">
            {(prediction.reasons || []).map((r: string, i: number) => (
              <div key={i}>• {r}</div>
            ))}
          </div>
        </Panel>
      )}
    </div>
  );
}

export function BacktestingPage() {
  const [strategy, setStrategy] = useState('StrategyA_TrendPullback');
  const [capital, setCapital] = useState(10000);
  const [accountType, setAccountType] = useState('CENT');
  const [riskPct, setRiskPct] = useState(0.5);
  const [result, setResult] = useState<any>(null);
  const [running, setRunning] = useState(false);

  const runBacktest = async () => {
    setRunning(true);
    try {
      const res = await apiPost('/api/v1/backtesting/run', {
        strategy_name: strategy,
        symbol: 'XAUUSDc',
        timeframe: 'M15',
        initial_balance: capital,
        account_type: accountType,
        risk_percent: riskPct,
        bars: 350,
      });
      setResult(res);
    } finally {
      setRunning(false);
    }
  };

  return (
    <div className="space-y-4">
      <Panel title="Backtest Configuration">
        <div className="grid grid-cols-1 sm:grid-cols-4 gap-3 mb-4 text-sm">
          <label className="block">
            <span className="text-slate-400 text-xs">Strategy</span>
            <select value={strategy} onChange={(e) => setStrategy(e.target.value)} className="mt-1 w-full bg-slate-800 border border-slate-700 rounded px-3 py-1.5">
              <option value="StrategyA_TrendPullback">Strategy A: Pullback</option>
              <option value="StrategyB_Breakout">Strategy B: Breakout</option>
            </select>
          </label>
          <label className="block">
            <span className="text-slate-400 text-xs">Initial Capital</span>
            <input type="number" value={capital} onChange={(e) => setCapital(Number(e.target.value))} className="mt-1 w-full bg-slate-800 border border-slate-700 rounded px-3 py-1.5" />
          </label>
          <label className="block">
            <span className="text-slate-400 text-xs">Account Type</span>
            <select value={accountType} onChange={(e) => setAccountType(e.target.value)} className="mt-1 w-full bg-slate-800 border border-slate-700 rounded px-3 py-1.5">
              <option value="CENT">CENT (USC)</option>
              <option value="STANDARD">STANDARD (USD)</option>
            </select>
          </label>
          <label className="block">
            <span className="text-slate-400 text-xs">Risk %</span>
            <input type="number" step="0.1" value={riskPct} onChange={(e) => setRiskPct(Number(e.target.value))} className="mt-1 w-full bg-slate-800 border border-slate-700 rounded px-3 py-1.5" />
          </label>
        </div>
        <button onClick={runBacktest} disabled={running} className="bg-amber-500 text-slate-950 font-medium text-sm px-4 py-2 rounded-lg disabled:opacity-50">
          {running ? 'Running Backtest...' : 'Start Backtest'}
        </button>
      </Panel>

      {result && (
        <Panel title="Backtest Results">
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mb-3">
            <MetricCard title="Final Balance" value={`${result.final_balance} ${result.currency}`} accent="gold" />
            <MetricCard title="Net Profit" value={`${result.net_profit} ${result.currency}`} accent={result.net_profit >= 0 ? 'green' : 'red'} />
            <MetricCard title="Win Rate" value={`${result.win_rate_pct}%`} sub={`Trades: ${result.total_trades}`} />
            <MetricCard title="Max Drawdown" value={`${result.max_drawdown_pct}%`} sub={`Sharpe: ${result.sharpe_ratio}`} />
          </div>
          <div className="text-xs text-slate-400">{result.limitations_note}</div>
        </Panel>
      )}
    </div>
  );
}

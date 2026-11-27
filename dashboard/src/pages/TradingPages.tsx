import { useEffect, useState } from 'react';
import { apiGet } from '../api/client';
import { Panel, StatusBadge } from '../components/UI';

export function TradingSignalsPage() {
  const [data, setData] = useState<any>(null);

  useEffect(() => {
    apiGet('/api/v1/trading/signals?symbol=XAUUSDc').then(setData);
  }, []);

  if (!data) return <div className="text-slate-400 p-4">Loading signals...</div>;
  const cur = data.current_signal;

  return (
    <div className="space-y-4">
      <Panel title="Live Signal Evaluation">
        <div className="flex flex-wrap items-center gap-3 mb-2">
          <StatusBadge label={cur.signal} tone={cur.signal === 'BUY' ? 'green' : cur.signal === 'SELL' ? 'red' : 'amber'} />
          <span className="text-sm text-slate-300">Strategy: {cur.strategy_name}</span>
          <span className="text-sm text-slate-400">Score: {cur.score}/100</span>
          <span className="text-sm text-slate-400">Regime: {cur.market_regime}</span>
        </div>
        <div className="text-xs text-slate-400">
          {(cur.rejection_reasons || []).join(' | ') || (cur.reasons || []).join(' | ')}
        </div>
      </Panel>

      <Panel title="Signal History">
        <div className="overflow-x-auto">
          <table className="w-full text-sm text-left text-slate-300">
            <thead className="text-xs uppercase text-slate-400 border-b border-slate-800">
              <tr>
                <th className="py-2 pr-4">Time (UTC)</th>
                <th className="py-2 pr-4">Signal</th>
                <th className="py-2 pr-4">Strategy</th>
                <th className="py-2 pr-4">Score</th>
                <th className="py-2">Notes</th>
              </tr>
            </thead>
            <tbody>
              {(data.history || []).map((s: any) => (
                <tr key={s.id} className="border-b border-slate-800/60">
                  <td className="py-2 pr-4">{s.timestamp_utc.slice(0, 19)}</td>
                  <td className="py-2 pr-4">{s.signal}</td>
                  <td className="py-2 pr-4">{s.strategy_name}</td>
                  <td className="py-2 pr-4">{s.score}</td>
                  <td className="py-2 text-slate-400">{s.rejection_reason || s.reasons}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Panel>
    </div>
  );
}

export function PositionsPage() {
  const [positions, setPositions] = useState<any[]>([]);

  useEffect(() => {
    apiGet<{ positions: any[] }>('/api/v1/trading/positions').then((d) => setPositions(d.positions || []));
  }, []);

  return (
    <Panel title="Open Positions">
      {positions.length === 0 ? (
        <div className="text-slate-400 text-sm py-4">No open positions.</div>
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full text-sm text-left text-slate-300">
            <thead className="text-xs uppercase text-slate-400 border-b border-slate-800">
              <tr>
                <th className="py-2 pr-3">Ticket</th>
                <th className="py-2 pr-3">Symbol</th>
                <th className="py-2 pr-3">Side</th>
                <th className="py-2 pr-3">Vol</th>
                <th className="py-2 pr-3">Entry</th>
                <th className="py-2 pr-3">Current</th>
                <th className="py-2 pr-3">SL / TP</th>
                <th className="py-2">Floating PnL</th>
              </tr>
            </thead>
            <tbody>
              {positions.map((p) => (
                <tr key={p.id} className="border-b border-slate-800/60">
                  <td className="py-2 pr-3">{p.ticket}</td>
                  <td className="py-2 pr-3">{p.symbol}</td>
                  <td className="py-2 pr-3">{p.side}</td>
                  <td className="py-2 pr-3">{p.volume}</td>
                  <td className="py-2 pr-3">{p.entry_price}</td>
                  <td className="py-2 pr-3">{p.current_price}</td>
                  <td className="py-2 pr-3">{p.stop_loss} / {p.take_profit}</td>
                  <td className={`py-2 font-medium ${p.floating_pnl >= 0 ? 'text-emerald-400' : 'text-rose-400'}`}>
                    {p.floating_pnl} {p.currency}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </Panel>
  );
}

export function TradingHistoryPage() {
  const [trades, setTrades] = useState<any[]>([]);
  const [side, setSide] = useState('');
  const [outcome, setOutcome] = useState('');

  useEffect(() => {
    const params = new URLSearchParams();
    if (side) params.set('side', side);
    if (outcome) params.set('outcome', outcome);
    apiGet<{ trades: any[] }>(`/api/v1/trading/history?${params.toString()}`).then((d) => setTrades(d.trades || []));
  }, [side, outcome]);

  const exportCsv = () => {
    const header = 'ticket,symbol,side,strategy,volume,entry,exit,profit,currency,closed_at_utc\n';
    const rows = trades
      .map((t) => `${t.ticket},${t.symbol},${t.side},${t.strategy_name},${t.volume},${t.entry_price},${t.exit_price},${t.profit},${t.currency},${t.closed_at_utc}`)
      .join('\n');
    const blob = new Blob([header + rows], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'goldaitrader_history.csv';
    a.click();
  };

  return (
    <Panel
      title="Trading History"
      right={
        <div className="flex items-center gap-2">
          <select value={side} onChange={(e) => setSide(e.target.value)} className="bg-slate-800 text-xs rounded px-2 py-1 border border-slate-700">
            <option value="">All Sides</option>
            <option value="BUY">BUY</option>
            <option value="SELL">SELL</option>
          </select>
          <select value={outcome} onChange={(e) => setOutcome(e.target.value)} className="bg-slate-800 text-xs rounded px-2 py-1 border border-slate-700">
            <option value="">All Outcomes</option>
            <option value="WIN">WIN</option>
            <option value="LOSS">LOSS</option>
          </select>
          <button onClick={exportCsv} className="bg-amber-500 text-slate-950 text-xs font-medium px-3 py-1 rounded">
            Export CSV
          </button>
        </div>
      }
    >
      <div className="overflow-x-auto">
        <table className="w-full text-sm text-left text-slate-300">
          <thead className="text-xs uppercase text-slate-400 border-b border-slate-800">
            <tr>
              <th className="py-2 pr-3">Ticket</th>
              <th className="py-2 pr-3">Side</th>
              <th className="py-2 pr-3">Strategy</th>
              <th className="py-2 pr-3">Vol</th>
              <th className="py-2 pr-3">Entry / Exit</th>
              <th className="py-2 pr-3">Profit</th>
              <th className="py-2">Closed (UTC)</th>
            </tr>
          </thead>
          <tbody>
            {trades.map((t) => (
              <tr key={t.id} className="border-b border-slate-800/60">
                <td className="py-2 pr-3">{t.ticket}</td>
                <td className="py-2 pr-3">{t.side}</td>
                <td className="py-2 pr-3">{t.strategy_name}</td>
                <td className="py-2 pr-3">{t.volume}</td>
                <td className="py-2 pr-3">{t.entry_price} / {t.exit_price}</td>
                <td className={`py-2 pr-3 font-medium ${t.profit >= 0 ? 'text-emerald-400' : 'text-rose-400'}`}>
                  {t.profit} {t.currency}
                </td>
                <td className="py-2 text-slate-400">{t.closed_at_utc.slice(0, 19)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </Panel>
  );
}

import { useEffect, useState } from 'react';
import { apiGet, apiPut } from '../api/client';
import { Panel, StatusBadge } from '../components/UI';

export function EconomicCalendarPage() {
  const [events, setEvents] = useState<any[]>([]);
  const [status, setStatus] = useState<any>(null);

  useEffect(() => {
    apiGet<{ events: any[] }>('/api/v1/news/upcoming').then((d) => setEvents(d.events || []));
    apiGet('/api/v1/news/status').then(setStatus);
  }, []);

  return (
    <div className="space-y-4">
      {status && (
        <Panel title="News Blackout Status">
          <div className="flex items-center gap-3">
            <StatusBadge label={status.in_blackout ? 'BLACKOUT ACTIVE' : 'CLEAR'} tone={status.in_blackout ? 'red' : 'green'} />
            <span className="text-sm text-slate-300">{status.status_message}</span>
          </div>
        </Panel>
      )}

      <Panel title="Upcoming Economic Events">
        <div className="overflow-x-auto">
          <table className="w-full text-sm text-left text-slate-300">
            <thead className="text-xs uppercase text-slate-400 border-b border-slate-800">
              <tr>
                <th className="py-2 pr-3">Event</th>
                <th className="py-2 pr-3">Currency</th>
                <th className="py-2 pr-3">Impact</th>
                <th className="py-2 pr-3">Time (UTC)</th>
                <th className="py-2">Forecast / Prev</th>
              </tr>
            </thead>
            <tbody>
              {events.map((e) => (
                <tr key={e.id} className="border-b border-slate-800/60">
                  <td className="py-2 pr-3">{e.title}</td>
                  <td className="py-2 pr-3">{e.currency}</td>
                  <td className="py-2 pr-3">
                    <StatusBadge label={e.impact} tone={e.impact === 'HIGH' ? 'red' : 'amber'} />
                  </td>
                  <td className="py-2 pr-3">{e.event_time_utc.slice(0, 19)}</td>
                  <td className="py-2 text-slate-400">{e.forecast} / {e.previous}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Panel>
    </div>
  );
}

export function SettingsPage() {
  const [config, setConfig] = useState<any>(null);
  const [savedMsg, setSavedMsg] = useState('');

  useEffect(() => {
    apiGet('/api/v1/system/config').then(setConfig);
  }, []);

  const handleSave = async () => {
    if (!config) return;
    await apiPut('/api/v1/system/config', {
      settings: {
        symbol: config.default_symbol,
        account_type: config.account_type,
        data_mode: config.data_mode,
        operating_mode: config.operating_mode,
      },
    });
    setSavedMsg('Settings persisted to SQLite.');
  };

  if (!config) return <div className="text-slate-400 p-4">Loading settings...</div>;

  return (
    <Panel title="System & Trading Settings">
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-sm mb-4">
        <div>
          <div className="text-xs text-slate-400">Trading Symbol</div>
          <div className="mt-1 font-medium text-slate-200">{config.default_symbol}</div>
        </div>
        <div>
          <div className="text-xs text-slate-400">Account Type / Currency</div>
          <div className="mt-1 font-medium text-slate-200">{config.account_type} ({config.account_currency})</div>
        </div>
        <div>
          <div className="text-xs text-slate-400">Data Mode</div>
          <div className="mt-1 font-medium text-slate-200">{config.data_mode}</div>
        </div>
        <div>
          <div className="text-xs text-slate-400">Operating Mode</div>
          <div className="mt-1 font-medium text-amber-400">{config.operating_mode} (Safe Default)</div>
        </div>
      </div>
      <button onClick={handleSave} className="bg-amber-500 text-slate-950 font-medium text-sm px-4 py-2 rounded-lg">
        Save Snapshot to DB
      </button>
      {savedMsg && <span className="ml-3 text-xs text-emerald-400">{savedMsg}</span>}
    </Panel>
  );
}

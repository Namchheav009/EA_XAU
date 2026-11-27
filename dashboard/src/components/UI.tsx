import React from 'react';

export function StatusBadge({ label, tone = 'neutral' }: { label: string; tone?: 'gold' | 'green' | 'red' | 'amber' | 'neutral' }) {
  const styles: Record<string, string> = {
    gold: 'bg-amber-500/15 text-amber-400 border-amber-500/30',
    green: 'bg-emerald-500/15 text-emerald-400 border-emerald-500/30',
    red: 'bg-rose-500/15 text-rose-400 border-rose-500/30',
    amber: 'bg-yellow-500/15 text-yellow-300 border-yellow-500/30',
    neutral: 'bg-slate-800 text-slate-300 border-slate-700',
  };
  return (
    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium border ${styles[tone]}`}>
      {label}
    </span>
  );
}

export function MetricCard({
  title,
  value,
  sub,
  accent,
}: {
  title: string;
  value: string;
  sub?: string;
  accent?: 'gold' | 'green' | 'red';
}) {
  const valColor =
    accent === 'gold'
      ? 'text-amber-400'
      : accent === 'green'
        ? 'text-emerald-400'
        : accent === 'red'
          ? 'text-rose-400'
          : 'text-slate-100';
  return (
    <div className="bg-slate-900/90 border border-slate-800 rounded-xl p-4 shadow-sm">
      <div className="text-xs uppercase tracking-wider text-slate-400">{title}</div>
      <div className={`text-2xl font-semibold mt-1 ${valColor}`}>{value}</div>
      {sub && <div className="text-xs text-slate-400 mt-1">{sub}</div>}
    </div>
  );
}

export function Panel({ title, right, children }: { title: string; right?: React.ReactNode; children: React.ReactNode }) {
  return (
    <div className="bg-slate-900/90 border border-slate-800 rounded-xl p-4">
      <div className="flex items-center justify-between mb-3">
        <h2 className="text-sm font-semibold text-slate-200 tracking-wide">{title}</h2>
        {right}
      </div>
      {children}
    </div>
  );
}

import { useState } from 'react';
import {
  Activity,
  BarChart3,
  Brain,
  Calendar,
  History,
  LayoutDashboard,
  Layers,
  Settings,
  ShieldAlert,
  TrendingUp,
} from 'lucide-react';
import { MarketAnalysisPage, OverviewPage } from './pages/OverviewAndMarket';
import { PositionsPage, TradingHistoryPage, TradingSignalsPage } from './pages/TradingPages';
import { AIAnalysisPage, BacktestingPage, RiskManagementPage } from './pages/RiskAiBacktestPages';
import { EconomicCalendarPage, SettingsPage } from './pages/NewsAndSettingsPages';

const NAV_ITEMS = [
  { id: 'overview', label: 'Overview', icon: LayoutDashboard },
  { id: 'market', label: 'Market Analysis', icon: BarChart3 },
  { id: 'signals', label: 'Trading Signals', icon: TrendingUp },
  { id: 'positions', label: 'Positions', icon: Layers },
  { id: 'history', label: 'Trading History', icon: History },
  { id: 'risk', label: 'Risk Management', icon: ShieldAlert },
  { id: 'ai', label: 'AI Analysis', icon: Brain },
  { id: 'backtesting', label: 'Backtesting', icon: Activity },
  { id: 'calendar', label: 'Economic Calendar', icon: Calendar },
  { id: 'settings', label: 'Settings', icon: Settings },
] as const;

type TabId = (typeof NAV_ITEMS)[number]['id'];

export function App() {
  const [activeTab, setActiveTab] = useState<TabId>('overview');

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col md:flex-row">
      <aside className="w-full md:w-64 bg-slate-900 border-b md:border-b-0 md:border-r border-slate-800 p-4 flex flex-col">
        <div className="flex items-center gap-2 mb-6">
          <div className="w-8 h-8 rounded-lg bg-amber-500/20 border border-amber-500/40 flex items-center justify-center text-amber-400 font-bold">
            Au
          </div>
          <div>
            <div className="font-bold text-amber-400 tracking-wide">GoldAITrader</div>
            <div className="text-[11px] text-slate-400">XAUUSDc • Hybrid AI</div>
          </div>
        </div>

        <nav className="flex md:flex-col gap-1 overflow-x-auto">
          {NAV_ITEMS.map((item) => {
            const Icon = item.icon;
            const active = activeTab === item.id;
            return (
              <button
                key={item.id}
                onClick={() => setActiveTab(item.id)}
                className={`flex items-center gap-2.5 px-3 py-2 rounded-lg text-sm whitespace-nowrap transition-colors ${
                  active
                    ? 'bg-amber-500/15 text-amber-400 border border-amber-500/30 font-medium'
                    : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/60'
                }`}
              >
                <Icon className="w-4 h-4 shrink-0" />
                <span>{item.label}</span>
              </button>
            );
          })}
        </nav>
      </aside>

      <main className="flex-1 p-4 md:p-6 overflow-y-auto">
        {activeTab === 'overview' && <OverviewPage />}
        {activeTab === 'market' && <MarketAnalysisPage />}
        {activeTab === 'signals' && <TradingSignalsPage />}
        {activeTab === 'positions' && <PositionsPage />}
        {activeTab === 'history' && <TradingHistoryPage />}
        {activeTab === 'risk' && <RiskManagementPage />}
        {activeTab === 'ai' && <AIAnalysisPage />}
        {activeTab === 'backtesting' && <BacktestingPage />}
        {activeTab === 'calendar' && <EconomicCalendarPage />}
        {activeTab === 'settings' && <SettingsPage />}
      </main>
    </div>
  );
}

export default App;

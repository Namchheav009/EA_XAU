import { render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';
import App from './App';

globalThis.fetch = vi.fn(() =>
  Promise.resolve({
    ok: true,
    json: () =>
      Promise.resolve({
        operating_mode: 'MONITORING',
        data_mode: 'MOCK',
        emergency_stop: false,
        connector: { connected: true },
        balance: 10000,
        equity: 10042.5,
        margin_free: 9922.5,
        currency: 'USC',
        account_type: 'CENT',
        server: 'Exness-MT5Trial-Mock',
        is_mock: true,
        positions: [],
      }),
  })
) as unknown as typeof fetch;

describe('GoldAITrader Dashboard', () => {
  it('renders navigation tabs and brand header', () => {
    render(<App />);
    expect(screen.getByText('GoldAITrader')).toBeInTheDocument();
    expect(screen.getByText('Overview')).toBeInTheDocument();
    expect(screen.getByText('Market Analysis')).toBeInTheDocument();
    expect(screen.getByText('Risk Management')).toBeInTheDocument();
    expect(screen.getByText('Backtesting')).toBeInTheDocument();
  });
});

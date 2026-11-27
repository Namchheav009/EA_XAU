import { useEffect, useRef } from 'react';
import { createChart, ColorType, UTCTimestamp } from 'lightweight-charts';

export interface CandlePoint {
  timestamp: string;
  open: number;
  high: number;
  low: number;
  close: number;
}

export function CandlestickChart({
  candles,
  support,
  resistance,
}: {
  candles: CandlePoint[];
  support?: number;
  resistance?: number;
}) {
  const containerRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    if (!containerRef.current || candles.length === 0) return;
    const chart = createChart(containerRef.current, {
      layout: {
        background: { type: ColorType.Solid, color: '#0f172a' },
        textColor: '#94a3b8',
      },
      grid: {
        vertLines: { color: '#1e293b' },
        horzLines: { color: '#1e293b' },
      },
      width: containerRef.current.clientWidth,
      height: 360,
      timeScale: { timeVisible: true, secondsVisible: false },
    });

    const series = chart.addCandlestickSeries({
      upColor: '#10b981',
      downColor: '#ef4444',
      borderVisible: false,
      wickUpColor: '#10b981',
      wickDownColor: '#ef4444',
    });

    const formatted = candles.map((c) => ({
      time: Math.floor(new Date(c.timestamp).getTime() / 1000) as UTCTimestamp,
      open: c.open,
      high: c.high,
      low: c.low,
      close: c.close,
    }));
    series.setData(formatted);

    if (support) {
      const supLine = chart.addLineSeries({ color: '#22c55e', lineWidth: 1, lineStyle: 2 });
      supLine.setData(formatted.map((d) => ({ time: d.time, value: support })));
    }
    if (resistance) {
      const resLine = chart.addLineSeries({ color: '#f59e0b', lineWidth: 1, lineStyle: 2 });
      resLine.setData(formatted.map((d) => ({ time: d.time, value: resistance })));
    }

    chart.timeScale().fitContent();

    const handleResize = () => {
      if (containerRef.current) {
        chart.applyOptions({ width: containerRef.current.clientWidth });
      }
    };
    window.addEventListener('resize', handleResize);
    return () => {
      window.removeEventListener('resize', handleResize);
      chart.remove();
    };
  }, [candles, support, resistance]);

  return <div ref={containerRef} className="w-full rounded-lg overflow-hidden" />;
}

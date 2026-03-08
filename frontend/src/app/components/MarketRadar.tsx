'use client';

import { useState, useEffect } from 'react';
import { fetchMacroSignal, type MacroSignal } from '@/lib/api';

function StanceColor(stance: string): string {
  switch (stance) {
    case 'BULLISH': return 'var(--accent-green)';
    case 'NEUTRAL': return 'var(--accent-cyan)';
    case 'CAUTIOUS': return 'var(--accent-orange)';
    case 'BEARISH': return 'var(--accent-red)';
    default: return 'var(--text-muted)';
  }
}

function StanceEmoji(stance: string): string {
  switch (stance) {
    case 'BULLISH': return '🟢';
    case 'NEUTRAL': return '🔵';
    case 'CAUTIOUS': return '🟠';
    case 'BEARISH': return '🔴';
    default: return '⚪';
  }
}

function ScoreBar({ score }: { score: number }) {
  // Score ranges from -100 to +100
  const normalized = (score + 100) / 200; // 0 to 1
  const percentage = Math.round(normalized * 100);
  const color = score >= 20 ? 'var(--accent-green)'
    : score >= -20 ? 'var(--accent-cyan)'
    : score >= -40 ? 'var(--accent-orange)'
    : 'var(--accent-red)';

  return (
    <div className="w-full">
      <div className="flex justify-between text-xs mb-1">
        <span style={{ color: 'var(--text-muted)' }}>RISK-OFF</span>
        <span className="font-bold" style={{ color }}>{score > 0 ? '+' : ''}{score}</span>
        <span style={{ color: 'var(--text-muted)' }}>RISK-ON</span>
      </div>
      <div className="w-full h-2 rounded-full" style={{ background: 'var(--bg-primary)' }}>
        <div
          className="h-full rounded-full transition-all duration-500"
          style={{
            width: `${percentage}%`,
            background: `linear-gradient(90deg, var(--accent-red), var(--accent-orange), var(--accent-green))`,
            opacity: 0.8,
          }}
        />
        <div
          className="relative w-2 h-2 rounded-full -mt-2"
          style={{
            left: `calc(${percentage}% - 4px)`,
            background: color,
            boxShadow: `0 0 8px ${color}`,
          }}
        />
      </div>
    </div>
  );
}

function Indicator({ label, value, unit, trend }: {
  label: string;
  value: string | number | null;
  unit?: string;
  trend?: 'up' | 'down' | 'neutral';
}) {
  const trendColor = trend === 'up' ? 'var(--accent-green)'
    : trend === 'down' ? 'var(--accent-red)'
    : 'var(--text-secondary)';

  return (
    <div className="flex flex-col gap-0.5 p-2 rounded" style={{ background: 'var(--bg-primary)' }}>
      <span className="text-[10px] uppercase tracking-wider" style={{ color: 'var(--text-muted)' }}>
        {label}
      </span>
      <div className="flex items-baseline gap-1">
        <span className="text-sm font-bold" style={{ color: trendColor }}>
          {value !== null && value !== undefined ? value : '—'}
        </span>
        {unit && <span className="text-[10px]" style={{ color: 'var(--text-muted)' }}>{unit}</span>}
      </div>
    </div>
  );
}

export default function MarketRadar() {
  const [signal, setSignal] = useState<MacroSignal | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchMacroSignal().then((data) => {
      setSignal(data);
      setLoading(false);
    });
  }, []);

  if (loading) {
    return (
      <div className="rounded-lg p-4" style={{ background: 'var(--bg-card)', border: '1px solid var(--border)' }}>
        <div className="flex items-center gap-2 mb-3">
          <span className="text-xs font-bold tracking-wider" style={{ color: 'var(--accent-cyan)' }}>📡 MARKET RADAR</span>
        </div>
        <div className="flex items-center justify-center py-8">
          <span className="text-xs" style={{ color: 'var(--text-muted)' }}>Loading signals...</span>
        </div>
      </div>
    );
  }

  if (!signal) {
    return (
      <div className="rounded-lg p-4" style={{ background: 'var(--bg-card)', border: '1px solid var(--border)' }}>
        <div className="flex items-center gap-2 mb-3">
          <span className="text-xs font-bold tracking-wider" style={{ color: 'var(--accent-cyan)' }}>📡 MARKET RADAR</span>
        </div>
        <div className="text-xs text-center py-4" style={{ color: 'var(--text-muted)' }}>
          No signal data available
        </div>
      </div>
    );
  }

  const vixTrend = signal.vix !== null ? (signal.vix > 25 ? 'down' : signal.vix < 15 ? 'up' : 'neutral') : undefined;

  return (
    <div className="rounded-lg p-4" style={{ background: 'var(--bg-card)', border: '1px solid var(--border)' }}>
      {/* Header */}
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <span className="text-xs font-bold tracking-wider" style={{ color: 'var(--accent-cyan)' }}>
            📡 MARKET RADAR
          </span>
          <span className="w-1.5 h-1.5 rounded-full pulse-dot" style={{ background: 'var(--accent-green)' }} />
        </div>
        <span className="text-[10px]" style={{ color: 'var(--text-muted)' }}>{signal.date}</span>
      </div>

      {/* Macro Stance */}
      <div className="flex items-center gap-2 mb-3 p-2 rounded"
        style={{ background: 'var(--bg-primary)', border: `1px solid ${StanceColor(signal.macro_stance)}30` }}>
        <span className="text-lg">{StanceEmoji(signal.macro_stance)}</span>
        <div className="flex flex-col">
          <span className="text-xs font-bold" style={{ color: StanceColor(signal.macro_stance) }}>
            {signal.macro_stance}
          </span>
          <span className="text-[10px]" style={{ color: 'var(--text-muted)' }}>
            {signal.crypto_action}
          </span>
        </div>
      </div>

      {/* Score Bar */}
      <div className="mb-4">
        <ScoreBar score={signal.macro_score} />
      </div>

      {/* Indicators Grid */}
      <div className="grid grid-cols-2 gap-1.5 mb-3">
        <Indicator label="VIX" value={signal.vix?.toFixed(1) ?? null} trend={vixTrend} />
        <Indicator label="SOFR" value={signal.sofr?.toFixed(2) ?? null} unit="%" />
        <Indicator label="USD/JPY" value={signal.usdjpy?.toFixed(1) ?? null} />
        <Indicator label="US 10Y" value={signal.us10y?.toFixed(2) ?? null} unit="%" />
        <Indicator
          label="NET LIQ"
          value={signal.net_liq_billion ? `${(signal.net_liq_billion / 1000).toFixed(2)}T` : null}
        />
        <Indicator
          label="LIQ Δ/W"
          value={signal.net_liq_weekly_change_pct ? `${signal.net_liq_weekly_change_pct > 0 ? '+' : ''}${signal.net_liq_weekly_change_pct.toFixed(1)}%` : null}
          trend={signal.net_liq_weekly_change_pct ? (signal.net_liq_weekly_change_pct > 0 ? 'up' : 'down') : undefined}
        />
      </div>

      {/* Triggers */}
      {signal.triggers && signal.triggers.length > 0 && (
        <div className="mt-3 pt-3" style={{ borderTop: '1px solid var(--border)' }}>
          <span className="text-[10px] uppercase tracking-wider" style={{ color: 'var(--text-muted)' }}>
            SIGNALS
          </span>
          <div className="mt-1.5 flex flex-col gap-1">
            {signal.triggers.map((t, i) => (
              <div key={i} className="flex items-start gap-1.5 text-[11px] leading-relaxed">
                <span>{t.type === 'DANGER' ? '🔴' : t.type === 'WARNING' ? '🟡' : '🟢'}</span>
                <span style={{ color: 'var(--text-secondary)' }}>{t.msg}</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

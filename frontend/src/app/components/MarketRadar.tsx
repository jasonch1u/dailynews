'use client';

import { useState, useEffect } from 'react';
import { fetchMacroSignal, fetchMacroHistory, type MacroSignal, type MacroSnapshot } from '@/lib/api';
import {
  RadarChart, Radar, PolarGrid, PolarAngleAxis, PolarRadiusAxis,
  ResponsiveContainer, AreaChart, Area, Tooltip
} from 'recharts';

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
  const normalized = (score + 100) / 200;
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

// ─── 7-Signal Radar Chart ───
function MacroRadarChart({ signal }: { signal: MacroSignal }) {
  // Normalize each indicator to 0-100 scale for the radar
  const normalize = (value: number | null, min: number, max: number, invert = false): number => {
    if (value === null) return 50;
    const clamped = Math.max(min, Math.min(max, value));
    const norm = ((clamped - min) / (max - min)) * 100;
    return invert ? 100 - norm : norm;
  };

  const radarData = [
    { signal: 'VIX', value: normalize(signal.vix, 10, 50, true), raw: signal.vix?.toFixed(1) ?? '—' },
    { signal: 'SOFR', value: normalize(signal.sofr, 3.5, 5.5, true), raw: signal.sofr?.toFixed(2) ?? '—' },
    { signal: 'USD/JPY', value: normalize(signal.usdjpy, 140, 165, true), raw: signal.usdjpy?.toFixed(1) ?? '—' },
    { signal: 'US10Y', value: normalize(signal.us10y, 3.5, 5.0, true), raw: signal.us10y?.toFixed(2) ?? '—' },
    { signal: 'NET LIQ', value: normalize(signal.net_liq_billion, 5000, 7000), raw: signal.net_liq_billion ? `${(signal.net_liq_billion / 1000).toFixed(1)}T` : '—' },
    { signal: 'LIQ Δ', value: normalize(signal.net_liq_weekly_change_pct, -3, 3), raw: signal.net_liq_weekly_change_pct ? `${signal.net_liq_weekly_change_pct > 0 ? '+' : ''}${signal.net_liq_weekly_change_pct.toFixed(1)}%` : '—' },
    { signal: 'SCORE', value: normalize(signal.macro_score, -100, 100), raw: String(signal.macro_score) },
  ];

  const stanceColor = StanceColor(signal.macro_stance);

  return (
    <div className="mb-3">
      <ResponsiveContainer width="100%" height={220}>
        <RadarChart data={radarData} cx="50%" cy="50%" outerRadius="70%">
          <PolarGrid stroke="#2a2a3a" />
          <PolarAngleAxis
            dataKey="signal"
            tick={{ fill: '#8888a0', fontSize: 10 }}
          />
          <PolarRadiusAxis
            angle={90}
            domain={[0, 100]}
            tick={false}
            axisLine={false}
          />
          <Radar
            name="Macro"
            dataKey="value"
            stroke={stanceColor}
            fill={stanceColor}
            fillOpacity={0.15}
            strokeWidth={2}
          />
        </RadarChart>
      </ResponsiveContainer>
    </div>
  );
}

// ─── Mini Sparkline for each indicator ───
function Sparkline({ data, color, height = 24 }: { data: number[]; color: string; height?: number }) {
  if (data.length < 2) return null;
  const chartData = data.map((v, i) => ({ i, v }));

  return (
    <div style={{ width: '60px', height: `${height}px` }}>
      <ResponsiveContainer width="100%" height="100%">
        <AreaChart data={chartData} margin={{ top: 2, right: 0, bottom: 0, left: 0 }}>
          <defs>
            <linearGradient id={`spark-${color.replace(/[^a-z0-9]/gi, '')}`} x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor={color} stopOpacity={0.3} />
              <stop offset="100%" stopColor={color} stopOpacity={0} />
            </linearGradient>
          </defs>
          <Area
            type="monotone"
            dataKey="v"
            stroke={color}
            strokeWidth={1.5}
            fill={`url(#spark-${color.replace(/[^a-z0-9]/gi, '')})`}
            dot={false}
            isAnimationActive={false}
          />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
}

function Indicator({ label, value, unit, trend, sparkData, sparkColor }: {
  label: string;
  value: string | number | null;
  unit?: string;
  trend?: 'up' | 'down' | 'neutral';
  sparkData?: number[];
  sparkColor?: string;
}) {
  const trendColor = trend === 'up' ? 'var(--accent-green)'
    : trend === 'down' ? 'var(--accent-red)'
    : 'var(--text-secondary)';

  return (
    <div className="flex items-center justify-between gap-1 p-2 rounded" style={{ background: 'var(--bg-primary)' }}>
      <div className="flex flex-col gap-0.5 min-w-0">
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
      {sparkData && sparkData.length >= 2 && (
        <Sparkline data={sparkData} color={sparkColor || trendColor} />
      )}
    </div>
  );
}

export default function MarketRadar() {
  const [signal, setSignal] = useState<MacroSignal | null>(null);
  const [history, setHistory] = useState<MacroSnapshot[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([
      fetchMacroSignal(),
      fetchMacroHistory(7),
    ]).then(([sig, hist]) => {
      setSignal(sig);
      setHistory(hist);
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

  // Build sparkline data from history (reversed to chronological order)
  const histReversed = [...history].reverse();
  const vixSpark = histReversed.map(h => h.vix ?? 0).filter(v => v > 0);
  const sofrSpark = histReversed.map(h => h.sofr ?? 0).filter(v => v > 0);
  const usdjpySpark = histReversed.map(h => h.usdjpy ?? 0).filter(v => v > 0);
  const us10ySpark = histReversed.map(h => h.us10y ?? 0).filter(v => v > 0);
  const netLiqSpark = histReversed.map(h => h.net_liq_billion ?? 0).filter(v => v > 0);
  const scoreSpark = histReversed.map(h => h.macro_score ?? 0);

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
      <div className="mb-3">
        <ScoreBar score={signal.macro_score} />
      </div>

      {/* 7-Signal Radar Chart */}
      <MacroRadarChart signal={signal} />

      {/* Indicators Grid with Sparklines */}
      <div className="grid grid-cols-1 gap-1.5 mb-3">
        <Indicator label="VIX" value={signal.vix?.toFixed(1) ?? null} trend={vixTrend}
          sparkData={vixSpark} sparkColor="#ff4757" />
        <Indicator label="SOFR" value={signal.sofr?.toFixed(2) ?? null} unit="%"
          sparkData={sofrSpark} sparkColor="#00d4ff" />
        <Indicator label="USD/JPY" value={signal.usdjpy?.toFixed(1) ?? null}
          sparkData={usdjpySpark} sparkColor="#ff8c00" />
        <Indicator label="US 10Y" value={signal.us10y?.toFixed(2) ?? null} unit="%"
          sparkData={us10ySpark} sparkColor="#a855f7" />
        <Indicator
          label="NET LIQ"
          value={signal.net_liq_billion ? `${(signal.net_liq_billion / 1000).toFixed(2)}T` : null}
          sparkData={netLiqSpark} sparkColor="#00e599"
        />
        <Indicator
          label="LIQ Δ/W"
          value={signal.net_liq_weekly_change_pct ? `${signal.net_liq_weekly_change_pct > 0 ? '+' : ''}${signal.net_liq_weekly_change_pct.toFixed(1)}%` : null}
          trend={signal.net_liq_weekly_change_pct ? (signal.net_liq_weekly_change_pct > 0 ? 'up' : 'down') : undefined}
          sparkData={scoreSpark} sparkColor="#ffd700"
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

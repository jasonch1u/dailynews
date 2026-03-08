'use client';

import { useMemo, useState } from 'react';

interface GeoMapProps {
  markdown: string | null;
}

interface Marker {
  key: string;
  label: string;
  x: number;
  y: number;
  intensity: number;
}

const LOCATION_POINTS: Array<{ key: string; aliases: string[]; label: string; x: number; y: number }> = [
  { key: 'usa', aliases: ['united states', 'u.s.', 'usa', '美國'], label: 'United States', x: 22, y: 38 },
  { key: 'canada', aliases: ['canada', '加拿大'], label: 'Canada', x: 20, y: 28 },
  { key: 'mexico', aliases: ['mexico', '墨西哥'], label: 'Mexico', x: 18, y: 48 },
  { key: 'uk', aliases: ['united kingdom', 'britain', 'uk', '英國'], label: 'United Kingdom', x: 47, y: 30 },
  { key: 'eu', aliases: ['european union', 'europe', 'eu', '歐盟', '歐洲'], label: 'Europe', x: 50, y: 32 },
  { key: 'ukraine', aliases: ['ukraine', '烏克蘭'], label: 'Ukraine', x: 56, y: 33 },
  { key: 'russia', aliases: ['russia', '俄羅斯'], label: 'Russia', x: 63, y: 26 },
  { key: 'turkey', aliases: ['turkey', '土耳其'], label: 'Turkey', x: 56, y: 39 },
  { key: 'israel', aliases: ['israel', '以色列', 'gaza', '加薩'], label: 'Israel / Gaza', x: 57, y: 43 },
  { key: 'iran', aliases: ['iran', '伊朗'], label: 'Iran', x: 61, y: 43 },
  { key: 'saudi', aliases: ['saudi', '沙烏地'], label: 'Saudi Arabia', x: 60, y: 47 },
  { key: 'hormuz', aliases: ['hormuz', '荷姆茲'], label: 'Strait of Hormuz', x: 63, y: 45 },
  { key: 'india', aliases: ['india', '印度'], label: 'India', x: 68, y: 47 },
  { key: 'china', aliases: ['china', '中國'], label: 'China', x: 75, y: 39 },
  { key: 'taiwan', aliases: ['taiwan', '台灣'], label: 'Taiwan', x: 80, y: 43 },
  { key: 'japan', aliases: ['japan', '日本'], label: 'Japan', x: 84, y: 37 },
  { key: 'korea', aliases: ['korea', '韓國', '北韓'], label: 'Korean Peninsula', x: 81, y: 38 },
  { key: 'philippines', aliases: ['philippines', '菲律賓'], label: 'Philippines', x: 83, y: 50 },
  { key: 'south-china-sea', aliases: ['south china sea', '南海'], label: 'South China Sea', x: 79, y: 50 },
  { key: 'australia', aliases: ['australia', '澳洲'], label: 'Australia', x: 83, y: 69 },
  { key: 'africa', aliases: ['africa', '非洲'], label: 'Africa', x: 53, y: 56 },
];

function extractGeoText(markdown: string): string {
  const chunks = markdown.split(/\n### \d+\./g);
  const geoChunks = chunks.filter((chunk) => {
    const lower = chunk.toLowerCase();
    return /\[geo\]|地緣|geopolit|war|military|sanction|制裁|戰爭|衝突|iran|ukraine|taiwan|中東/.test(lower);
  });
  return geoChunks.join('\n').toLowerCase();
}

function buildMarkers(markdown: string | null): Marker[] {
  if (!markdown) return [];
  const geoText = extractGeoText(markdown);
  if (!geoText.trim()) return [];

  const markers: Marker[] = [];

  for (const loc of LOCATION_POINTS) {
    const hits = loc.aliases.reduce((count, alias) => {
      const pattern = new RegExp(alias.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'), 'g');
      const matched = geoText.match(pattern);
      return count + (matched ? matched.length : 0);
    }, 0);

    if (hits > 0) {
      markers.push({
        key: loc.key,
        label: loc.label,
        x: loc.x,
        y: loc.y,
        intensity: Math.min(hits, 4),
      });
    }
  }

  return markers;
}

export default function GeoMap({ markdown }: GeoMapProps) {
  const markers = useMemo(() => buildMarkers(markdown), [markdown]);
  const [collapsed, setCollapsed] = useState(false);

  return (
    <section className="rounded-lg p-4 mb-4" style={{ background: 'var(--bg-card)', border: '1px solid var(--border)' }}>
      <button
        onClick={() => setCollapsed(!collapsed)}
        className="flex items-center justify-between mb-2 w-full text-left"
      >
        <span className="text-xs font-bold tracking-wider" style={{ color: 'var(--accent-red)' }}>
          🌍 GEOPOLITICAL EVENT MAP
        </span>
        <div className="flex items-center gap-2">
          <span className="text-[10px]" style={{ color: 'var(--text-muted)' }}>
            {markers.length} hotspots
          </span>
          <span className="text-[10px] transition-transform" style={{ color: 'var(--text-muted)', transform: collapsed ? 'rotate(-90deg)' : 'rotate(0)' }}>
            ▼
          </span>
        </div>
      </button>

      <div className={`${collapsed ? 'hidden' : 'block'} rounded p-2`} style={{ background: 'var(--bg-primary)', border: '1px solid var(--border)' }}>
        <svg viewBox="0 0 1000 480" className="w-full h-auto" role="img" aria-label="Geopolitical event map">
          <defs>
            <linearGradient id="wm-ocean" x1="0" y1="0" x2="1" y2="1">
              <stop offset="0%" stopColor="#090d16" />
              <stop offset="100%" stopColor="#11182a" />
            </linearGradient>
            <radialGradient id="wm-glow" cx="50%" cy="50%" r="50%">
              <stop offset="0%" stopColor="#ff4757" stopOpacity="0.9" />
              <stop offset="100%" stopColor="#ff4757" stopOpacity="0" />
            </radialGradient>
          </defs>

          <rect x="0" y="0" width="1000" height="480" fill="url(#wm-ocean)" rx="12" />

          <g fill="#1f2b3d" stroke="#31435c" strokeWidth="2" opacity="0.95">
            <path d="M92 150 L110 110 L168 88 L224 96 L256 132 L252 172 L214 204 L152 206 L108 188 Z" />
            <path d="M248 230 L286 214 L312 232 L298 276 L262 296 L236 266 Z" />
            <path d="M442 110 L470 90 L550 92 L606 116 L642 154 L614 190 L540 188 L502 212 L468 188 L430 164 Z" />
            <path d="M528 210 L564 224 L582 254 L570 300 L526 336 L490 316 L476 274 L492 234 Z" />
            <path d="M598 162 L654 148 L712 164 L782 194 L828 216 L806 258 L732 254 L678 242 L642 214 Z" />
            <path d="M772 284 L830 292 L892 334 L880 374 L812 390 L758 352 Z" />
          </g>

          {markers.map((marker) => {
            const cx = (marker.x / 100) * 1000;
            const cy = (marker.y / 100) * 480;
            const pulse = 6 + marker.intensity * 2;
            return (
              <g key={marker.key}>
                <circle cx={cx} cy={cy} r={pulse * 2.2} fill="url(#wm-glow)" />
                <circle cx={cx} cy={cy} r={pulse} fill="#ff4757" fillOpacity="0.25" />
                <circle cx={cx} cy={cy} r="3.5" fill="#ffd1d6" stroke="#ff4757" strokeWidth="1.5" />
              </g>
            );
          })}
        </svg>
      </div>

      <div className={`${collapsed ? 'hidden' : 'flex'} mt-2 flex-wrap gap-1.5`}>
        {markers.slice(0, 8).map((marker) => (
          <span
            key={marker.key}
            className="text-[10px] px-1.5 py-0.5 rounded"
            style={{ color: '#ff9aa4', background: 'rgba(255,71,87,0.12)', border: '1px solid rgba(255,71,87,0.35)' }}
          >
            {marker.label}
          </span>
        ))}
        {markers.length === 0 && (
          <span className="text-[10px]" style={{ color: 'var(--text-muted)' }}>
            No GEO hotspots detected from current digest.
          </span>
        )}
      </div>
    </section>
  );
}

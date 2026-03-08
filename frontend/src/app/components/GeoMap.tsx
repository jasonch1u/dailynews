'use client';

import { useMemo, useRef, useState } from 'react';
import {
  ComposableMap,
  Geographies,
  Geography,
  Marker,
  Graticule,
} from 'react-simple-maps';
import { geoNaturalEarth1 } from 'd3-geo';

const GEO_URL = 'https://cdn.jsdelivr.net/npm/world-atlas@2/countries-110m.json';

interface GeoMapProps {
  markdown: string | null;
}

interface HotspotMarker {
  key: string;
  label: string;
  coordinates: [number, number]; // [lng, lat]
  intensity: number;
  snippets: string[]; // extracted context sentences
}

const LOCATION_POINTS: Array<{
  key: string;
  aliases: string[];
  label: string;
  coordinates: [number, number];
}> = [
  { key: 'usa', aliases: ['united states', 'u.s.', 'usa', '美國', 'washington', 'white house', 'pentagon'], label: 'United States', coordinates: [-98, 39] },
  { key: 'canada', aliases: ['canada', '加拿大', 'ottawa'], label: 'Canada', coordinates: [-106, 56] },
  { key: 'mexico', aliases: ['mexico', '墨西哥'], label: 'Mexico', coordinates: [-102, 23] },
  { key: 'brazil', aliases: ['brazil', '巴西'], label: 'Brazil', coordinates: [-51, -14] },
  { key: 'argentina', aliases: ['argentina', '阿根廷'], label: 'Argentina', coordinates: [-64, -34] },
  { key: 'uk', aliases: ['united kingdom', 'britain', 'uk', '英國', 'london'], label: 'United Kingdom', coordinates: [-2, 54] },
  { key: 'france', aliases: ['france', '法國', 'paris', 'macron'], label: 'France', coordinates: [2, 47] },
  { key: 'germany', aliases: ['germany', '德國', 'berlin'], label: 'Germany', coordinates: [10, 51] },
  { key: 'eu', aliases: ['european union', 'europe', 'eu', '歐盟', '歐洲', 'brussels'], label: 'Europe', coordinates: [15, 50] },
  { key: 'ukraine', aliases: ['ukraine', '烏克蘭', 'kyiv', 'zelensky'], label: 'Ukraine', coordinates: [32, 49] },
  { key: 'russia', aliases: ['russia', '俄羅斯', 'moscow', 'kremlin', 'putin'], label: 'Russia', coordinates: [60, 60] },
  { key: 'turkey', aliases: ['turkey', 'türkiye', '土耳其', 'ankara', 'erdogan'], label: 'Turkey', coordinates: [32, 39] },
  { key: 'israel', aliases: ['israel', '以色列', 'gaza', '加薩', 'hamas', 'netanyahu', 'tel aviv'], label: 'Israel / Gaza', coordinates: [35, 31] },
  { key: 'iran', aliases: ['iran', '伊朗', 'tehran'], label: 'Iran', coordinates: [53, 33] },
  { key: 'saudi', aliases: ['saudi', '沙烏地', 'riyadh'], label: 'Saudi Arabia', coordinates: [45, 24] },
  { key: 'hormuz', aliases: ['hormuz', '荷姆茲', 'strait of hormuz'], label: 'Strait of Hormuz', coordinates: [56, 26] },
  { key: 'india', aliases: ['india', '印度', 'modi', 'delhi', 'mumbai'], label: 'India', coordinates: [79, 21] },
  { key: 'china', aliases: ['china', '中國', 'beijing', 'xi jinping', '習近平'], label: 'China', coordinates: [104, 35] },
  { key: 'taiwan', aliases: ['taiwan', '台灣', 'taipei'], label: 'Taiwan', coordinates: [121, 24] },
  { key: 'japan', aliases: ['japan', '日本', 'tokyo', 'boj'], label: 'Japan', coordinates: [138, 36] },
  { key: 'korea', aliases: ['korea', '韓國', '北韓', 'pyongyang', 'seoul', 'kim jong'], label: 'Korean Peninsula', coordinates: [128, 37] },
  { key: 'philippines', aliases: ['philippines', '菲律賓', 'manila'], label: 'Philippines', coordinates: [122, 13] },
  { key: 'south-china-sea', aliases: ['south china sea', '南海', 'spratlys'], label: 'South China Sea', coordinates: [114, 12] },
  { key: 'australia', aliases: ['australia', '澳洲', 'canberra'], label: 'Australia', coordinates: [134, -25] },
  { key: 'africa', aliases: ['africa', '非洲'], label: 'Africa', coordinates: [20, 5] },
  { key: 'nigeria', aliases: ['nigeria', '奈及利亞'], label: 'Nigeria', coordinates: [8, 10] },
  { key: 'south-africa', aliases: ['south africa', '南非'], label: 'South Africa', coordinates: [25, -29] },
  { key: 'egypt', aliases: ['egypt', '埃及', 'suez', 'cairo'], label: 'Egypt', coordinates: [30, 27] },
  { key: 'yemen', aliases: ['yemen', '葉門', 'houthi'], label: 'Yemen', coordinates: [48, 15] },
  { key: 'red-sea', aliases: ['red sea', '紅海'], label: 'Red Sea', coordinates: [39, 20] },
];

function extractGeoChunks(markdown: string): string[] {
  // Split by ### numbered sections and keep geo-relevant ones
  const chunks = markdown.split(/\n### \d+\./g);
  return chunks.filter((chunk) => {
    const lower = chunk.toLowerCase();
    return /\[geo\]|地緣|geopolit|war|military|sanction|制裁|戰爭|衝突|iran|ukraine|taiwan|中東|missile|bomb|troops|naval|army|tariff|關稅|外交|diplomacy/.test(lower);
  });
}

function extractSnippets(chunks: string[], aliases: string[]): string[] {
  const snippets: string[] = [];
  for (const chunk of chunks) {
    const lower = chunk.toLowerCase();
    const matched = aliases.some((alias) => lower.includes(alias.toLowerCase()));
    if (!matched) continue;

    // Extract the headline (first line) or first meaningful sentence
    const lines = chunk.trim().split('\n').filter((l) => l.trim());
    if (lines.length > 0) {
      // First line is usually the headline
      let headline = lines[0]
        .replace(/^\*\*|\*\*$/g, '') // strip bold
        .replace(/^【[^】]*】\s*/, '') // strip 【TAG】
        .replace(/^\[[^\]]*\]\s*/, '') // strip [TAG]
        .trim();
      if (headline.length > 80) headline = headline.slice(0, 77) + '…';
      if (headline && !snippets.includes(headline)) {
        snippets.push(headline);
      }
    }
  }
  return snippets.slice(0, 3); // max 3 snippets per location
}

function buildMarkers(markdown: string | null): HotspotMarker[] {
  if (!markdown) return [];
  const geoChunks = extractGeoChunks(markdown);
  const geoText = geoChunks.join('\n').toLowerCase();
  if (!geoText.trim()) return [];

  const markers: HotspotMarker[] = [];

  for (const loc of LOCATION_POINTS) {
    const hits = loc.aliases.reduce((count, alias) => {
      const pattern = new RegExp(alias.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'), 'gi');
      const matched = geoText.match(pattern);
      return count + (matched ? matched.length : 0);
    }, 0);

    if (hits > 0) {
      const snippets = extractSnippets(geoChunks, loc.aliases);
      markers.push({
        key: loc.key,
        label: loc.label,
        coordinates: loc.coordinates,
        intensity: Math.min(hits, 5),
        snippets,
      });
    }
  }

  return markers;
}

const intensityColor = (intensity: number) => {
  if (intensity >= 4) return '#ff2d3b';
  if (intensity >= 3) return '#ff4757';
  if (intensity >= 2) return '#ff6b7a';
  return '#ff8f9c';
};

export default function GeoMap({ markdown }: GeoMapProps) {
  const markers = useMemo(() => buildMarkers(markdown), [markdown]);
  const [collapsed, setCollapsed] = useState(false);
  const [hoveredMarker, setHoveredMarker] = useState<string | null>(null);
  const [selectedMarker, setSelectedMarker] = useState<string | null>(null);
  const mapRef = useRef<HTMLDivElement>(null);
  const selectedData = markers.find((m) => m.key === selectedMarker);
  const hoveredData = markers.find((m) => m.key === hoveredMarker);

  // Project geo coordinates → pixel position inside the map div
  const getMarkerPixelPos = (coordinates: [number, number]) => {
    if (!mapRef.current) return null;
    const projection = geoNaturalEarth1()
      .scale(148)
      .center([10, 0])
      .translate([400, 200]); // half of 800x400 SVG viewBox
    const projected = projection(coordinates);
    if (!projected) return null;
    const rect = mapRef.current;
    const scaleX = rect.clientWidth / 800;
    const scaleY = rect.clientHeight / 400;
    return { x: projected[0] * scaleX, y: projected[1] * scaleY };
  };

  return (
    <section
      className="rounded-lg p-4 mb-4"
      style={{ background: 'var(--bg-card)', border: '1px solid var(--border)' }}
    >
      <button
        onClick={() => setCollapsed(!collapsed)}
        className="flex items-center justify-between mb-2 w-full text-left"
      >
        <span
          className="text-xs font-bold tracking-wider"
          style={{ color: 'var(--accent-red)' }}
        >
          🌍 GEOPOLITICAL EVENT MAP
        </span>
        <div className="flex items-center gap-2">
          <span className="text-[10px]" style={{ color: 'var(--text-muted)' }}>
            {markers.length} hotspots
          </span>
          <span
            className="text-[10px] transition-transform"
            style={{
              color: 'var(--text-muted)',
              transform: collapsed ? 'rotate(-90deg)' : 'rotate(0)',
            }}
          >
            ▼
          </span>
        </div>
      </button>

      <div
        ref={mapRef}
        className={`${collapsed ? 'hidden' : 'block'} rounded overflow-hidden relative`}
        style={{
          background: '#080d19',
          border: '1px solid var(--border)',
        }}
      >
        <style>{`
          @keyframes geo-pulse {
            0% { r: 4; opacity: 0.8; }
            50% { r: 10; opacity: 0.3; }
            100% { r: 4; opacity: 0.8; }
          }
          @keyframes geo-pulse-lg {
            0% { r: 6; opacity: 0.6; }
            50% { r: 18; opacity: 0.1; }
            100% { r: 6; opacity: 0.6; }
          }
          .geo-pulse { animation: geo-pulse 2.5s ease-in-out infinite; }
          .geo-pulse-lg { animation: geo-pulse-lg 3s ease-in-out infinite; }
        `}</style>
        <ComposableMap
          projection="geoNaturalEarth1"
          projectionConfig={{
            scale: 148,
            center: [10, 0],
          }}
          width={800}
          height={400}
          style={{ width: '100%', height: 'auto' }}
        >
          <defs>
            <radialGradient id="geo-hotspot-glow">
              <stop offset="0%" stopColor="#ff4757" stopOpacity="0.6" />
              <stop offset="100%" stopColor="#ff4757" stopOpacity="0" />
            </radialGradient>
          </defs>

          {/* Ocean background */}
          <rect x={-50} y={-50} width={900} height={460} fill="#080d19" />

          {/* Grid lines */}
          <Graticule stroke="#1a2540" strokeWidth={0.4} />

          {/* Countries */}
          <Geographies geography={GEO_URL}>
            {({ geographies }) =>
              geographies.map((geo) => (
                <Geography
                  key={geo.rsmKey}
                  geography={geo}
                  fill="#16213e"
                  stroke="#1e3055"
                  strokeWidth={0.5}
                  style={{
                    default: { outline: 'none' },
                    hover: { outline: 'none', fill: '#1e3055' },
                    pressed: { outline: 'none' },
                  }}
                />
              ))
            }
          </Geographies>

          {/* Hotspot markers */}
          {markers.map((marker) => {
            const color = intensityColor(marker.intensity);
            const isHovered = hoveredMarker === marker.key;
            const baseR = 3 + marker.intensity * 1.2;

            return (
              <Marker
                key={marker.key}
                coordinates={marker.coordinates}
                onMouseEnter={() => setHoveredMarker(marker.key)}
                onMouseLeave={() => setHoveredMarker(null)}
                onClick={() => setSelectedMarker(selectedMarker === marker.key ? null : marker.key)}
                style={{ cursor: 'pointer' }}
              >
                {/* Outer glow */}
                <circle
                  r={baseR * 4}
                  fill="url(#geo-hotspot-glow)"
                  opacity={0.5}
                />
                {/* Pulse ring */}
                <circle
                  className={marker.intensity >= 3 ? 'geo-pulse-lg' : 'geo-pulse'}
                  fill="none"
                  stroke={color}
                  strokeWidth={1}
                  opacity={0.6}
                />
                {/* Inner dot */}
                <circle
                  r={baseR}
                  fill={color}
                  fillOpacity={0.35}
                  stroke={color}
                  strokeWidth={1.5}
                />
                <circle r={2} fill="#fff" fillOpacity={0.9} />

                {/* Tooltip label */}
                {isHovered && (
                  <g>
                    <rect
                      x={8}
                      y={-12}
                      width={marker.label.length * 6.5 + 12}
                      height={20}
                      rx={4}
                      fill="rgba(0,0,0,0.85)"
                      stroke={color}
                      strokeWidth={0.5}
                    />
                    <text
                      x={14}
                      y={2}
                      style={{
                        fontSize: '10px',
                        fill: '#fff',
                        fontFamily: 'system-ui, sans-serif',
                        fontWeight: 500,
                      }}
                    >
                      {marker.label}
                    </text>
                  </g>
                )}
              </Marker>
            );
          })}
        </ComposableMap>

        {/* Floating tooltip on hover */}
        {hoveredData && (() => {
          const pos = getMarkerPixelPos(hoveredData.coordinates);
          if (!pos || hoveredData.snippets.length === 0) return null;
          const isRight = pos.x > (mapRef.current?.clientWidth ?? 400) / 2;
          return (
          <div
            className="absolute z-20 pointer-events-none"
            style={{
              left: pos.x,
              top: pos.y,
              transform: isRight
                ? 'translate(-105%, -50%)'
                : 'translate(12px, -50%)',
              maxWidth: 280,
            }}
          >
            <div
              className="rounded-lg p-2.5 shadow-lg"
              style={{
                background: 'rgba(8,13,25,0.95)',
                border: `1px solid ${intensityColor(hoveredData.intensity)}60`,
                backdropFilter: 'blur(8px)',
              }}
            >
              <div className="flex items-center gap-1.5 mb-1.5">
                <span
                  className="inline-block w-2 h-2 rounded-full"
                  style={{ background: intensityColor(hoveredData.intensity) }}
                />
                <span className="text-[11px] font-semibold text-white">
                  {hoveredData.label}
                </span>
                <span
                  className="text-[9px] ml-auto px-1 rounded"
                  style={{
                    color: intensityColor(hoveredData.intensity),
                    background: `${intensityColor(hoveredData.intensity)}20`,
                  }}
                >
                  ×{hoveredData.intensity}
                </span>
              </div>
              <ul className="space-y-1">
                {hoveredData.snippets.map((snippet, i) => (
                  <li
                    key={i}
                    className="text-[10px] leading-snug pl-2"
                    style={{
                      color: 'rgba(255,255,255,0.7)',
                      borderLeft: `2px solid ${intensityColor(hoveredData.intensity)}50`,
                    }}
                  >
                    {snippet}
                  </li>
                ))}
              </ul>
            </div>
          </div>
          );
        })()}
      </div>

      {/* Detail panel for selected hotspot */}
      {!collapsed && selectedData && selectedData.snippets.length > 0 && (
        <div
          className="mt-2 rounded p-3"
          style={{
            background: 'rgba(255,71,87,0.06)',
            border: `1px solid ${intensityColor(selectedData.intensity)}30`,
          }}
        >
          <div className="flex items-center justify-between mb-1.5">
            <span className="text-xs font-semibold" style={{ color: intensityColor(selectedData.intensity) }}>
              📍 {selectedData.label}
            </span>
            <button
              onClick={() => setSelectedMarker(null)}
              className="text-[10px] px-1.5 py-0.5 rounded hover:opacity-80"
              style={{ color: 'var(--text-muted)', background: 'rgba(255,255,255,0.05)' }}
            >
              ✕
            </button>
          </div>
          <ul className="space-y-1">
            {selectedData.snippets.map((snippet, i) => (
              <li
                key={i}
                className="text-[11px] leading-relaxed pl-2"
                style={{
                  color: 'var(--text-secondary)',
                  borderLeft: `2px solid ${intensityColor(selectedData.intensity)}40`,
                }}
              >
                {snippet}
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Legend tags */}
      <div className={`${collapsed ? 'hidden' : 'flex'} mt-2 flex-wrap gap-1.5`}>
        {markers
          .sort((a, b) => b.intensity - a.intensity)
          .slice(0, 10)
          .map((marker) => (
            <button
              key={marker.key}
              className="text-[10px] px-1.5 py-0.5 rounded transition-all"
              style={{
                color: intensityColor(marker.intensity),
                background: selectedMarker === marker.key
                  ? `${intensityColor(marker.intensity)}25`
                  : `${intensityColor(marker.intensity)}15`,
                border: `1px solid ${selectedMarker === marker.key
                  ? intensityColor(marker.intensity)
                  : `${intensityColor(marker.intensity)}40`}`,
              }}
              onMouseEnter={() => setHoveredMarker(marker.key)}
              onMouseLeave={() => setHoveredMarker(null)}
              onClick={() => setSelectedMarker(selectedMarker === marker.key ? null : marker.key)}
            >
              {marker.intensity >= 4 ? '🔴' : marker.intensity >= 2 ? '🟠' : '🟡'}{' '}
              {marker.label}
            </button>
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

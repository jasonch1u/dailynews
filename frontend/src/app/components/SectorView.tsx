'use client';

import { useMemo } from 'react';

interface SectorViewProps {
  markdown: string | null;
}

interface SectorData {
  bullish: string[];
  bearish: string[];
}

function extractSectors(markdown: string): SectorData {
  const result: SectorData = { bullish: [], bearish: [] };

  const bullMatch = markdown.match(/📈\s*\*\*看漲[/／]活躍\*\*[：:]\s*(.+)/);
  if (bullMatch) {
    result.bullish = bullMatch[1].split(/[,，、]/).map(s => s.trim()).filter(Boolean);
  }

  const bearMatch = markdown.match(/📉\s*\*\*承壓[/／]回調\*\*[：:]\s*(.+)/);
  if (bearMatch) {
    result.bearish = bearMatch[1].split(/[,，、]/).map(s => s.trim()).filter(Boolean);
  }

  return result;
}

export default function SectorView({ markdown }: SectorViewProps) {
  const sectors = useMemo(() => markdown ? extractSectors(markdown) : null, [markdown]);

  if (!sectors || (sectors.bullish.length === 0 && sectors.bearish.length === 0)) return null;

  return (
    <div className="rounded-lg p-4 mb-4" style={{ background: 'var(--bg-card)', border: '1px solid var(--border)' }}>
      <span className="text-xs font-bold tracking-wider mb-3 block" style={{ color: 'var(--accent-cyan)' }}>
        📊 SECTOR VIEW
      </span>

      {sectors.bullish.length > 0 && (
        <div className="mb-2">
          <span className="text-[10px] uppercase tracking-wider" style={{ color: 'var(--accent-green)' }}>
            ▲ BULLISH
          </span>
          <div className="flex flex-wrap gap-1 mt-1">
            {sectors.bullish.map((s, i) => (
              <span key={i} className="text-[10px] px-2 py-0.5 rounded"
                style={{ background: 'rgba(0,229,153,0.1)', color: 'var(--accent-green)', border: '1px solid rgba(0,229,153,0.2)' }}>
                {s}
              </span>
            ))}
          </div>
        </div>
      )}

      {sectors.bearish.length > 0 && (
        <div>
          <span className="text-[10px] uppercase tracking-wider" style={{ color: 'var(--accent-red)' }}>
            ▼ BEARISH
          </span>
          <div className="flex flex-wrap gap-1 mt-1">
            {sectors.bearish.map((s, i) => (
              <span key={i} className="text-[10px] px-2 py-0.5 rounded"
                style={{ background: 'rgba(255,71,87,0.1)', color: 'var(--accent-red)', border: '1px solid rgba(255,71,87,0.2)' }}>
                {s}
              </span>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

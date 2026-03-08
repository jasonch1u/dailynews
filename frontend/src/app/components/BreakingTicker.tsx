'use client';

import { useMemo } from 'react';

interface BreakingTickerProps {
  markdown: string | null;
}

export default function BreakingTicker({ markdown }: BreakingTickerProps) {
  const headlines = useMemo(() => {
    if (!markdown) return [];
    // Extract topic titles
    const titleRegex = /### \d+\.\s*(?:\[[^\]]+\]\s*)?(.+)/g;
    const titles: string[] = [];
    let match;
    while ((match = titleRegex.exec(markdown)) !== null) {
      titles.push(match[1].trim());
    }
    return titles.slice(0, 10);
  }, [markdown]);

  if (headlines.length === 0) return null;

  const tickerText = headlines.map((h, i) => `${h}  ◆  `).join('');

  return (
    <div className="fixed bottom-0 left-0 right-0 z-50 h-8 flex items-center overflow-hidden"
      style={{
        background: 'rgba(10, 10, 15, 0.95)',
        borderTop: '1px solid var(--border)',
        backdropFilter: 'blur(8px)',
      }}>
      {/* BREAKING label */}
      <div className="shrink-0 px-3 h-full flex items-center gap-1.5"
        style={{ background: 'var(--accent-red)', zIndex: 1 }}>
        <span className="w-1.5 h-1.5 rounded-full pulse-dot" style={{ background: '#fff' }} />
        <span className="text-[10px] font-bold tracking-wider text-white">BREAKING</span>
      </div>

      {/* Scrolling text */}
      <div className="flex-1 overflow-hidden whitespace-nowrap">
        <span className="inline-block ticker-scroll text-[11px]"
          style={{ color: 'var(--text-secondary)' }}>
          {tickerText}{tickerText}
        </span>
      </div>
    </div>
  );
}

'use client';

interface AIBriefProps {
  markdown: string | null;
  isLoading: boolean;
  loadingStatus: string;
  loadingStep: number;
}

function extractBrief(markdown: string): { sentiment: string; keywords: string; takeaways: string[] } {
  const result = { sentiment: '', keywords: '', takeaways: [] as string[] };

  // Extract market sentiment line
  const sentimentMatch = markdown.match(/\*\*市場情緒\*\*[：:]\s*(.+)/);
  if (sentimentMatch) result.sentiment = sentimentMatch[1].trim();

  // Extract keywords
  const keywordsMatch = markdown.match(/\*\*熱門關鍵字\*\*[：:]\s*(.+)/);
  if (keywordsMatch) result.keywords = keywordsMatch[1].trim();

  // Extract key takeaways
  const takeawaySection = markdown.match(/關鍵結論[\s\S]*?\n([\s\S]*?)(?=\n##|\n---)/);
  if (takeawaySection) {
    const lines = takeawaySection[1].split('\n').filter(l => l.trim().startsWith('*') || l.trim().startsWith('-'));
    result.takeaways = lines.map(l => l.replace(/^[\s*-]+/, '').trim()).filter(Boolean).slice(0, 3);
  }

  return result;
}

export default function AIBrief({ markdown, isLoading, loadingStatus, loadingStep }: AIBriefProps) {
  if (isLoading) {
    return (
      <div className="rounded-lg p-4 mb-4" style={{ background: 'var(--bg-card)', border: '1px solid var(--border)' }}>
        <div className="flex items-center gap-2 mb-3">
          <span className="text-xs font-bold tracking-wider" style={{ color: 'var(--accent-purple)' }}>
            🤖 AI BRIEF
          </span>
          <span className="w-1.5 h-1.5 rounded-full pulse-dot" style={{ background: 'var(--accent-orange)' }} />
        </div>

        {/* Progress */}
        <div className="mb-2">
          <div className="flex gap-1 mb-2">
            {[1, 2, 3].map((s) => (
              <div key={s} className="h-1 flex-1 rounded-full transition-all duration-500"
                style={{
                  background: s <= loadingStep ? 'var(--accent-cyan)' : 'var(--bg-primary)',
                  boxShadow: s <= loadingStep ? '0 0 6px var(--accent-cyan)' : 'none',
                }}
              />
            ))}
          </div>
          <span className="text-[11px]" style={{ color: 'var(--text-muted)' }}>{loadingStatus || 'Initializing...'}</span>
        </div>
      </div>
    );
  }

  if (!markdown) {
    return (
      <div className="rounded-lg p-4 mb-4" style={{ background: 'var(--bg-card)', border: '1px solid var(--border)' }}>
        <div className="flex items-center gap-2 mb-2">
          <span className="text-xs font-bold tracking-wider" style={{ color: 'var(--accent-purple)' }}>
            🤖 AI BRIEF
          </span>
        </div>
        <p className="text-xs" style={{ color: 'var(--text-muted)' }}>
          No summary available. Click REFRESH to generate.
        </p>
      </div>
    );
  }

  const brief = extractBrief(markdown);

  return (
    <div className="rounded-lg p-4 mb-4" style={{ background: 'var(--bg-card)', border: '1px solid var(--border)' }}>
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <span className="text-xs font-bold tracking-wider" style={{ color: 'var(--accent-purple)' }}>
            🤖 AI BRIEF
          </span>
          <span className="w-1.5 h-1.5 rounded-full" style={{ background: 'var(--accent-green)' }} />
        </div>
      </div>

      {/* Sentiment */}
      {brief.sentiment && (
        <div className="flex items-center gap-2 mb-2 p-2 rounded" style={{ background: 'var(--bg-primary)' }}>
          <span className="text-[10px] uppercase tracking-wider" style={{ color: 'var(--text-muted)' }}>SENTIMENT</span>
          <span className="text-xs font-semibold" style={{ color: 'var(--text-primary)' }}>
            {brief.sentiment}
          </span>
        </div>
      )}

      {/* Keywords */}
      {brief.keywords && (
        <div className="flex flex-wrap gap-1.5 mb-3">
          {brief.keywords.split(/[,，\s]+/).filter(k => k.startsWith('#')).map((tag, i) => (
            <span key={i} className="text-[11px] px-2 py-0.5 rounded"
              style={{ background: 'rgba(0, 212, 255, 0.1)', color: 'var(--accent-cyan)', border: '1px solid rgba(0, 212, 255, 0.2)' }}>
              {tag}
            </span>
          ))}
        </div>
      )}

      {/* Key Takeaways */}
      {brief.takeaways.length > 0 && (
        <div className="flex flex-col gap-1.5">
          {brief.takeaways.map((t, i) => (
            <div key={i} className="flex items-start gap-2 text-xs" style={{ color: 'var(--text-secondary)' }}>
              <span className="text-[10px] font-bold mt-0.5 shrink-0"
                style={{ color: 'var(--accent-yellow)' }}>{i + 1}.</span>
              <span className="leading-relaxed">{t}</span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

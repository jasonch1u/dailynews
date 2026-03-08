'use client';

import { useMemo } from 'react';

interface NewsFeedProps {
  markdown: string | null;
  activeCategory: string;
}

// Source color mapping
const SOURCE_COLORS: Record<string, string> = {
  'cnyes': '#dc3545',
  '鉅亨': '#dc3545',
  'blocktempo': '#fd7e14',
  '動區': '#fd7e14',
  'fox': '#0d6efd',
  'anduril': '#0d6efd',
  'cnbc': '#20c997',
  'seekingalpha': '#ffc107',
  'bbc': '#b80000',
  'cnn': '#cc0000',
  'techcrunch': '#00a562',
  'forbes': '#666',
  'businessinsider': '#444',
  'axios': '#2251ff',
  'nyt': '#999',
  'reuters': '#ff8000',
};

function getSourceColor(source: string): string {
  const lower = source.toLowerCase();
  for (const [key, color] of Object.entries(SOURCE_COLORS)) {
    if (lower.includes(key)) return color;
  }
  return '#6c757d';
}

// Categorize topics based on keywords
function categorize(text: string): string[] {
  const cats: string[] = [];
  const lower = text.toLowerCase();

  if (/crypto|bitcoin|btc|eth|加密|幣|defi|nft|blockchain|區塊鏈|穩定幣|usdc|usdt/.test(lower)) cats.push('crypto');
  if (/fed|inflation|gdp|利率|央行|cpi|sofr|treasury|fiscal|宏觀|macro|tariff|關稅|trade war/.test(lower)) cats.push('macro');
  if (/ai |artificial intelligence|openai|gemini|claude|nvidia|chip|半導體|gpu|llm|robot/.test(lower)) cats.push('tech');
  if (/geopolit|war|military|missile|sanction|制裁|戰爭|衝突|iran|ukraine|china|taiwan/.test(lower)) cats.push('geo');

  return cats.length > 0 ? cats : ['general'];
}

interface ParsedTopic {
  title: string;
  category: string;
  content: string;
  sentiment: string;
  sources: Array<{ name: string; title: string; url: string }>;
  rawIndex: number;
}

function parseTopics(markdown: string): ParsedTopic[] {
  const topics: ParsedTopic[] = [];

  // Match ### numbered topics
  const topicRegex = /### \d+\.\s*(?:\[([^\]]+)\]\s*)?(.+?)(?:\n)([\s\S]*?)(?=\n### \d+\.|\n## |$)/g;
  let match;
  let index = 0;

  while ((match = topicRegex.exec(markdown)) !== null) {
    const cat = match[1] || '';
    const title = match[2].trim();
    const body = match[3];

    // Extract sentiment
    const sentimentMatch = body.match(/\*\*情緒\*\*[：:]\s*\(?([\w/]+)\)?/);
    const sentiment = sentimentMatch ? sentimentMatch[1] : '';

    // Extract sources with links
    const sources: Array<{ name: string; title: string; url: string }> = [];
    const linkRegex = /[-*]\s*\[([^\]]+)\]\s*\[([^\]]+)\]\(([^)]+)\)/g;
    let linkMatch;
    while ((linkMatch = linkRegex.exec(body)) !== null) {
      sources.push({ name: linkMatch[1], title: linkMatch[2], url: linkMatch[3] });
    }

    // Clean content (remove source links and sentiment line)
    let content = body
      .replace(/\*\*情緒\*\*[：:].*\n?/g, '')
      .replace(/\*\*相關報導\*\*[\s\S]*?(?=\n\n|\n###|$)/g, '')
      .trim();

    // Remove leading empty lines
    content = content.split('\n').filter(l => l.trim()).join('\n');

    const categories = categorize(cat + ' ' + title + ' ' + content);

    topics.push({
      title: `${cat ? `[${cat}] ` : ''}${title}`,
      category: categories[0],
      content,
      sentiment,
      sources,
      rawIndex: index++,
    });
  }

  return topics;
}

function SentimentBadge({ sentiment }: { sentiment: string }) {
  if (!sentiment) return null;

  const isPositive = /正面|positive/i.test(sentiment);
  const isNegative = /負面|negative/i.test(sentiment);

  const color = isPositive ? 'var(--accent-green)' : isNegative ? 'var(--accent-red)' : 'var(--accent-cyan)';
  const bg = isPositive ? 'rgba(0,229,153,0.1)' : isNegative ? 'rgba(255,71,87,0.1)' : 'rgba(0,212,255,0.1)';

  return (
    <span className="text-[10px] px-1.5 py-0.5 rounded font-semibold"
      style={{ color, background: bg, border: `1px solid ${color}30` }}>
      {sentiment}
    </span>
  );
}

function TopicCard({ topic }: { topic: ParsedTopic }) {
  const catColor = topic.category === 'crypto' ? 'var(--accent-orange)'
    : topic.category === 'macro' ? 'var(--accent-cyan)'
    : topic.category === 'tech' ? 'var(--accent-purple)'
    : topic.category === 'geo' ? 'var(--accent-red)'
    : 'var(--text-muted)';

  return (
    <div className="rounded-lg p-4 card-hover" style={{ background: 'var(--bg-card)', border: '1px solid var(--border)' }}>
      {/* Header */}
      <div className="flex items-start justify-between gap-2 mb-2">
        <div className="flex items-center gap-2 flex-wrap">
          <span className="text-[10px] font-bold uppercase px-1.5 py-0.5 rounded"
            style={{ color: catColor, background: `${catColor}15`, border: `1px solid ${catColor}30` }}>
            {topic.category}
          </span>
          <SentimentBadge sentiment={topic.sentiment} />
        </div>
        <span className="text-[10px] shrink-0" style={{ color: 'var(--text-muted)' }}>
          #{topic.rawIndex + 1}
        </span>
      </div>

      {/* Title */}
      <h3 className="text-sm font-semibold mb-2" style={{ color: 'var(--text-primary)' }}>
        {topic.title.replace(/^\[\w+\]\s*/, '')}
      </h3>

      {/* Content */}
      <p className="text-xs leading-relaxed mb-3" style={{ color: 'var(--text-secondary)' }}>
        {topic.content.slice(0, 300)}{topic.content.length > 300 ? '...' : ''}
      </p>

      {/* Sources */}
      {topic.sources.length > 0 && (
        <div className="flex flex-wrap gap-1">
          {topic.sources.map((s, i) => (
            <a key={i} href={s.url} target="_blank" rel="noopener noreferrer"
              className="text-[10px] px-1.5 py-0.5 rounded no-underline transition-opacity hover:opacity-80"
              style={{ background: getSourceColor(s.name), color: '#fff' }}>
              {s.name}
            </a>
          ))}
        </div>
      )}
    </div>
  );
}

const CATEGORIES = [
  { id: 'all', label: 'ALL', icon: '🌐' },
  { id: 'crypto', label: 'CRYPTO', icon: '₿' },
  { id: 'macro', label: 'MACRO', icon: '🏦' },
  { id: 'tech', label: 'TECH', icon: '🤖' },
  { id: 'geo', label: 'GEO', icon: '⚔️' },
];

export function CategoryTabs({ active, onChange }: { active: string; onChange: (cat: string) => void }) {
  return (
    <div className="flex gap-1 mb-4 overflow-x-auto pb-1">
      {CATEGORIES.map((cat) => (
        <button
          key={cat.id}
          onClick={() => onChange(cat.id)}
          className="text-[11px] px-3 py-1.5 rounded font-semibold whitespace-nowrap transition-all"
          style={{
            background: active === cat.id ? 'rgba(0, 212, 255, 0.15)' : 'var(--bg-card)',
            border: `1px solid ${active === cat.id ? 'var(--accent-cyan)' : 'var(--border)'}`,
            color: active === cat.id ? 'var(--accent-cyan)' : 'var(--text-muted)',
          }}
        >
          {cat.icon} {cat.label}
        </button>
      ))}
    </div>
  );
}

export default function NewsFeed({ markdown, activeCategory }: NewsFeedProps) {
  const topics = useMemo(() => markdown ? parseTopics(markdown) : [], [markdown]);

  const filteredTopics = useMemo(() => {
    if (activeCategory === 'all') return topics;
    return topics.filter(t => t.category === activeCategory);
  }, [topics, activeCategory]);

  // Extract "Other News" section
  const otherNews = useMemo(() => {
    if (!markdown) return '';
    const otherMatch = markdown.match(/## 📰 其他快訊[\s\S]*?(?=\n## |$)/);
    return otherMatch ? otherMatch[0] : '';
  }, [markdown]);

  if (!markdown) {
    return (
      <div className="flex items-center justify-center py-16">
        <div className="text-center">
          <span className="text-4xl mb-4 block">📰</span>
          <p className="text-sm" style={{ color: 'var(--text-muted)' }}>
            Select a date or click REFRESH to load news
          </p>
        </div>
      </div>
    );
  }

  return (
    <div>
      {/* Topic Cards */}
      <div className="flex flex-col gap-3">
        {filteredTopics.length > 0 ? (
          filteredTopics.map((topic) => (
            <TopicCard key={topic.rawIndex} topic={topic} />
          ))
        ) : (
          <div className="text-center py-8">
            <span className="text-xs" style={{ color: 'var(--text-muted)' }}>
              No topics in this category
            </span>
          </div>
        )}
      </div>

      {/* Other News (raw markdown) */}
      {activeCategory === 'all' && otherNews && (
        <div className="mt-4 rounded-lg p-4" style={{ background: 'var(--bg-card)', border: '1px solid var(--border)' }}>
          <span className="text-xs font-bold tracking-wider mb-2 block" style={{ color: 'var(--text-muted)' }}>
            📰 OTHER NEWS
          </span>
          <div className="news-content text-xs" dangerouslySetInnerHTML={{
            __html: simpleMarkdown(otherNews.replace(/^## 📰 其他快訊.*\n/, ''))
          }} />
        </div>
      )}
    </div>
  );
}

// Minimal markdown renderer for other news section
function simpleMarkdown(md: string): string {
  return md
    .replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2" target="_blank" rel="noopener noreferrer">$1</a>')
    .replace(/^[-*]\s+(.+)/gm, '<li>$1</li>')
    .replace(/(<li>.*<\/li>\n?)+/g, '<ul>$&</ul>')
    .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
    .replace(/\n/g, '<br>');
}

'use client';

import type { Article } from '@/lib/api';
import { useMemo } from 'react';

interface NewsFeedProps {
  markdown: string | null;
  activeCategory: string;
  searchQuery: string;
  serverSearchResults: Article[];
  isServerSearching: boolean;
}

// Source metadata with colors, reliability, and favicon
const SOURCE_META: Record<string, { color: string; reliability: number; icon: string; label: string }> = {
  'cnyes':          { color: '#dc3545', reliability: 4, icon: '🔴', label: 'Cnyes 鉅亨' },
  '鉅亨':          { color: '#dc3545', reliability: 4, icon: '🔴', label: 'Cnyes 鉅亨' },
  'blocktempo':    { color: '#fd7e14', reliability: 4, icon: '🟠', label: '動區 BlockTempo' },
  '動區':          { color: '#fd7e14', reliability: 4, icon: '🟠', label: '動區 BlockTempo' },
  'fox':           { color: '#0d6efd', reliability: 3, icon: '📺', label: 'FOX/Anduril' },
  'anduril':       { color: '#0d6efd', reliability: 3, icon: '📺', label: 'FOX/Anduril' },
  'cnbc':          { color: '#20c997', reliability: 5, icon: '💹', label: 'CNBC' },
  'seekingalpha':  { color: '#ffc107', reliability: 4, icon: '📊', label: 'SeekingAlpha' },
  'bbc':           { color: '#b80000', reliability: 5, icon: '🇬🇧', label: 'BBC' },
  'cnn':           { color: '#cc0000', reliability: 4, icon: '📡', label: 'CNN' },
  'techcrunch':    { color: '#00a562', reliability: 4, icon: '💻', label: 'TechCrunch' },
  'forbes':        { color: '#666666', reliability: 4, icon: '💼', label: 'Forbes' },
  'businessinsider': { color: '#444444', reliability: 3, icon: '📰', label: 'Business Insider' },
  'axios':         { color: '#2251ff', reliability: 4, icon: '⚡', label: 'Axios' },
  'nyt':           { color: '#999999', reliability: 5, icon: '🗽', label: 'NYT' },
  'reuters':       { color: '#ff8000', reliability: 5, icon: '🌐', label: 'Reuters' },
  'bloomberg':     { color: '#1a1a2e', reliability: 5, icon: '🏦', label: 'Bloomberg' },
  'ft':            { color: '#f2c7a7', reliability: 5, icon: '📜', label: 'Financial Times' },
  'wsj':           { color: '#444444', reliability: 5, icon: '📰', label: 'WSJ' },
  'coindesk':      { color: '#2962ff', reliability: 4, icon: '₿', label: 'CoinDesk' },
  'theblock':      { color: '#000000', reliability: 4, icon: '⬛', label: 'The Block' },
};

function getSourceMeta(source: string): { color: string; reliability: number; icon: string; label: string } {
  const lower = source.toLowerCase();
  for (const [key, meta] of Object.entries(SOURCE_META)) {
    if (lower.includes(key)) return meta;
  }
  return { color: '#6c757d', reliability: 3, icon: '📄', label: source };
}

function reliabilityLabel(score: number): { text: string; color: string } {
  if (score >= 5) return { text: '★★★', color: '#ffd700' };
  if (score >= 4) return { text: '★★', color: '#ffc107' };
  if (score >= 3) return { text: '★', color: '#888' };
  return { text: '—', color: '#555' };
}

// Categorize topics based on keywords
function categorize(text: string): string[] {
  const cats: string[] = [];
  const lower = text.toLowerCase();

  if (/crypto|bitcoin|btc|eth|加密|幣|defi|nft|blockchain|區塊鏈|穩定幣|usdc|usdt/.test(lower)) cats.push('crypto');
  if (/fed|inflation|gdp|利率|央行|cpi|sofr|treasury|fiscal|宏觀|macro|tariff|關稅|trade war|油價|原油|oil/.test(lower)) cats.push('macro');
  if (/ai |artificial intelligence|openai|gemini|claude|nvidia|chip|半導體|gpu|llm|robot|台積電/.test(lower)) cats.push('tech');
  if (/geopolit|war|military|missile|sanction|制裁|戰爭|衝突|iran|ukraine|china|taiwan|中東|荷姆茲/.test(lower)) cats.push('geo');

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

  const topicRegex = /### \d+\.\s*(?:\[([^\]]+)\]\s*)?(.+?)(?:\n)([\s\S]*?)(?=\n### \d+\.|\n## |$)/g;
  let match;
  let index = 0;

  while ((match = topicRegex.exec(markdown)) !== null) {
    const cat = match[1] || '';
    const title = match[2].trim();
    const body = match[3];

    const sentimentMatch = body.match(/\*\*情緒\*\*[：:]\s*\(?([\w/（）\s]+)\)?/);
    const sentiment = sentimentMatch ? sentimentMatch[1].trim() : '';

    const sources: Array<{ name: string; title: string; url: string }> = [];
    const linkRegex = /[-*]\s*\[([^\]]+)\]\s*\[([^\]]+)\]\(([^)]+)\)/g;
    let linkMatch;
    while ((linkMatch = linkRegex.exec(body)) !== null) {
      sources.push({ name: linkMatch[1], title: linkMatch[2], url: linkMatch[3] });
    }

    let content = body
      .replace(/\*\*情緒\*\*[：:].*\n?/g, '')
      .replace(/\*\*相關報導\*\*[\s\S]*?(?=\n\n|\n###|$)/g, '')
      .trim();

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

function SourceBadge({ source }: { source: { name: string; title: string; url: string } }) {
  const meta = getSourceMeta(source.name);
  const rel = reliabilityLabel(meta.reliability);

  return (
    <a href={source.url} target="_blank" rel="noopener noreferrer"
      className="inline-flex items-center gap-1 text-[10px] px-1.5 py-0.5 rounded no-underline transition-all hover:brightness-125 group"
      style={{ background: meta.color, color: '#fff' }}
      title={`${meta.label} — Reliability: ${rel.text}\n${source.title}`}
    >
      <span>{meta.icon}</span>
      <span>{source.name}</span>
      <span style={{ color: rel.color, fontSize: '8px' }}>{rel.text}</span>
    </a>
  );
}

function TopicCard({ topic }: { topic: ParsedTopic }) {
  const catColor = topic.category === 'crypto' ? 'var(--accent-orange)'
    : topic.category === 'macro' ? 'var(--accent-cyan)'
    : topic.category === 'tech' ? 'var(--accent-purple)'
    : topic.category === 'geo' ? 'var(--accent-red)'
    : 'var(--text-muted)';

  const catIcon = topic.category === 'crypto' ? '₿'
    : topic.category === 'macro' ? '🏦'
    : topic.category === 'tech' ? '🤖'
    : topic.category === 'geo' ? '⚔️'
    : '📰';

  return (
    <div className="rounded-lg p-4 card-hover" style={{ background: 'var(--bg-card)', border: '1px solid var(--border)' }}>
      {/* Header */}
      <div className="flex items-start justify-between gap-2 mb-2">
        <div className="flex items-center gap-2 flex-wrap">
          <span className="text-[10px] font-bold uppercase px-1.5 py-0.5 rounded inline-flex items-center gap-1"
            style={{ color: catColor, background: `${catColor}15`, border: `1px solid ${catColor}30` }}>
            <span>{catIcon}</span>
            {topic.category}
          </span>
          <SentimentBadge sentiment={topic.sentiment} />
        </div>
        <span className="text-[10px] shrink-0 font-mono" style={{ color: 'var(--text-muted)' }}>
          #{topic.rawIndex + 1}
        </span>
      </div>

      {/* Title */}
      <h3 className="text-sm font-semibold mb-2 leading-snug" style={{ color: 'var(--text-primary)' }}>
        {topic.title.replace(/^\[\w+\]\s*/, '')}
      </h3>

      {/* Content */}
      <p className="text-xs leading-relaxed mb-3" style={{ color: 'var(--text-secondary)' }}>
        {topic.content.slice(0, 400)}{topic.content.length > 400 ? '...' : ''}
      </p>

      {/* Sources with favicons + reliability */}
      {topic.sources.length > 0 && (
        <div className="flex flex-wrap gap-1.5">
          {topic.sources.map((s, i) => (
            <SourceBadge key={i} source={s} />
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

export default function NewsFeed({
  markdown,
  activeCategory,
  searchQuery,
  serverSearchResults,
  isServerSearching,
}: NewsFeedProps) {
  const topics = useMemo(() => markdown ? parseTopics(markdown) : [], [markdown]);

  const filteredTopics = useMemo(() => {
    const categoryFiltered = activeCategory === 'all'
      ? topics
      : topics.filter((t) => t.category === activeCategory);

    if (!searchQuery) return categoryFiltered;
    const lower = searchQuery.toLowerCase();
    return categoryFiltered.filter((t) =>
      `${t.title} ${t.content}`.toLowerCase().includes(lower)
    );
  }, [topics, activeCategory, searchQuery]);

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
      {/* Topic count */}
      <div className="flex items-center justify-between mb-3">
        <span className="text-[10px] uppercase tracking-wider" style={{ color: 'var(--text-muted)' }}>
          {filteredTopics.length} topics
          {activeCategory !== 'all' ? ` in ${activeCategory}` : ''}
          {searchQuery ? ` · filter "${searchQuery}"` : ''}
        </span>
      </div>

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

      {searchQuery && (
        <div className="mt-4 rounded-lg p-4" style={{ background: 'var(--bg-card)', border: '1px solid var(--border)' }}>
          <span className="text-xs font-bold tracking-wider mb-2 block" style={{ color: 'var(--accent-cyan)' }}>
            🔍 SUPABASE SEARCH
          </span>
          {isServerSearching && (
            <p className="text-xs" style={{ color: 'var(--text-muted)' }}>
              Searching...
            </p>
          )}
          {!isServerSearching && serverSearchResults.length === 0 && (
            <p className="text-xs" style={{ color: 'var(--text-muted)' }}>
              Press Enter in search bar to run server-side search.
            </p>
          )}
          {!isServerSearching && serverSearchResults.length > 0 && (
            <div className="flex flex-col gap-2">
              {serverSearchResults.slice(0, 8).map((item) => (
                <a
                  key={item.id}
                  href={item.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="block rounded p-2 transition-colors"
                  style={{ background: 'var(--bg-primary)', border: '1px solid var(--border)' }}
                >
                  <p className="text-xs font-semibold mb-1" style={{ color: 'var(--text-primary)' }}>{item.title}</p>
                  <p className="text-[10px]" style={{ color: 'var(--text-muted)' }}>{item.source}</p>
                </a>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Other News */}
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

function simpleMarkdown(md: string): string {
  return md
    .replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2" target="_blank" rel="noopener noreferrer">$1</a>')
    .replace(/^[-*]\s+(.+)/gm, '<li>$1</li>')
    .replace(/(<li>.*<\/li>\n?)+/g, '<ul>$&</ul>')
    .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
    .replace(/\n/g, '<br>');
}

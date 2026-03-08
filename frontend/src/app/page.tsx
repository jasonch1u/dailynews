'use client';

import { useState, useEffect, useCallback, useRef } from 'react';
import Header, { type HeaderHandle } from './components/Header';
import MarketRadar from './components/MarketRadar';
import AIBrief from './components/AIBrief';
import NewsFeed, { CategoryTabs } from './components/NewsFeed';
import SectorView from './components/SectorView';
import BreakingTicker from './components/BreakingTicker';
import GeoMap from './components/GeoMap';
import { fetchSummary, searchArticles, type Article } from '@/lib/api';
import { useKeyboardShortcuts } from '@/lib/useKeyboardShortcuts';

const SOURCES = [
  { name: 'Reuters', icon: '🌐', tier: 1 },
  { name: 'BBC', icon: '🇬🇧', tier: 1 },
  { name: 'CNBC', icon: '💹', tier: 1 },
  { name: 'NYT', icon: '🗽', tier: 1 },
  { name: 'Cnyes', icon: '🔴', tier: 2 },
  { name: '動區', icon: '🟠', tier: 2 },
  { name: 'TechCrunch', icon: '💻', tier: 2 },
  { name: 'Axios', icon: '⚡', tier: 2 },
  { name: 'Forbes', icon: '💼', tier: 2 },
  { name: 'SeekingAlpha', icon: '📊', tier: 2 },
  { name: 'CNN', icon: '📡', tier: 2 },
  { name: 'FOX', icon: '📺', tier: 3 },
  { name: 'BI', icon: '📰', tier: 3 },
];

export default function Dashboard() {
  const [selectedDate, setSelectedDate] = useState('');
  const [markdown, setMarkdown] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [loadingStatus, setLoadingStatus] = useState('');
  const [loadingStep, setLoadingStep] = useState(0);
  const [activeCategory, setActiveCategory] = useState('all');
  const [lastUpdated, setLastUpdated] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [debouncedSearchQuery, setDebouncedSearchQuery] = useState('');
  const [serverSearchResults, setServerSearchResults] = useState<Article[]>([]);
  const [isServerSearching, setIsServerSearching] = useState(false);

  const headerRef = useRef<HeaderHandle>(null);

  // Debounce search query
  useEffect(() => {
    const timer = window.setTimeout(() => setDebouncedSearchQuery(searchQuery.trim()), 250);
    return () => window.clearTimeout(timer);
  }, [searchQuery]);

  // Initial load
  useEffect(() => {
    loadSummary();
  }, []);

  const loadSummary = useCallback(async (date?: string) => {
    setIsLoading(true);
    setLoadingStatus('Fetching from Supabase...');
    setLoadingStep(1);

    const summary = await fetchSummary(date || undefined);
    if (summary) {
      setMarkdown(summary);
      setLastUpdated(new Date().toLocaleTimeString('en-US', {
        timeZone: 'Asia/Taipei',
        hour: '2-digit',
        minute: '2-digit',
        hour12: false,
      }));
    } else {
      setMarkdown(null);
    }
    setIsLoading(false);
    setLoadingStatus('');
    setLoadingStep(0);
  }, []);

  const handleDateChange = useCallback((date: string) => {
    setSelectedDate(date);
    loadSummary(date);
  }, [loadSummary]);

  const handleRefresh = useCallback(() => {
    loadSummary(selectedDate || undefined);
  }, [selectedDate, loadSummary]);

  const handleServerSearch = useCallback(async (query: string) => {
    const trimmed = query.trim();
    if (!trimmed) {
      setServerSearchResults([]);
      return;
    }
    setIsServerSearching(true);
    const results = await searchArticles(trimmed);
    setServerSearchResults(results);
    setIsServerSearching(false);
  }, []);

  // Keyboard shortcuts
  useKeyboardShortcuts({
    onSearch: () => headerRef.current?.focusSearch(),
    onRefresh: handleRefresh,
    onCategoryChange: setActiveCategory,
    onEscape: () => {
      setSearchQuery('');
      setServerSearchResults([]);
    },
  });

  return (
    <div className="min-h-screen pb-10" style={{ background: 'var(--bg-primary)' }}>
      <Header
        ref={headerRef}
        selectedDate={selectedDate}
        onDateChange={handleDateChange}
        onRefresh={handleRefresh}
        isLoading={isLoading}
        searchQuery={searchQuery}
        onSearchChange={setSearchQuery}
        onSearchSubmit={handleServerSearch}
      />

      {/* Main Content — pt-[7.5rem] accounts for fixed header + search bar */}
      <main className="pt-[7.5rem] px-3 md:px-6 max-w-[1600px] mx-auto">
        <div className="grid grid-cols-1 lg:grid-cols-[1fr_320px] gap-4">

          {/* Left Column: News */}
          <div className="min-w-0">
            <AIBrief
              markdown={markdown}
              isLoading={isLoading}
              loadingStatus={loadingStatus}
              loadingStep={loadingStep}
            />

            <GeoMap markdown={markdown} />

            <CategoryTabs active={activeCategory} onChange={setActiveCategory} />

            <NewsFeed
              markdown={markdown}
              activeCategory={activeCategory}
              searchQuery={debouncedSearchQuery}
              serverSearchResults={serverSearchResults}
              isServerSearching={isServerSearching}
            />
          </div>

          {/* Right Column: Sidebar */}
          <div className="flex flex-col gap-4">
            <MarketRadar />
            <SectorView markdown={markdown} />

            {/* Sources Panel */}
            <div className="rounded-lg p-4" style={{ background: 'var(--bg-card)', border: '1px solid var(--border)' }}>
              <span className="text-xs font-bold tracking-wider mb-3 block" style={{ color: 'var(--accent-cyan)' }}>
                📡 INTELLIGENCE SOURCES
              </span>

              <div className="mb-2">
                <span className="text-[9px] uppercase tracking-wider" style={{ color: 'var(--accent-yellow)' }}>
                  ★★★ TIER 1
                </span>
                <div className="flex flex-wrap gap-1 mt-1">
                  {SOURCES.filter(s => s.tier === 1).map((s) => (
                    <span key={s.name} className="text-[10px] px-1.5 py-0.5 rounded inline-flex items-center gap-0.5"
                      style={{ background: 'rgba(255,215,0,0.08)', color: 'var(--accent-yellow)', border: '1px solid rgba(255,215,0,0.2)' }}>
                      <span>{s.icon}</span> {s.name}
                    </span>
                  ))}
                </div>
              </div>

              <div className="mb-2">
                <span className="text-[9px] uppercase tracking-wider" style={{ color: 'var(--text-muted)' }}>
                  ★★ TIER 2
                </span>
                <div className="flex flex-wrap gap-1 mt-1">
                  {SOURCES.filter(s => s.tier === 2).map((s) => (
                    <span key={s.name} className="text-[10px] px-1.5 py-0.5 rounded inline-flex items-center gap-0.5"
                      style={{ background: 'var(--bg-primary)', color: 'var(--text-muted)', border: '1px solid var(--border)' }}>
                      <span>{s.icon}</span> {s.name}
                    </span>
                  ))}
                </div>
              </div>

              <div className="mb-2">
                <span className="text-[9px] uppercase tracking-wider" style={{ color: 'var(--text-muted)' }}>
                  ★ TIER 3
                </span>
                <div className="flex flex-wrap gap-1 mt-1">
                  {SOURCES.filter(s => s.tier === 3).map((s) => (
                    <span key={s.name} className="text-[10px] px-1.5 py-0.5 rounded inline-flex items-center gap-0.5"
                      style={{ background: 'var(--bg-primary)', color: 'var(--text-muted)', border: '1px solid var(--border)' }}>
                      <span>{s.icon}</span> {s.name}
                    </span>
                  ))}
                </div>
              </div>

              <div className="mt-3 pt-2 flex items-center justify-between" style={{ borderTop: '1px solid var(--border)' }}>
                <span className="text-[10px]" style={{ color: 'var(--text-muted)' }}>
                  {SOURCES.length} sources · AI by Gemini Flash
                </span>
                {lastUpdated && (
                  <span className="text-[10px]" style={{ color: 'var(--accent-green)' }}>
                    Updated {lastUpdated}
                  </span>
                )}
              </div>
            </div>

            {/* Keyboard Shortcuts Help (desktop only) */}
            <div className="hidden lg:block rounded-lg p-3" style={{ background: 'var(--bg-card)', border: '1px solid var(--border)' }}>
              <span className="text-[10px] font-bold tracking-wider mb-2 block" style={{ color: 'var(--text-muted)' }}>
                ⌨️ SHORTCUTS
              </span>
              <div className="grid grid-cols-2 gap-1 text-[10px]" style={{ color: 'var(--text-muted)' }}>
                <span><kbd className="px-1 rounded" style={{ background: 'var(--bg-primary)', border: '1px solid var(--border)' }}>/</kbd> Search</span>
                <span><kbd className="px-1 rounded" style={{ background: 'var(--bg-primary)', border: '1px solid var(--border)' }}>r</kbd> Refresh</span>
                <span><kbd className="px-1 rounded" style={{ background: 'var(--bg-primary)', border: '1px solid var(--border)' }}>0</kbd> All</span>
                <span><kbd className="px-1 rounded" style={{ background: 'var(--bg-primary)', border: '1px solid var(--border)' }}>1</kbd> Crypto</span>
                <span><kbd className="px-1 rounded" style={{ background: 'var(--bg-primary)', border: '1px solid var(--border)' }}>2</kbd> Macro</span>
                <span><kbd className="px-1 rounded" style={{ background: 'var(--bg-primary)', border: '1px solid var(--border)' }}>3</kbd> Tech</span>
                <span><kbd className="px-1 rounded" style={{ background: 'var(--bg-primary)', border: '1px solid var(--border)' }}>4</kbd> Geo</span>
                <span><kbd className="px-1 rounded" style={{ background: 'var(--bg-primary)', border: '1px solid var(--border)' }}>Esc</kbd> Clear</span>
              </div>
            </div>
          </div>
        </div>
      </main>

      <BreakingTicker markdown={markdown} />
    </div>
  );
}

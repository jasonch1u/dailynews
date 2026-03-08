'use client';

import { useState, useEffect, useCallback } from 'react';
import Header from './components/Header';
import MarketRadar from './components/MarketRadar';
import AIBrief from './components/AIBrief';
import NewsFeed, { CategoryTabs } from './components/NewsFeed';
import SectorView from './components/SectorView';
import BreakingTicker from './components/BreakingTicker';
import { fetchSummary, streamSummary, type SummaryResponse } from '@/lib/api';

export default function Dashboard() {
  const [selectedDate, setSelectedDate] = useState('');
  const [markdown, setMarkdown] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [loadingStatus, setLoadingStatus] = useState('');
  const [loadingStep, setLoadingStep] = useState(0);
  const [activeCategory, setActiveCategory] = useState('all');

  // Load today's summary on mount
  useEffect(() => {
    loadSummary();
  }, []);

  const loadSummary = useCallback(async (date?: string) => {
    setIsLoading(true);
    setLoadingStatus('Fetching cached summary...');
    setLoadingStep(1);

    const summary = await fetchSummary(date || undefined);
    if (summary) {
      setMarkdown(summary);
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
    setIsLoading(true);
    setMarkdown(null);
    setLoadingStep(0);
    setLoadingStatus('Initializing...');

    const cleanup = streamSummary(
      (data: SummaryResponse) => {
        if (data.status) {
          setLoadingStatus(data.status);
          if (data.step) setLoadingStep(data.step);
        }
        if (data.markdown) {
          setMarkdown(data.markdown);
        }
        if (data.error) {
          setLoadingStatus(`Error: ${data.error}`);
        }
      },
      (err) => {
        setLoadingStatus(`Error: ${err}`);
      },
      () => {
        setIsLoading(false);
      }
    );

    // Cleanup on unmount
    return cleanup;
  }, []);

  return (
    <div className="min-h-screen pb-10" style={{ background: 'var(--bg-primary)' }}>
      <Header
        selectedDate={selectedDate}
        onDateChange={handleDateChange}
        onRefresh={handleRefresh}
        isLoading={isLoading}
      />

      {/* Main Content */}
      <main className="pt-16 px-3 md:px-6 max-w-[1600px] mx-auto">
        <div className="grid grid-cols-1 lg:grid-cols-[1fr_320px] gap-4">

          {/* Left Column: News */}
          <div className="min-w-0">
            {/* AI Brief */}
            <AIBrief
              markdown={markdown}
              isLoading={isLoading}
              loadingStatus={loadingStatus}
              loadingStep={loadingStep}
            />

            {/* Category Tabs */}
            <CategoryTabs active={activeCategory} onChange={setActiveCategory} />

            {/* News Feed */}
            <NewsFeed markdown={markdown} activeCategory={activeCategory} />
          </div>

          {/* Right Column: Sidebar */}
          <div className="flex flex-col gap-4">
            {/* Market Radar */}
            <MarketRadar />

            {/* Sector View */}
            <SectorView markdown={markdown} />

            {/* Stats card */}
            <div className="rounded-lg p-4" style={{ background: 'var(--bg-card)', border: '1px solid var(--border)' }}>
              <span className="text-xs font-bold tracking-wider mb-2 block" style={{ color: 'var(--accent-cyan)' }}>
                ℹ️ SOURCES
              </span>
              <div className="flex flex-wrap gap-1">
                {['FOX', '動區', 'Cnyes', 'CNBC', 'SeekingAlpha', 'BBC', 'CNN', 'TechCrunch', 'Forbes', 'BI', 'Axios', 'NYT', 'Reuters'].map((s) => (
                  <span key={s} className="text-[10px] px-1.5 py-0.5 rounded"
                    style={{ background: 'var(--bg-primary)', color: 'var(--text-muted)', border: '1px solid var(--border)' }}>
                    {s}
                  </span>
                ))}
              </div>
              <div className="mt-2 text-[10px]" style={{ color: 'var(--text-muted)' }}>
                13 sources · AI by Gemini Flash · Macro by XinGPT
              </div>
            </div>
          </div>
        </div>
      </main>

      {/* Breaking Ticker */}
      <BreakingTicker markdown={markdown} />
    </div>
  );
}

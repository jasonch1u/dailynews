'use client';

import { useState, useEffect } from 'react';
import { fetchHistoryDates } from '@/lib/api';

interface HeaderProps {
  selectedDate: string;
  onDateChange: (date: string) => void;
  onRefresh: () => void;
  isLoading: boolean;
  searchQuery: string;
  onSearchChange: (query: string) => void;
  onSearchSubmit: (query: string) => void;
}

export default function Header({
  selectedDate,
  onDateChange,
  onRefresh,
  isLoading,
  searchQuery,
  onSearchChange,
  onSearchSubmit,
}: HeaderProps) {
  const [dates, setDates] = useState<string[]>([]);

  useEffect(() => {
    fetchHistoryDates().then(setDates);
  }, []);

  const today = new Date().toLocaleDateString('sv-SE', { timeZone: 'Asia/Taipei' });
  const isToday = !selectedDate || selectedDate === today;

  return (
    <header
      className="fixed top-0 left-0 right-0 z-50"
      style={{ background: 'rgba(10, 10, 15, 0.95)', backdropFilter: 'blur(12px)', borderBottom: '1px solid var(--border)' }}
    >
      <div className="h-14 flex items-center justify-between px-4 md:px-6">
        {/* Left: Logo + Title */}
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2">
            <span className="text-lg">📡</span>
            <h1 className="text-sm md:text-base font-bold tracking-wider" style={{ color: 'var(--accent-cyan)' }}>
              WORLD<span style={{ color: 'var(--text-primary)' }}>MONITOR</span>
            </h1>
          </div>
          <div className="hidden md:flex items-center gap-1.5 px-2 py-0.5 rounded text-xs"
            style={{ background: 'rgba(0, 229, 153, 0.1)', border: '1px solid rgba(0, 229, 153, 0.3)' }}>
            <span className="w-1.5 h-1.5 rounded-full pulse-dot" style={{ background: 'var(--accent-green)' }} />
            <span style={{ color: 'var(--accent-green)' }}>LIVE</span>
          </div>
          <span className="hidden lg:inline text-[10px] px-2 py-0.5 rounded"
            style={{ background: 'rgba(168, 85, 247, 0.1)', color: 'var(--accent-purple)', border: '1px solid rgba(168, 85, 247, 0.3)' }}>
            AI-POWERED
          </span>
        </div>

        {/* Center: Time */}
        <div className="hidden md:block text-xs tracking-widest" style={{ color: 'var(--text-muted)' }}>
          <LiveClock />
        </div>

        {/* Right: Controls */}
        <div className="flex items-center gap-2">
          <select
            value={selectedDate || today}
            onChange={(e) => onDateChange(e.target.value === today ? '' : e.target.value)}
            className="text-xs px-2 py-1.5 rounded cursor-pointer"
            style={{
              background: 'var(--bg-card)',
              border: '1px solid var(--border)',
              color: 'var(--text-secondary)',
            }}
          >
            <option value={today}>TODAY</option>
            {dates.map((d) => (
              <option key={d} value={d}>{d}</option>
            ))}
          </select>

          <button
            onClick={onRefresh}
            disabled={isLoading}
            className="text-xs px-3 py-1.5 rounded font-semibold transition-all disabled:opacity-40"
            style={{
              background: isLoading ? 'var(--bg-card)' : 'rgba(0, 212, 255, 0.15)',
              border: '1px solid var(--accent-cyan)',
              color: 'var(--accent-cyan)',
            }}
          >
            {isLoading ? '⏳ LOADING...' : '⚡ REFRESH'}
          </button>
        </div>
      </div>

      <div className="px-4 md:px-6 pb-3">
        <form
          onSubmit={(e) => {
            e.preventDefault();
            onSearchSubmit(searchQuery);
          }}
          className="w-full"
        >
          <label
            className="flex items-center gap-2 rounded px-3 py-2"
            style={{ background: 'var(--bg-card)', border: '1px solid var(--border)' }}
          >
            <span className="text-sm" style={{ color: 'var(--text-muted)' }}>🔎</span>
            <input
              value={searchQuery}
              onChange={(e) => onSearchChange(e.target.value)}
              placeholder="Search title + content (press Enter for Supabase search)"
              className="w-full text-xs bg-transparent outline-none"
              style={{ color: 'var(--text-primary)' }}
            />
          </label>
        </form>
      </div>
    </header>
  );
}

function LiveClock() {
  const [time, setTime] = useState('');

  useEffect(() => {
    const update = () => {
      const now = new Date();
      setTime(now.toLocaleString('en-US', {
        timeZone: 'Asia/Taipei',
        weekday: 'short',
        day: '2-digit',
        month: 'short',
        year: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit',
        hour12: false,
      }).toUpperCase());
    };
    update();
    const interval = setInterval(update, 1000);
    return () => clearInterval(interval);
  }, []);

  return <span>{time} TST</span>;
}

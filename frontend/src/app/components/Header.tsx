'use client';

import { useState, useEffect, useRef, forwardRef, useImperativeHandle } from 'react';
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

export interface HeaderHandle {
  focusSearch: () => void;
}

const Header = forwardRef<HeaderHandle, HeaderProps>(function Header(
  { selectedDate, onDateChange, onRefresh, isLoading, searchQuery, onSearchChange, onSearchSubmit },
  ref
) {
  const [dates, setDates] = useState<string[]>([]);
  const [mobileSearchOpen, setMobileSearchOpen] = useState(false);
  const searchRef = useRef<HTMLInputElement>(null);

  useImperativeHandle(ref, () => ({
    focusSearch: () => {
      setMobileSearchOpen(true);
      setTimeout(() => searchRef.current?.focus(), 50);
    },
  }));

  useEffect(() => {
    fetchHistoryDates().then(setDates);
  }, []);

  const today = new Date().toLocaleDateString('sv-SE', { timeZone: 'Asia/Taipei' });

  return (
    <header
      className="fixed top-0 left-0 right-0 z-50"
      style={{ background: 'rgba(10, 10, 15, 0.95)', backdropFilter: 'blur(12px)', borderBottom: '1px solid var(--border)' }}
    >
      <div className="h-14 flex items-center justify-between px-3 md:px-6">
        {/* Left: Logo */}
        <div className="flex items-center gap-2 md:gap-3 shrink-0">
          <div className="flex items-center gap-1.5 md:gap-2">
            <span className="text-base md:text-lg">📡</span>
            <h1 className="text-xs md:text-base font-bold tracking-wider" style={{ color: 'var(--accent-cyan)' }}>
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

        {/* Center: Time (desktop only) */}
        <div className="hidden lg:block text-xs tracking-widest" style={{ color: 'var(--text-muted)' }}>
          <LiveClock />
        </div>

        {/* Right: Controls */}
        <div className="flex items-center gap-1.5 md:gap-2">
          {/* Mobile search toggle */}
          <button
            onClick={() => {
              setMobileSearchOpen(!mobileSearchOpen);
              if (!mobileSearchOpen) setTimeout(() => searchRef.current?.focus(), 50);
            }}
            className="md:hidden text-xs px-2 py-1.5 rounded"
            style={{ background: 'var(--bg-card)', border: '1px solid var(--border)', color: 'var(--text-muted)' }}
            aria-label="Toggle search"
          >
            🔎
          </button>

          <select
            value={selectedDate || today}
            onChange={(e) => onDateChange(e.target.value === today ? '' : e.target.value)}
            className="text-[11px] md:text-xs px-1.5 md:px-2 py-1.5 rounded cursor-pointer"
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
            className="text-[11px] md:text-xs px-2 md:px-3 py-1.5 rounded font-semibold transition-all disabled:opacity-40"
            style={{
              background: isLoading ? 'var(--bg-card)' : 'rgba(0, 212, 255, 0.15)',
              border: '1px solid var(--accent-cyan)',
              color: 'var(--accent-cyan)',
            }}
          >
            {isLoading ? '⏳' : '⚡'}
            <span className="hidden sm:inline"> {isLoading ? 'LOADING...' : 'REFRESH'}</span>
          </button>
        </div>
      </div>

      {/* Search bar — always visible on desktop, toggle on mobile */}
      <div className={`px-3 md:px-6 pb-3 ${mobileSearchOpen ? 'block' : 'hidden md:block'}`}>
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
              ref={searchRef}
              value={searchQuery}
              onChange={(e) => onSearchChange(e.target.value)}
              placeholder="Search news..."
              className="w-full text-xs bg-transparent outline-none"
              style={{ color: 'var(--text-primary)' }}
            />
            <kbd className="hidden md:inline-flex text-[9px] px-1.5 py-0.5 rounded items-center"
              style={{ background: 'var(--bg-primary)', color: 'var(--text-muted)', border: '1px solid var(--border)' }}>
              /
            </kbd>
          </label>
        </form>
      </div>
    </header>
  );
});

export default Header;

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

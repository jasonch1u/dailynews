'use client';

import { useEffect, useCallback } from 'react';

interface ShortcutHandlers {
  onSearch: () => void;
  onRefresh: () => void;
  onCategoryChange: (cat: string) => void;
  onEscape: () => void;
}

const CATEGORY_MAP: Record<string, string> = {
  '0': 'all',
  '1': 'crypto',
  '2': 'macro',
  '3': 'tech',
  '4': 'geo',
};

export function useKeyboardShortcuts(handlers: ShortcutHandlers) {
  const handleKeyDown = useCallback((e: KeyboardEvent) => {
    const target = e.target as HTMLElement;
    const isInput = target.tagName === 'INPUT' || target.tagName === 'TEXTAREA' || target.tagName === 'SELECT';

    // Escape always works
    if (e.key === 'Escape') {
      handlers.onEscape();
      (document.activeElement as HTMLElement)?.blur();
      return;
    }

    // Skip shortcuts when typing in input fields
    if (isInput) return;

    // `/` — focus search
    if (e.key === '/') {
      e.preventDefault();
      handlers.onSearch();
      return;
    }

    // `r` — refresh
    if (e.key === 'r' && !e.metaKey && !e.ctrlKey) {
      e.preventDefault();
      handlers.onRefresh();
      return;
    }

    // `0-4` — switch categories
    if (CATEGORY_MAP[e.key]) {
      e.preventDefault();
      handlers.onCategoryChange(CATEGORY_MAP[e.key]);
      return;
    }
  }, [handlers]);

  useEffect(() => {
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [handleKeyDown]);
}

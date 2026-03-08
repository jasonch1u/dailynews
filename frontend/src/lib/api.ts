// API helper — talks to the Python FastAPI backend
// In production on Vercel, both frontend and API are on the same domain
// In development, the API runs on a different port

import { MOCK_MACRO_SIGNAL, MOCK_SUMMARY, MOCK_DATES } from './mockData';

const API_BASE = process.env.NEXT_PUBLIC_API_BASE || '';
const USE_MOCK = process.env.NEXT_PUBLIC_USE_MOCK === 'true' || (!API_BASE && typeof window !== 'undefined');

export interface MacroSignal {
  date: string;
  sofr: number | null;
  tga_billion: number | null;
  vix: number | null;
  usdjpy: number | null;
  us10y: number | null;
  net_liq_billion: number | null;
  net_liq_weekly_change_pct: number | null;
  macro_score: number;
  macro_stance: 'BEARISH' | 'CAUTIOUS' | 'NEUTRAL' | 'BULLISH';
  crypto_action: string;
  triggers: Array<{
    type: 'DANGER' | 'WARNING' | 'POSITIVE';
    indicator: string;
    msg: string;
    action: string;
  }>;
  source: string;
}

export interface LiquidityData {
  date: string;
  net_liquidity: number;
  walcl: number;
  tga: number;
  rrp: number;
}

export interface EconomicIndicator {
  date: string;
  symbol: string;
  value: number;
}

export async function fetchMacroSignal(refresh = false): Promise<MacroSignal | null> {
  if (USE_MOCK) return MOCK_MACRO_SIGNAL;
  try {
    const res = await fetch(`${API_BASE}/api/macro-signal${refresh ? '?refresh=true' : ''}`, {
      cache: 'no-store',
    });
    if (!res.ok) return MOCK_MACRO_SIGNAL;
    return await res.json();
  } catch {
    return MOCK_MACRO_SIGNAL;
  }
}

export async function fetchLiquidity(): Promise<LiquidityData[]> {
  try {
    const res = await fetch(`${API_BASE}/api/liquidity`, { cache: 'no-store' });
    if (!res.ok) return [];
    const data = await res.json();
    return data.data || [];
  } catch {
    return [];
  }
}

export async function fetchEconomics(symbol?: string): Promise<EconomicIndicator[]> {
  try {
    const url = symbol
      ? `${API_BASE}/api/economics?symbol=${symbol}`
      : `${API_BASE}/api/economics`;
    const res = await fetch(url, { cache: 'no-store' });
    if (!res.ok) return [];
    const data = await res.json();
    return data.data || [];
  } catch {
    return [];
  }
}

export async function fetchHistoryDates(): Promise<string[]> {
  if (USE_MOCK) return MOCK_DATES;
  try {
    const res = await fetch(`${API_BASE}/api/history`, { cache: 'no-store' });
    if (!res.ok) return MOCK_DATES;
    const data = await res.json();
    return data.dates || [];
  } catch {
    return MOCK_DATES;
  }
}

export interface SummaryResponse {
  markdown?: string;
  source?: string;
  date?: string;
  status?: string;
  step?: number;
  error?: string;
}

export async function fetchSummary(date?: string): Promise<string | null> {
  if (USE_MOCK) return MOCK_SUMMARY;
  try {
    const url = date
      ? `${API_BASE}/api/summarize?date=${date}`
      : `${API_BASE}/api/summarize`;
    const res = await fetch(url, { cache: 'no-store' });
    if (!res.ok) return MOCK_SUMMARY;
    const data = await res.json();
    return data.markdown || null;
  } catch {
    return MOCK_SUMMARY;
  }
}

// SSE streaming for live generation
export function streamSummary(
  onMessage: (data: SummaryResponse) => void,
  onError: (err: string) => void,
  onDone: () => void
): () => void {
  const url = `${API_BASE}/api/summarize?refresh=true`;
  const eventSource = new EventSource(url);

  eventSource.onmessage = (event) => {
    try {
      const data: SummaryResponse = JSON.parse(event.data);
      onMessage(data);
      if (data.markdown) {
        eventSource.close();
        onDone();
      }
    } catch {
      // ignore parse errors
    }
  };

  eventSource.onerror = () => {
    onError('Connection lost');
    eventSource.close();
    onDone();
  };

  // Return cleanup function
  return () => eventSource.close();
}

export async function fetchArticles(date: string) {
  try {
    const res = await fetch(`${API_BASE}/api/articles?date=${date}`, { cache: 'no-store' });
    if (!res.ok) return [];
    const data = await res.json();
    return data.articles || [];
  } catch {
    return [];
  }
}

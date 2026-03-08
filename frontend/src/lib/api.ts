// API helper — talks directly to Supabase (no backend needed)
// Cron script handles scraping + summarization, frontend just reads

const SUPABASE_URL = process.env.NEXT_PUBLIC_SUPABASE_URL || '';
const SUPABASE_ANON_KEY = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY || '';

const supabaseHeaders = {
  'apikey': SUPABASE_ANON_KEY,
  'Authorization': `Bearer ${SUPABASE_ANON_KEY}`,
  'Content-Type': 'application/json',
};

async function supabaseFetch(path: string) {
  if (!SUPABASE_URL || !SUPABASE_ANON_KEY) return null;
  try {
    const res = await fetch(`${SUPABASE_URL}/rest/v1/${path}`, {
      headers: supabaseHeaders,
      cache: 'no-store',
    });
    if (!res.ok) return null;
    return await res.json();
  } catch {
    return null;
  }
}

// ─── Types ───

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

export interface MacroSnapshot {
  id: number;
  date: string;
  sofr: number | null;
  tga_billion: number | null;
  vix: number | null;
  usdjpy: number | null;
  us10y: number | null;
  net_liq_billion: number | null;
  net_liq_weekly_change_pct: number | null;
  macro_score: number;
  macro_stance: string;
  crypto_action: string;
  triggers: MacroSignal['triggers'];
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

export interface Article {
  id: number;
  title: string;
  content: string;
  source: string;
  url: string;
  published_date: string;
  created_at: string;
}

// ─── Data Fetchers ───

export async function fetchMacroSignal(): Promise<MacroSignal | null> {
  // Get latest macro snapshot
  const data = await supabaseFetch('macro_snapshots?order=date.desc&limit=1');
  if (!data || data.length === 0) return null;
  const row = data[0];
  return {
    date: row.date,
    sofr: row.sofr,
    tga_billion: row.tga_billion,
    vix: row.vix,
    usdjpy: row.usdjpy,
    us10y: row.us10y,
    net_liq_billion: row.net_liq_billion,
    net_liq_weekly_change_pct: row.net_liq_weekly_change_pct,
    macro_score: row.macro_score ?? 0,
    macro_stance: row.macro_stance ?? 'NEUTRAL',
    crypto_action: row.crypto_action ?? '',
    triggers: row.triggers ?? [],
    source: 'supabase',
  };
}

export async function fetchMacroHistory(days: number = 7): Promise<MacroSnapshot[]> {
  const data = await supabaseFetch(`macro_snapshots?order=date.desc&limit=${days}`);
  return data ?? [];
}

export async function fetchLiquidity(): Promise<LiquidityData[]> {
  const data = await supabaseFetch('market_liquidity?order=date.desc&limit=90');
  return data ?? [];
}

export async function fetchEconomics(symbol?: string): Promise<EconomicIndicator[]> {
  const filter = symbol ? `&symbol=eq.${symbol}` : '';
  const data = await supabaseFetch(`economic_indicators?order=date.desc&limit=500${filter}`);
  return data ?? [];
}

export async function fetchHistoryDates(): Promise<string[]> {
  const data = await supabaseFetch('news_summaries?select=date&order=date.desc&limit=30');
  if (!data) return [];
  return data.map((r: { date: string }) => r.date);
}

export async function fetchSummary(date?: string): Promise<string | null> {
  const today = new Date().toLocaleDateString('sv-SE', { timeZone: 'Asia/Taipei' });
  const targetDate = date || today;
  const data = await supabaseFetch(
    `news_summaries?date=eq.${targetDate}&select=content&order=version.desc&limit=1`
  );
  if (!data || data.length === 0) return null;
  return data[0].content;
}

export async function fetchArticles(date: string): Promise<Article[]> {
  const data = await supabaseFetch(
    `articles?published_date=eq.${date}&select=id,title,content,source,url,published_date,created_at&order=created_at.desc`
  );
  return data ?? [];
}

// SSE streaming is no longer needed (cron generates summaries)
// Keep a stub for backward compatibility
export function streamSummary(
  onMessage: (data: { markdown?: string; status?: string; step?: number; error?: string }) => void,
  onError: (err: string) => void,
  onDone: () => void
): () => void {
  // No-op: just fetch the latest summary
  fetchSummary().then((md) => {
    if (md) {
      onMessage({ markdown: md });
    } else {
      onMessage({ error: 'No summary available. Wait for the next cron run.' });
    }
    onDone();
  }).catch((e) => {
    onError(String(e));
    onDone();
  });
  return () => {};
}

export type SummaryResponse = {
  markdown?: string;
  source?: string;
  date?: string;
  status?: string;
  step?: number;
  error?: string;
};

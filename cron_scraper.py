#!/usr/bin/env python3
"""
Standalone cron script for dailynews.
Runs scrapers → LLM summary → saves to Supabase.
No backend server needed.

Usage:
  python3 cron_scraper.py           # Full run (scrape + summarize)
  python3 cron_scraper.py --macro   # Only update macro signal
  python3 cron_scraper.py --summary # Only regenerate summary from existing articles
"""

import asyncio
import os
import sys
import json
import argparse
from datetime import datetime, timezone, timedelta
from dotenv import load_dotenv

# Load env
load_dotenv(os.path.join(os.path.dirname(__file__), '.env'))

# Import existing modules
sys.path.insert(0, os.path.dirname(__file__))
from scrapers import run_all_scrapers
from api.db import SupabaseClient
from api.fred_utils import FredClient
from api.llm_utils import generate_daily_summary
from api.macro_utils import build_macro_snapshot, compute_macro_signal, get_yahoo_price_history

TZ_TW = timezone(timedelta(hours=8))


async def update_macro(db: SupabaseClient):
    """Fetch fresh macro data and save snapshot."""
    print("[MACRO] Fetching macro signals...")

    # Get historical liquidity for weekly change
    liq_history = await db.get_market_liquidity()
    walcl_billion = None
    rrp_billion = None
    net_liq_prev_week = None

    if liq_history:
        latest = liq_history[0]
        walcl_billion = float(latest.get("walcl")) if latest.get("walcl") else None
        rrp_billion = float(latest.get("rrp")) if latest.get("rrp") else None
        if len(liq_history) >= 7:
            prev = liq_history[6]
            net_liq_prev_week = float(prev.get("net_liquidity")) if prev.get("net_liquidity") else None

    snapshot = build_macro_snapshot(walcl_billion=walcl_billion, rrp_billion=rrp_billion)

    if net_liq_prev_week and snapshot.get("net_liq_billion"):
        change_pct = (snapshot["net_liq_billion"] - net_liq_prev_week) / abs(net_liq_prev_week) * 100
        snapshot["net_liq_weekly_change_pct"] = round(change_pct, 2)

        usdjpy_history = get_yahoo_price_history("USDJPY=X", days=10)
        usdjpy_prev_week = usdjpy_history[-8] if len(usdjpy_history) >= 8 else None

        signal = compute_macro_signal(
            net_liq=snapshot["net_liq_billion"],
            net_liq_prev_week=net_liq_prev_week,
            sofr=snapshot.get("sofr"),
            vix=snapshot.get("vix"),
            usdjpy=snapshot.get("usdjpy"),
            usdjpy_prev_week=usdjpy_prev_week,
        )
        snapshot.update({
            "macro_score": signal["score"],
            "macro_stance": signal["stance"],
            "crypto_action": signal["crypto_action"],
            "triggers": signal["triggers"],
        })

    await db.save_macro_snapshot(snapshot)
    print(f"[MACRO] Saved: {snapshot.get('macro_stance')} score={snapshot.get('macro_score')}")
    return snapshot


async def scrape_and_summarize(db: SupabaseClient, sources: list = None):
    """Run scrapers, fetch articles, generate AI summary."""
    today = datetime.now(TZ_TW).strftime("%Y-%m-%d")
    api_key = os.getenv("GEMINI_API_KEY")

    if not api_key:
        print("[ERROR] GEMINI_API_KEY not set")
        return None

    all_sources = [
        'anduril', 'blocktempo', 'cnyes', 'cnbc', 'seekingalpha',
        'bbc', 'cnn', 'techcrunch', 'forbes', 'businessinsider', 'axios', 'nyt', 'reuters'
    ]
    source_list = sources or all_sources

    # Step 1: Scrape
    print(f"[SCRAPE] Running {len(source_list)} scrapers...")
    try:
        await asyncio.wait_for(run_all_scrapers(db, source_list), timeout=45.0)
        print("[SCRAPE] Done")
    except asyncio.TimeoutError:
        print("[SCRAPE] Timeout (45s), continuing with what we have")
    except Exception as e:
        print(f"[SCRAPE] Error: {e}")

    # Step 2: Fetch articles
    print("[FETCH] Getting today's articles from DB...")
    import aiohttp
    url = f"{db.base_url}/rest/v1/articles"
    params = {"published_date": f"eq.{today}", "select": "title,content,source,url"}
    articles = []
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=db.headers, params=params) as resp:
                if resp.status == 200:
                    articles = await resp.json()
    except Exception as e:
        print(f"[FETCH] Error: {e}")

    if not articles:
        print("[FETCH] No articles found for today")
        return None

    print(f"[FETCH] Got {len(articles)} articles")

    # Step 3: Get economic context
    eco_data = await db.get_economic_indicators(limit=500)
    eco_context = ""
    if eco_data:
        from collections import defaultdict
        grouped = defaultdict(list)
        for item in eco_data:
            grouped[item['symbol']].append(item)
        eco_context = "\n### 最新經濟數據參考:\n"
        for sym, items in grouped.items():
            items.sort(key=lambda x: x['date'], reverse=True)
            if items:
                eco_context += f"- {sym}: {items[0]['value']} [Date: {items[0]['date']}]\n"

    # Step 4: Generate AI summary
    print("[AI] Generating summary with Gemini Flash...")
    full_text = "\n".join([
        f"### {a['title']}\n{a['content']}\n出處: {a['source']}\nLink: {a['url']}"
        for a in articles
    ])
    if eco_context:
        full_text += f"\n\n---{eco_context}---"

    summary, prompt_used = await generate_daily_summary(full_text, api_key)

    if summary and not summary.startswith("Error") and not summary.startswith("Exception"):
        await db.save_summary(today, summary, prompt_used)
        print(f"[AI] Summary saved ({len(summary)} chars)")
        return summary
    else:
        print(f"[AI] Generation failed: {summary[:100] if summary else 'None'}")
        return None


async def update_fred(db: SupabaseClient):
    """Fetch FRED economic data (WALCL, RRP, M1, M2, VIX, 10Y2Y, DXY) and save to DB."""
    fred = FredClient(db)
    if not fred.api_key:
        print("[FRED] ⚠️ FRED_API_KEY not set, skipping")
        return

    print("[FRED] Updating market liquidity (WALCL/TGA/RRP)...")
    try:
        liq_result = await fred.update_market_liquidity()
        print(f"[FRED] Liquidity: {liq_result}")
    except Exception as e:
        print(f"[FRED] Liquidity error: {e}")

    print("[FRED] Updating economic indicators (VIX/M1/M2/10Y2Y/DXY)...")
    try:
        eco_result = await fred.update_economic_indicators()
        print(f"[FRED] Indicators: {eco_result}")
    except Exception as e:
        print(f"[FRED] Indicators error: {e}")


async def main():
    parser = argparse.ArgumentParser(description='DailyNews Cron Scraper')
    parser.add_argument('--macro', action='store_true', help='Only update macro signal')
    parser.add_argument('--summary', action='store_true', help='Only regenerate summary')
    parser.add_argument('--fred', action='store_true', help='Only update FRED data')
    args = parser.parse_args()

    db = SupabaseClient()
    if not db.is_configured:
        print("[ERROR] Supabase not configured")
        sys.exit(1)

    if args.macro:
        await update_macro(db)
    elif args.summary:
        await scrape_and_summarize(db)
    elif args.fred:
        await update_fred(db)
    else:
        # Full run: FRED + macro + scrape + summarize
        await update_fred(db)
        await update_macro(db)
        await scrape_and_summarize(db)

    print("[DONE] ✅")


if __name__ == "__main__":
    asyncio.run(main())

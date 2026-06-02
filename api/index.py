from fastapi import FastAPI, HTTPException, Request, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, HTMLResponse, StreamingResponse
import aiohttp
import os
import asyncio
import json
from datetime import datetime, timezone, timedelta
from typing import Optional
from dotenv import load_dotenv
from api.llm_utils import generate_daily_summary
from scrapers import run_all_scrapers
from api.templates import HTML_CONTENT
from api.db import SupabaseClient
from api.fred_utils import FredClient
from api.macro_utils import build_macro_snapshot

# Load environment variables
load_dotenv()

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

db = SupabaseClient()
TZ_TW = timezone(timedelta(hours=8))

# Debug Logging
print("--- Server Startup ---")
print(f"Supabase Configured: {db.is_configured}")
if not db.is_configured:
    if not os.getenv("SUPABASE_URL"): print("Missing Env: SUPABASE_URL")
    if not os.getenv("SUPABASE_KEY"): print("Missing Env: SUPABASE_KEY")
print("----------------------")


@app.get("/api/history")
async def get_history_dates():
    dates = await db.get_available_dates()
    return {"dates": dates}

@app.get("/api/articles")
async def get_articles_endpoint(date: str):
    """
    Get raw list of articles for a specific date from DB.
    """
    articles = await db.get_articles_by_date(date)
    return {"articles": articles}

@app.get("/api/liquidity")
async def get_liquidity_data(refresh: bool = False):
    """
    Get market liquidity data (Net Liquidity, WALCL, TGA, RRP).
    If refresh=True, triggers FRED fetch and update.
    """
    fred = FredClient(db)

    if refresh:
        # Trigger update
        await fred.update_market_liquidity()

    # Return data from DB
    data = await db.get_market_liquidity()

    # If empty and not forcing refresh, maybe we should try fetching once?
    if not data and not refresh:
         await fred.update_market_liquidity()
         data = await db.get_market_liquidity()

    return {"data": data}

@app.get("/api/economics")
async def get_economic_data(symbol: Optional[str] = None, refresh: bool = False):
    """
    Get economic indicators (VIX, M2, M1, 10Y2Y, DXY_BROAD).
    """
    fred = FredClient(db)

    if refresh:
        await fred.update_economic_indicators()

    data = await db.get_economic_indicators(symbol)

    if not data and not refresh:
        # Try fetch if empty
        await fred.update_economic_indicators()
        data = await db.get_economic_indicators(symbol)

    return {"data": data}

@app.get("/api/summarize")
@app.get("/summarize")
async def summarize_news_endpoint(
    date: Optional[str] = None,
    sources: Optional[str] = Query(None, description="Comma separated sources"),
    refresh: bool = False
):
    """
    Get news summary.
    - date: YYYY-MM-DD. If provided, STRICT READ ONLY from Cache.
    - refresh: If True, forces live generation (scrapers + AI) and updates cache for TODAY.
    - sources: Optional filter for sources (only used during live generation).

    Returns:
        JSONResponse (for cached content) OR StreamingResponse (for live generation).
    """
    today_str = datetime.now(TZ_TW).strftime("%Y-%m-%d")
    target_date = date if date else today_str

    # Defaults
    all_sources = {
        'anduril', 'blocktempo', 'cnyes', 'cnbc', 'seekingalpha',
        'bbc', 'cnn', 'techcrunch', 'forbes', 'businessinsider', 'axios', 'nyt', 'reuters'
    }
    if sources:
        source_list = [s.strip().lower() for s in sources.split(',') if s.strip().lower() in all_sources]
    else:
        source_list = list(all_sources)
    if not source_list: source_list = list(all_sources)

    # 1. READ MODE (If date provided OR (Not refreshing and Cache exists))
    should_check_cache = True
    if not date and refresh:
        should_check_cache = False

    if should_check_cache:
        try:
            cached = await db.get_summary_by_date(target_date)
            if cached:
                return JSONResponse(content={"markdown": cached, "source": "cache", "date": target_date})

            # If date was explicitly provided and no cache found -> 404
            if date:
                return JSONResponse(status_code=404, content={"markdown": f"⚠️ 找不到 {target_date} 的歷史摘要。", "date": target_date})
        except Exception as e:
            print(f"DB Error: {e}")
            if date: raise HTTPException(status_code=500, detail="DB Error")

    # 2. GENERATE MODE (Live) - Only allowed for TODAY (date=None)
    if date and date != today_str:
        return JSONResponse(status_code=404, content={"markdown": f"⚠️ 無法重新生成歷史日期 ({target_date}) 的摘要。", "date": target_date})

    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key: raise HTTPException(status_code=500, detail="GEMINI_API_KEY missing")

    async def summary_generator():
        try:
            # Step 1: Scrapers
            yield f"data: {json.dumps({'status': '正在連線至各國新聞來源...', 'step': 1})}\n\n"
            await asyncio.sleep(0.1)

            # Run Scrapers (30s timeout)
            try:
                await asyncio.wait_for(run_all_scrapers(db, source_list), timeout=30.0)
            except asyncio.TimeoutError:
                await db.log_error("api:timeout", "Timeout during scraping")
                # Continue anyway to see if we have DB data

            # Step 2: DB Fetch
            yield f"data: {json.dumps({'status': '正在從資料庫彙整今日文章...', 'step': 2})}\n\n"
            await asyncio.sleep(0.1)

            # Fetch latest economic indicators for AI Context (Fetch last ~90 days for trends)
            # Fetching 500 rows should cover all symbols for recent months
            eco_data = await db.get_economic_indicators(limit=500)

            eco_context = ""
            if eco_data:
                from collections import defaultdict
                grouped = defaultdict(list)
                for item in eco_data:
                    grouped[item['symbol']].append(item)

                eco_context = "\n### 最新經濟數據參考 (AI Context - Current vs 1M ago):\n"
                for sym, items in grouped.items():
                    # Sort desc just in case
                    items.sort(key=lambda x: x['date'], reverse=True)
                    if not items: continue

                    latest = items[0]
                    latest_val = latest['value']
                    latest_date = latest['date']

                    # Find ~30 days ago
                    prev_val = "N/A"
                    try:
                        curr_dt = datetime.strptime(latest_date, "%Y-%m-%d")
                        target_dt = curr_dt - timedelta(days=30)

                        # Find closest item >= 30 days ago
                        # Since items are desc, we look for item where date <= target_dt
                        for p in items:
                            p_dt = datetime.strptime(p['date'], "%Y-%m-%d")
                            if p_dt <= target_dt:
                                prev_val = p['value']
                                break
                    except: pass

                    trend_str = ""
                    if prev_val != "N/A" and isinstance(latest_val, (int, float)) and isinstance(prev_val, (int, float)):
                        try:
                            diff = ((latest_val - prev_val) / prev_val) * 100
                            sign = "+" if diff > 0 else ""
                            trend_str = f" (MoM: {sign}{diff:.1f}%)"
                        except: pass

                    eco_context += f"- {sym}: {latest_val}{trend_str} [Date: {latest_date}]\n"

            # Helper to fetch content
            async def fetch_todays_full_articles():
                url = f"{db.base_url}/rest/v1/articles"
                params = {
                    "published_date": f"eq.{today_str}",
                    "select": "title,content,source,url"
                }
                try:
                    async with aiohttp.ClientSession() as session:
                        async with session.get(url, headers=db.headers, params=params) as resp:
                            if resp.status == 200:
                                return await resp.json()
                except: pass
                return []

            todays_articles = await fetch_todays_full_articles()

            if not todays_articles:
                 # Try fallback to cache
                 cached = await db.get_summary_by_date(today_str)
                 if cached:
                     yield f"data: {json.dumps({'markdown': cached + '\n\n(註：最新嘗試抓取未獲得新文章，顯示庫存摘要)', 'source': 'cache_fallback', 'date': today_str})}\n\n"
                     return

                 yield f"data: {json.dumps({'markdown': '⚠️ 今日尚未有符合條件的新聞 (且無歷史存檔)。', 'date': today_str})}\n\n"
                 return

            # Step 3: AI Generation
            yield f"data: {json.dumps({'status': 'AI 正在分析市場趨勢並撰寫報告 (請稍候)...', 'step': 3})}\n\n"
            await asyncio.sleep(0.1)

            # Filter out MarketWatch from database articles (double protection)
            filtered_articles = [a for a in todays_articles if 'marketwatch' not in a['source'].lower()]

            full_text = "\n".join([f"### {a['title']}\n{a['content']}\n出處: {a['source']}\nLink: {a['url']}" for a in filtered_articles])

            # Append Economic Context
            if eco_context:
                full_text += f"\n\n---{eco_context}---"

            summary, prompt_used = await generate_daily_summary(full_text, api_key)

            if summary and not summary.startswith("Error") and not summary.startswith("Exception"):
                 is_default_set = set(source_list) == all_sources
                 if is_default_set or refresh:
                      await db.save_summary(today_str, summary, prompt_used)

                 # Step 4: Final Result
                 yield f"data: {json.dumps({'markdown': summary, 'source': 'live_update', 'date': today_str})}\n\n"
            else:
                 await db.log_error("api:gemini", f"Gen Failed: {summary}")
                 yield f"data: {json.dumps({'error': 'AI 生成失敗', 'details': summary})}\n\n"

        except Exception as e:
            await db.log_error("api:error", str(e))
            yield f"data: {json.dumps({'error': '系統發生錯誤', 'details': str(e)})}\n\n"

    return StreamingResponse(summary_generator(), media_type="text/event-stream", headers={"X-Accel-Buffering": "no", "Cache-Control": "no-cache"})

@app.get("/api/macro-signal")
async def get_macro_signal(refresh: bool = False):
    """
    Get current macro signal for crypto contract trading (XinGPT Skill 4).
    Used by PolyArb market_monitor as Layer 1 macro filter.

    Query params:
        refresh: bool — if True, fetch fresh data from all sources

    Returns:
        {
          "date": "2026-02-24",
          "score": -30,
          "stance": "BEARISH",
          "crypto_action": "禁止多頭，可做空",
          "triggers": [...],
          "data": { sofr, tga_billion, vix, usdjpy, us10y, net_liq_billion, ... },
          "source": "cached" | "fresh"
        }
    """
    # Try cache first (unless forced refresh)
    if not refresh:
        cached = await db.get_latest_macro_snapshot()
        if cached:
            from datetime import date as _date
            today_str = _date.today().isoformat()
            if cached.get("date") == today_str:
                cached["source"] = "cached"
                return cached

    # Fetch latest WALCL and RRP from existing DB (market_liquidity table)
    liq_history = await db.get_market_liquidity()
    walcl_billion = None
    rrp_billion = None
    net_liq_prev_week = None

    if liq_history:
        # Latest entry (sorted desc)
        latest_liq = liq_history[0]
        # market_liquidity stores values — check existing field names
        # WALCL is typically in billions already in FRED; RRP same
        walcl_val = latest_liq.get("walcl")
        rrp_val = latest_liq.get("rrp")
        # FRED WALCL is in billions (fred_utils divides by 1000)
        walcl_billion = float(walcl_val) if walcl_val else None
        rrp_billion = float(rrp_val) if rrp_val else None

        # Weekly net_liq for change calculation (7 days ago)
        if len(liq_history) >= 7:
            week_ago = liq_history[6]
            prev_nl = week_ago.get("net_liquidity")
            net_liq_prev_week = float(prev_nl) if prev_nl else None

    # Build fresh snapshot (calls NY Fed, Fiscal Data, Yahoo Finance)
    snapshot = build_macro_snapshot(
        walcl_billion=walcl_billion,
        rrp_billion=rrp_billion,
    )

    # Inject historical weekly change if we have it
    if net_liq_prev_week is not None and snapshot.get("net_liq_billion") is not None:
        change_pct = (
            (snapshot["net_liq_billion"] - net_liq_prev_week) / abs(net_liq_prev_week) * 100
        )
        snapshot["net_liq_weekly_change_pct"] = round(change_pct, 2)

        # Re-compute signal with historical context
        from api.macro_utils import compute_macro_signal, get_yahoo_price_history
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

    # Save to DB
    await db.save_macro_snapshot(snapshot)

    snapshot["source"] = "fresh"
    return snapshot


@app.get("/api/macro-signal/refresh")
@app.post("/api/macro-signal/refresh")
async def refresh_macro_signal():
    """Force refresh macro signal (called by Vercel cron — must be GET)."""
    result = await get_macro_signal(refresh=True)
    return {"status": "ok", "stance": result.get("macro_stance"), "score": result.get("macro_score")}


@app.get("/")
@app.get("")
async def serve_root():
    return HTMLResponse(content=HTML_CONTENT)

@app.api_route("/{full_path:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def catch_all(request: Request, full_path: str):
    return {"detail": "Route not found", "path": full_path}

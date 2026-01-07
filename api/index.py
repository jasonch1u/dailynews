from fastapi import FastAPI, HTTPException, Request, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, HTMLResponse
import aiohttp
import os
import asyncio
from datetime import datetime, timezone, timedelta
from typing import List, Optional
from dotenv import load_dotenv
from api.llm_utils import translate_text, generate_daily_summary
from scrapers import run_all_scrapers
from api.templates import HTML_CONTENT
from api.db import SupabaseClient

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
    """
    today_str = datetime.now(TZ_TW).strftime("%Y-%m-%d")
    target_date = date if date else today_str

    # Defaults
    all_sources = {
        'anduril', 'blocktempo', 'cnyes', 'cnbc', 'seekingalpha', 'marketwatch',
        'bbc', 'cnn', 'techcrunch', 'forbes', 'businessinsider', 'axios', 'nyt', 'reuters'
    }
    if sources:
        source_list = [s.strip().lower() for s in sources.split(',') if s.strip().lower() in all_sources]
    else:
        source_list = list(all_sources)
    if not source_list: source_list = list(all_sources)

    # 1. READ MODE (If date provided OR (Not refreshing and Cache exists))
    # If date is specifically provided, we ONLY read from cache. We never scrape for historical dates.
    # If date is NOT provided (today), we check cache first. If refresh=True, we skip this.

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
            # If DB fails, we might fall through to live generation ONLY if it's today and not a specific date query
            if date: raise HTTPException(status_code=500, detail="DB Error")

    # 2. GENERATE MODE (Live) - Only allowed for TODAY (date=None)
    if date and date != today_str:
        return JSONResponse(status_code=404, content={"markdown": f"⚠️ 無法重新生成歷史日期 ({target_date}) 的摘要。", "date": target_date})

    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key: raise HTTPException(status_code=500, detail="GEMINI_API_KEY missing")

    try:
        # Run Scrapers
        # 30s timeout for scrapers
        # We don't use the return value 'articles' directly for summary anymore.
        # We assume scrapers populate the DB with today's articles.
        await asyncio.wait_for(run_all_scrapers(db, source_list), timeout=30.0)

        # Fetch ALL articles for today from DB to ensure AI uses everything available
        # (including those scraped in previous runs today or by other instances)
        # Note: get_articles_by_date returns a list of dicts, we need to format them for AI.
        # But get_articles_by_date in db.py currently selects only 'title,url,source,published_date'
        # We need CONTENT.
        # So we should probably add a new DB method or modify the scraper to return the full objects
        # OR just use what scrapers returned but filter strictly?
        # The user requested: "改用DB articles裡面，台灣時間當天的所有文章去給AI分析"
        # So we MUST fetch from DB.

        # We need a way to fetch full content for today's articles.
        # Let's add a helper or use a new query.
        # Since we can't easily modify DB client interface in this block without touching db.py again,
        # let's assume we can add a method to DB client or use raw SQL? No, we use REST.
        # We need to fetch 'content' column.

        # Let's define a local helper to fetch full articles for today
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
             # If scraping yielded nothing and DB is empty for today
             cached = await db.get_summary_by_date(today_str)
             if cached:
                 return JSONResponse(content={"markdown": cached + "\n\n(註：最新嘗試抓取未獲得新文章，顯示庫存摘要)", "source": "cache_fallback", "date": today_str})
             return JSONResponse(content={"markdown": "⚠️ 今日尚未有符合條件的新聞 (且無歷史存檔)。", "date": today_str})

        # Format for AI
        full_text = "\n".join([f"### {a['title']}\n{a['content']}\n出處: {a['source']}\nLink: {a['url']}" for a in todays_articles])

        # Generate Summary
        summary, prompt_used = await generate_daily_summary(full_text, api_key)

        # Check for errors in summary (it returns string starting with "Error" or "Exception" on fail)
        if summary and not summary.startswith("Error") and not summary.startswith("Exception"):
             # Save to Cache if it's the full default set OR if it's a manual refresh (user forced update)
             is_default_set = set(source_list) == all_sources

             # Note: We now save versions instead of overwriting.
             # We pass the prompt used for record keeping.
             if is_default_set or refresh:
                  await db.save_summary(today_str, summary, prompt_used)
        else:
             await db.log_error("api:gemini", f"Gen Failed: {summary}")

        return JSONResponse(content={"markdown": summary, "source": "live_update", "date": today_str})

    except asyncio.TimeoutError:
        await db.log_error("api:timeout", "Timeout during scraping")
        raise HTTPException(status_code=504, detail="Timeout")
    except Exception as e:
        await db.log_error("api:error", str(e))
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/")
@app.get("")
async def serve_root():
    return HTMLResponse(content=HTML_CONTENT)

@app.api_route("/{full_path:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def catch_all(request: Request, full_path: str):
    return {"detail": "Route not found", "path": full_path}

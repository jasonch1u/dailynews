from fastapi import FastAPI, HTTPException, Request, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, HTMLResponse, StreamingResponse
import aiohttp
import os
import asyncio
import json
from datetime import datetime, timezone, timedelta
from typing import List, Optional
from dotenv import load_dotenv
from api._llm_utils import translate_text, generate_daily_summary
from scrapers import run_all_scrapers
from api._templates import HTML_CONTENT
from api._db import SupabaseClient

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

    Returns:
        JSONResponse (for cached content) OR StreamingResponse (for live generation).
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

            # Run Scrapers (30s timeout)
            try:
                await asyncio.wait_for(run_all_scrapers(db, source_list), timeout=30.0)
            except asyncio.TimeoutError:
                await db.log_error("api:timeout", "Timeout during scraping")
                # Continue anyway to see if we have DB data

            # Step 2: DB Fetch
            yield f"data: {json.dumps({'status': '正在從資料庫彙整今日文章...', 'step': 2})}\n\n"

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

            full_text = "\n".join([f"### {a['title']}\n{a['content']}\n出處: {a['source']}\nLink: {a['url']}" for a in todays_articles])

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

    return StreamingResponse(summary_generator(), media_type="text/event-stream")

@app.get("/")
@app.get("")
async def serve_root():
    return HTMLResponse(content=HTML_CONTENT)

@app.api_route("/{full_path:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def catch_all(request: Request, full_path: str):
    return {"detail": "Route not found", "path": full_path}

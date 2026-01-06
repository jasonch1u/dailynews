from fastapi import FastAPI, HTTPException, Request, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, HTMLResponse
import aiohttp
import os
import asyncio
from datetime import datetime, timezone, timedelta
from typing import List, Optional
from dotenv import load_dotenv
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

async def generate_summary(text: str, api_key: str):
    if not api_key: raise ValueError("API Key is missing")
    model_name = "gemini-2.5-flash"
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={api_key}"

    prompt_text = f"""
    你是一個專業的新聞編輯。請根據以下抓取到的新聞標題和連結，
    整理出一份「每日新聞熱點摘要」。

    原始資料 (包含標題、連結與部分內文)：
    {text}

    要求：
    1. **重點摘要**：請將新聞分類（例如：加密貨幣、股市金融、科技趨勢），並對每個主題進行總結。
    2. **關鍵結論 (Key Takeaways)**：在每個分類或整份報告的開頭，列出 3 點最重要的市場洞察或趨勢結論。
    3. **格式要求**：每一則新聞摘要請嚴格遵守以下格式，確保資訊清晰：

       (新聞標題)
       (摘要內容，約 50-100 字，總結事件重點與影響)
       **情緒**: (正面/負面/中性)
       [來源網站] 新聞標題
       [閱讀全文](連結)

       **注意**：「[閱讀全文](連結)」必須單獨一行，且放在該則新聞的最後。

    4. 語氣專業且易讀，使用繁體中文。
    5. 輸出格式請使用 Markdown。
    """

    payload = {"contents": [{"parts": [{"text": prompt_text}]}]}
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload, headers={"Content-Type": "application/json"}) as response:
                if response.status != 200:
                    err = await response.text()
                    await db.log_error("api:gemini", f"Status {response.status}: {err}")
                    return f"AI API Error: {err}"
                data = await response.json()
                try:
                    return data["candidates"][0]["content"]["parts"][0]["text"]
                except:
                    return "Error parsing AI response."
    except Exception as e:
        await db.log_error("api:gemini", str(e))
        return f"AI Request Failed: {e}"

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
    sources: Optional[str] = Query(None, description="Comma separated sources: anduril,blocktempo,cnyes")
):
    """
    Get news summary.
    - date: YYYY-MM-DD. If provided, prefer Cache.
    - sources: If provided (usually with date=None), trigger Live Generation.
    """
    today_str = datetime.now(TZ_TW).strftime("%Y-%m-%d")
    target_date = date if date else today_str

    source_list = sources.split(',') if sources else ['anduril', 'blocktempo', 'cnyes']
    valid_sources = {'anduril', 'blocktempo', 'cnyes'}
    source_list = [s.strip().lower() for s in source_list if s.strip().lower() in valid_sources]
    if not source_list: source_list = ['anduril', 'blocktempo', 'cnyes']

    # 1. READ MODE: If date is explicitly provided, try to fetch from Cache FIRST.
    # This covers both "History" and "Auto-load Latest Date" scenarios.
    if date:
        try:
            cached = await db.get_summary_by_date(target_date)
            if cached:
                return JSONResponse(content={"markdown": cached, "source": "cache", "date": target_date})

            # If date is in the past and no cache -> 404
            if target_date != today_str:
                return JSONResponse(status_code=404, content={"markdown": f"⚠️ 找不到 {target_date} 的歷史摘要。", "date": target_date})

            # If date is Today but no cache -> Fall through to Generation (below)
        except:
            raise HTTPException(status_code=500, detail="DB Error")

    # 2. GENERATE MODE: If date is None (Live) OR date is Today but Cache Miss
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key: raise HTTPException(status_code=500, detail="GEMINI_API_KEY missing")

    try:
        # Run Scrapers
        articles = await asyncio.wait_for(run_all_scrapers(db, source_list), timeout=30.0)

        if not articles:
             # Try cache one last time just in case
             cached = await db.get_summary_by_date(target_date)
             if cached: return JSONResponse(content={"markdown": cached + "\n\n(註：目前尚未抓取到最新文章)", "source": "cache_fallback", "date": target_date})
             return JSONResponse(content={"markdown": "⚠️ 今日尚未有符合條件的新聞。", "date": target_date})

        full_text = "\n".join(articles)

        # Generate Summary
        summary = await generate_summary(full_text, api_key)

        # Save to Cache ONLY if it's the full default set
        is_default_set = set(source_list) == valid_sources
        if is_default_set and "AI API Error" not in summary:
             await db.save_summary(today_str, summary)

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

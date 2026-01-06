from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, HTMLResponse
import aiohttp
import os
import asyncio
from datetime import datetime, timezone, timedelta
from dotenv import load_dotenv
from scrapers import run_all_scrapers
from api.templates import HTML_CONTENT
from api.db import SupabaseClient

# Load environment variables
load_dotenv()

app = FastAPI()

# Enable CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for simplicity (or specify Vercel domain later)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Supabase Client
db = SupabaseClient()

# Taiwan Timezone for consistency
TZ_TW = timezone(timedelta(hours=8))

# Debug Logging on Startup
print("--- Server Startup ---")
print(f"Supabase Configured: {db.is_configured}")
if db.is_configured:
    print(f"Supabase URL: {db.supabase_url[:10]}... (Masked)")
else:
    print("WARNING: Supabase is NOT configured. Caching and History will be disabled.")
    # Log specifically which one is missing for Vercel logs
    if not os.getenv("SUPABASE_URL"): print("Missing Env: SUPABASE_URL")
    if not os.getenv("SUPABASE_KEY"): print("Missing Env: SUPABASE_KEY")
print("----------------------")

async def generate_summary(text: str, api_key: str):
    """Call Google Gemini API via REST to summarize the news"""
    if not api_key:
        raise ValueError("API Key is missing")

    # Use the REST API to avoid heavy dependencies like grpcio
    model_name = "gemini-2.5-flash"
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={api_key}"

    prompt_text = f"""
    你是一個專業的新聞編輯。請根據以下抓取到的新聞標題和連結，
    整理出一份「每日新聞熱點摘要」。

    原始資料 (包含標題、連結與部分內文)：
    {text}

    要求：
    1. 請將新聞分類（例如：加密貨幣、股市金融、科技趨勢）。
    2. 對每個主題進行重點摘要。請基於提供的內文進行總結，確保資訊準確，不要編造數據。
    3. **必須**在每一條新聞摘要下方附上原始連結，格式為：[閱讀全文](連結)。
    4. 語氣專業且易讀，使用繁體中文。
    5. 輸出格式請使用 Markdown，並在開頭加上一個整體的「今日重點速覽」區塊。
    6. 文末請列出「原始新聞列表」，每一行格式為：- [出處] [標題](連結)
    """

    payload = {
        "contents": [{
            "parts": [{"text": prompt_text}]
        }]
    }

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload, headers={"Content-Type": "application/json"}) as response:
                if response.status != 200:
                    error_text = await response.text()
                    await db.log_error("api:gemini", f"Status {response.status}: {error_text}")
                    return f"AI API Error ({response.status}): {error_text}"

                data = await response.json()

                try:
                    return data["candidates"][0]["content"]["parts"][0]["text"]
                except (KeyError, IndexError):
                    await db.log_error("api:gemini", "Unexpected format: " + str(data))
                    return "Error parsing AI response: Unexpected format."

    except Exception as e:
        await db.log_error("api:gemini", str(e))
        return f"AI Request Failed: {e}"

@app.get("/api/history")
async def get_history_dates():
    """Return a list of dates that have summaries available."""
    dates = await db.get_available_dates()
    return {"dates": dates}

@app.get("/api/summarize")
@app.get("/summarize")
async def summarize_news_endpoint(date: str = None):
    """
    Get news summary.
    If 'date' param is provided (YYYY-MM-DD), fetch that specific day from cache.
    If 'date' is NOT provided (or is today), try cache -> otherwise scrape & generate.
    """
    today_str = datetime.now(TZ_TW).strftime("%Y-%m-%d")
    target_date = date if date else today_str

    # 1. Check Cache (Supabase)
    try:
        cached_summary = await db.get_summary_by_date(target_date)
        if cached_summary:
            return JSONResponse(content={"markdown": cached_summary, "source": "cache", "date": target_date})

        # If user requested a PAST date and it's not in cache, we return 404 (don't scrape past)
        if target_date != today_str:
             return JSONResponse(status_code=404, content={"markdown": f"⚠️ 找不到 {target_date} 的歷史摘要。", "date": target_date})

    except Exception as e:
        print(f"Cache check failed: {e}")
        # Continue to generation ONLY if it's today
        if target_date != today_str:
            raise HTTPException(status_code=500, detail="Database Error during history fetch.")

    # 2. Check API Key (Only needed for generation)
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="Server Error: GEMINI_API_KEY is not set.")

    try:
        # 3. Run Scrapers concurrently
        # Pass db.log_error as the logger
        articles = await asyncio.wait_for(run_all_scrapers(db.log_error), timeout=25.0)

        if not articles:
            await db.log_error("scraper:all", "No articles found")
            return JSONResponse(content={"markdown": "⚠️ 沒有抓取到任何有效的新聞資料。請稍後再試。", "date": today_str})

        full_text = "\n".join(articles)

        # 4. AI Summary
        summary = await generate_summary(full_text, api_key)

        # 5. Save to Cache
        if "AI API Error" not in summary and "AI Request Failed" not in summary:
             await db.save_summary(today_str, summary)

        return JSONResponse(content={"markdown": summary, "source": "live", "date": today_str})

    except asyncio.TimeoutError:
        await db.log_error("scraper:main", "Timeout")
        raise HTTPException(status_code=504, detail="Scraping timed out.")
    except Exception as e:
        await db.log_error("scraper:main", str(e))
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/")
@app.get("")
async def serve_root():
    """Serve the embedded index.html directly"""
    return HTMLResponse(content=HTML_CONTENT)

@app.api_route("/{full_path:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def catch_all(request: Request, full_path: str):
    return {
        "detail": "Debug: Route not found (Caught by catch-all)",
        "received_path": full_path,
        "base_url": str(request.base_url),
        "headers": dict(request.headers),
    }

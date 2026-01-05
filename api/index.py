from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import google.generativeai as genai
import os
import asyncio
from dotenv import load_dotenv
from scrapers import run_all_scrapers

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

async def generate_summary(text: str, api_key: str):
    """Call Google Gemini API to summarize the news"""
    if not api_key:
        raise ValueError("API Key is missing")

    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-2.5-flash')

    prompt = f"""
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

    # Run synchronous generation in a separate thread to avoid blocking the event loop
    try:
        response = await asyncio.to_thread(model.generate_content, prompt)
        return response.text
    except Exception as e:
        return f"AI 摘要生成失敗: {e}"

@app.get("/api/summarize")
async def summarize_news_endpoint():
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="Server Error: GEMINI_API_KEY is not set.")

    try:
        # 1. Run Scrapers concurrently
        # We set a timeout for the scraping part to ensure it doesn't hang forever
        # Vercel limit is strict, so we try to be fast.
        articles = await asyncio.wait_for(run_all_scrapers(), timeout=15.0)

        if not articles:
            return JSONResponse(content={"markdown": "⚠️ 沒有抓取到任何有效的新聞資料。請稍後再試。"})

        full_text = "\n".join(articles)

        # 2. AI Summary
        summary = await generate_summary(full_text, api_key)

        return JSONResponse(content={"markdown": summary})

    except asyncio.TimeoutError:
        raise HTTPException(status_code=504, detail="Scraping timed out.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Vercel entry point
# Vercel looks for `app` in the module.

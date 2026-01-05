from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import aiohttp
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
    """Call Google Gemini API via REST to summarize the news"""
    if not api_key:
        raise ValueError("API Key is missing")

    # Use the REST API to avoid heavy dependencies like grpcio
    # Assuming user wants gemini-2.5-flash as per their original code,
    # but strictly speaking, common models are gemini-1.5-flash or gemini-2.0-flash-exp.
    # We will use the model string from their original code: gemini-2.5-flash
    # If this model does not exist, it will 404.
    # To be safe, let's try to use a very standard recent model if 2.5 is not real,
    # but the user had it in their code, so we trust it or they might have an alias/preview.
    # However, to avoid breakage if 2.5 is a typo, we might want to fallback or use a known one?
    # No, stick to user's intent.

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
                    return f"AI API Error ({response.status}): {error_text}"

                data = await response.json()

                # Extract text from response
                # Response structure: candidates[0].content.parts[0].text
                try:
                    return data["candidates"][0]["content"]["parts"][0]["text"]
                except (KeyError, IndexError):
                    return "Error parsing AI response: Unexpected format."

    except Exception as e:
        return f"AI Request Failed: {e}"

@app.get("/api/summarize")
@app.get("/summarize")
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

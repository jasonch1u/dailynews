from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, HTMLResponse
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

# Embedded Frontend HTML to ensure serverless compatibility (avoids file path issues)
HTML_CONTENT = r"""<!DOCTYPE html>
<html lang="zh-TW">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>每日新聞 AI 摘要</title>
    <link rel="icon" href="data:image/svg+xml,<svg xmlns=%22http://www.w3.org/2000/svg%22 viewBox=%220 0 100 100%22><text y=%22.9em%22 font-size=%2290%22>📰</text></svg>">
    <!-- Use marked.js for Markdown rendering -->
    <script src="https://cdn.jsdelivr.net/npm/marked/marked.min.js"></script>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f8f9fa;
            color: #333;
        }
        header {
            text-align: center;
            margin-bottom: 40px;
        }
        h1 {
            color: #2c3e50;
        }
        .controls {
            text-align: center;
            margin-bottom: 20px;
        }
        button {
            background-color: #0d6efd;
            color: white;
            border: none;
            padding: 12px 24px;
            font-size: 16px;
            border-radius: 4px;
            cursor: pointer;
            transition: background-color 0.2s;
        }
        button:hover {
            background-color: #0b5ed7;
        }
        button:disabled {
            background-color: #6c757d;
            cursor: not-allowed;
        }
        #status {
            text-align: center;
            margin: 10px 0;
            font-weight: bold;
            color: #666;
            min-height: 24px;
        }
        #content {
            background: white;
            padding: 30px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            line-height: 1.6;
        }
        #content a {
            color: #0d6efd;
            text-decoration: none;
        }
        #content a:hover {
            text-decoration: underline;
        }
        .download-btn {
            display: none; /* Hidden by default */
            margin-top: 20px;
            background-color: #198754;
        }
        .download-btn:hover {
            background-color: #157347;
        }
        .loader {
            border: 4px solid #f3f3f3;
            border-top: 4px solid #0d6efd;
            border-radius: 50%;
            width: 20px;
            height: 20px;
            animation: spin 1s linear infinite;
            display: inline-block;
            vertical-align: middle;
            margin-right: 10px;
        }
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
    </style>
</head>
<body>
    <header>
        <h1>📰 每日新聞 AI 摘要服務</h1>
        <p>自動抓取 Anduril, BlockTempo, 鉅亨網 的最新新聞並生成重點摘要。</p>
    </header>

    <div class="controls">
        <button id="generateBtn" onclick="generateSummary()">🚀 開始抓取並生成摘要</button>
        <div id="status"></div>
    </div>

    <div id="content">
        <p style="text-align: center; color: #888;">點擊上方按鈕開始生成...</p>
    </div>

    <div style="text-align: center;">
        <button id="downloadBtn" class="download-btn" onclick="downloadMarkdown()">📥 下載 Markdown 報告</button>
    </div>

    <script>
        let currentMarkdown = "";

        async function generateSummary() {
            const btn = document.getElementById('generateBtn');
            const status = document.getElementById('status');
            const content = document.getElementById('content');
            const downloadBtn = document.getElementById('downloadBtn');

            btn.disabled = true;
            downloadBtn.style.display = 'none';
            status.innerHTML = '<span class="loader"></span> 正在抓取新聞並進行 AI 摘要，這可能需要幾秒鐘...';
            content.innerHTML = '';

            try {
                // Determine API URL based on environment (Vercel or local)
                // In Vercel, relative path /api/summarize works if served from same domain
                const response = await fetch('/api/summarize');

                if (!response.ok) {
                    throw new Error(`HTTP error! status: ${response.status}`);
                }

                const data = await response.json();

                if (data.markdown) {
                    currentMarkdown = data.markdown;
                    content.innerHTML = marked.parse(data.markdown);
                    status.innerHTML = '✅ 處理完成！';
                    status.style.color = 'green';
                    downloadBtn.style.display = 'inline-block';
                } else {
                    status.innerHTML = '❌ 未能生成摘要。';
                    status.style.color = 'red';
                }

            } catch (error) {
                console.error('Error:', error);
                status.innerHTML = `❌ 發生錯誤: ${error.message}`;
                status.style.color = 'red';
                content.innerHTML = `<p style="color: red;">請求失敗，請稍後再試。<br>錯誤訊息: ${error.message}</p>`;
            } finally {
                btn.disabled = false;
            }
        }

        function downloadMarkdown() {
            if (!currentMarkdown) return;

            const date = new Date().toISOString().split('T')[0];
            const filename = `Daily_News_${date}.md`;

            const blob = new Blob([currentMarkdown], { type: 'text/markdown' });
            const url = URL.createObjectURL(blob);

            const a = document.createElement('a');
            a.href = url;
            a.download = filename;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            URL.revokeObjectURL(url);
        }
    </script>
</body>
</html>"""

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

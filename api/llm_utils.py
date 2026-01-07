import aiohttp
import os
import json

async def call_gemini(prompt: str, api_key: str):
    """Generic function to call Gemini API"""
    if not api_key: return None

    model_name = "gemini-2.5-flash"
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={api_key}"

    payload = {"contents": [{"parts": [{"text": prompt}]}]}

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload, headers={"Content-Type": "application/json"}) as response:
                if response.status != 200:
                    # Return error string so caller can log it
                    err_text = await response.text()
                    return f"Error {response.status}: {err_text}"
                data = await response.json()
                try:
                    return data["candidates"][0]["content"]["parts"][0]["text"]
                except KeyError:
                     return "Error: Unexpected API response format."
    except Exception as e:
        return f"Exception: {str(e)}"

async def generate_daily_summary(articles_text: str, api_key: str):
    """
    Generates the daily news summary using Gemini.
    """
    prompt_text = f"""
    你是一個專業的財經新聞編輯。請根據以下抓取到的新聞標題和連結，整理出一份「每日新聞熱點摘要」。

    原始資料 (包含標題、連結與部分內文)：
    {articles_text}

    **核心任務：主題式整合 (Topic-Based Aggregation)**
    請分析所有文章，找出報導「同一具體事件」的新聞，並依照以下邏輯撰寫摘要：

    1.  **事件分組**：將報導相同事件的文章歸類在一起。
    2.  **單一來源處理**：如果某事件只有一篇報導，請維持單一格式。
    3.  **多重來源處理**：如果某事件有多篇報導，請整合成一個主題摘要，並列出所有參考來源。
    4.  **數量限制**：最多呈現 10 個新聞主題。若今日事件超過 10 個，請優先保留「對金融市場影響較大」的重大新聞。

    **格式要求 (請嚴格遵守 Markdown)**：

    ---

    ### 1. [分類] 事件標題 (請自擬一個概括性標題)

    (這裡寫一段約 80-150 字的綜合摘要，融合各家觀點、關鍵數據與市場影響。請使用繁體中文，語氣專業。)

    **情緒**: (正面/負面/中性)

    **相關報導**:
    - [來源網站] [新聞標題](連結)
    - [來源網站] [新聞標題](連結)

    ---

    **格式範例 (多來源)**：
    ### 1. [科技] Nvidia 財報超預期，帶動 AI 板塊齊漲
    輝達 (Nvidia) 公布最新季度財報，營收與獲利雙雙優於華爾街預期... (摘要內容)...
    **情緒**: 正面
    **相關報導**:
    - [CNBC] [Nvidia shares soar on earnings beat](https://...)
    - [鉅亨網] [輝達財報驚豔 目標價調升](https://...)

    **格式範例 (單一來源)**：
    ### 2. [加密貨幣] 比特幣突破 7 萬美元大關
    受 ETF 資金流入影響，比特幣今日強勢上漲... (摘要內容)...
    **情緒**: 正面
    **相關報導**:
    - [動區] [比特幣衝破 70K](https://...)

    **關鍵結論 (Key Takeaways)**：
    在整份報告的最開頭，請列出 3 點最重要的市場洞察或趨勢結論。

    **注意**：
    - [來源網站] 請直接使用原始資料提供的來源名稱 (如: FOX, Cnyes, BBC, CNBC 等)。
    - 請確保所有連結都能正確對應。
    """

    summary = await call_gemini(prompt_text, api_key)
    return summary, prompt_text

async def translate_text(text_list: list, api_key: str) -> list:
    """
    Translate a list of strings to Traditional Chinese.
    Returns a list of same length.
    """
    if not text_list: return []

    # Simple batching
    prompt = "請將以下每一行英文標題翻譯成繁體中文，保持原意，不要加額外的編號或解釋，每一行對應一行翻譯：\n\n"
    prompt += "\n".join(text_list)

    result = await call_gemini(prompt, api_key)

    if result:
        # Split by newline and clean
        translated = [line.strip() for line in result.strip().split('\n') if line.strip()]
        # Safety check: if length mismatch, return original (or partial)
        if len(translated) == len(text_list):
            return translated
        else:
            print(f"Translation count mismatch: Input {len(text_list)} vs Output {len(translated)}")
            # Fallback: return original if simple mismatch, or try to align?
            # Safer to return original to avoid wrong mapping
            return text_list

    return text_list

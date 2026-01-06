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
    你是一個專業的新聞編輯。請根據以下抓取到的新聞標題和連結，
    整理出一份「每日新聞熱點摘要」。

    原始資料 (包含標題、連結與部分內文)：
    {articles_text}

    要求：
    1. **重點摘要**：請將新聞分類（例如：加密貨幣、股市金融、科技趨勢），並對每個主題進行總結。
    2. **關鍵結論 (Key Takeaways)**：在每個分類或整份報告的開頭，列出 3 點最重要的市場洞察或趨勢結論。
    3. **格式要求**：每一則新聞摘要請嚴格遵守以下格式，確保資訊清晰。
       **非常重要：區塊順序與斷行必須完全一致**。

       格式範例：

       ### [來源網站] 新聞標題

       (摘要內容，約 50-100 字，總結事件重點與影響)

       **情緒**: (正面/負面/中性)

       [閱讀全文](連結)

       **注意**：
       - 請將來源網站 (例如: [鉅亨網]) 放在標題的最前面。
       - 每個區塊間請務必保留空行 (Double Line Break)。
       - 「[閱讀全文](連結)」必須單獨一行，且放在該則新聞的最後。

    4. 語氣專業且易讀，使用繁體中文。
    5. 輸出格式請使用 Markdown。
    """

    return await call_gemini(prompt_text, api_key)

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

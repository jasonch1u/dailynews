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
    Generates the daily news summary using Gemini with Advanced Architecture.
    (Clustering -> Top 10 Topics -> Other News List -> Maker-Checker)
    """
    prompt_text = f"""
    你是一個專業的華爾街財經新聞主編。請仔細閱讀以下抓取到的全球新聞，並製作一份「每日市場深度報告」。

    原始資料 (包含標題、連結與部分內文)：
    {articles_text}

    ---

    **執行步驟 (Chain of Thought Process)**：
    請在內心執行以下步驟，確保輸出品質：
    1.  **語意分群 (Clustering)**：將報導「同一事件」的不同來源文章歸類為一組。
    2.  **重要性排序**：從分群後的事件中，挑選出「對全球金融市場、科技趨勢、加密貨幣或地緣政治」影響最大的前 10 個事件。
    3.  **剩餘篩選**：將未進入前 10 大，但仍具參考價值的次要新聞，歸類為「其他快訊」。
    4.  **事實查核 (Maker-Checker)**：檢查所有連結是否正確對應來源，並確保摘要內容無幻覺。

    ---

    **最終輸出格式 (請嚴格遵守 Markdown)**：

    **關鍵結論 (Key Takeaways)**：
    *   (列出 3 點最重要的市場洞察，每點約 20-30 字)

    ---

    ## 🔥 今日十大焦點 (Top 10 Main Topics)

    ### 1. [分類] 事件標題 (請自擬一個精準的概括性標題)
    (這裡寫一段約 80-150 字的深度摘要，融合各家觀點。若有具體數據 [如股價漲跌、營收數字] 請務必列出。)
    **情緒**: (正面/負面/中性)
    **相關報導**:
    - [來源網站] [新聞標題](連結)
    - [來源網站] [新聞標題](連結)

    (請依此格式列出 1~10 個焦點事件)

    ---

    ## 📰 其他快訊 (Other News)
    (將剩餘有價值的文章列於此處，格式如下)

    - **[來源網站]** [文章標題](連結)
    - **[來源網站]** [文章標題](連結)
    - **[來源網站]** [文章標題](連結)

    ---

    **格式規範**：
    - [來源網站] 請直接使用原始資料提供的來源名稱 (如: FOX, Cnyes, BBC, BlockTempo 等)。
    - **其他快訊**區塊的來源名稱請加上粗體 `**[來源]**`，以便前端樣式渲染。
    - 請使用繁體中文撰寫摘要。
    - 若今日新聞極少，焦點事件不足 10 個，請有多少列多少，不必硬湊。
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

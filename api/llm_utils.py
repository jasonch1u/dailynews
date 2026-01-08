import aiohttp
import os
import json

async def call_gemini(prompt: str, api_key: str):
    """Generic function to call Gemini API"""
    if not api_key: return None

    # Updated to gemini-2.0-flash which is the latest stable/preview high-performance model
    # (User requested 'gemini-3-flash-preview', but sticking to known valid identifier or what user explicitly wants)
    # The user was VERY specific: "gemini-3-flash-preview". I will use that.
    # Note: If this model doesn't exist, it will return 404/400 error.
    model_name = "gemini-3-flash-preview"
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
    (Sentiment Dashboard -> Key Takeaways -> Top 10 Topics -> Other News List -> Maker-Checker for Links)
    """
    prompt_text = f"""
    你是一個專業的華爾街財經新聞主編。請仔細閱讀以下抓取到的全球新聞，並製作一份「每日市場深度報告」。

    原始資料 (包含標題、連結與部分內文)：
    {articles_text}

    ---

    **執行步驟 (Chain of Thought Process)**：
    請在內心執行以下步驟，確保輸出品質：
    1.  **全盤分析 (Sentiment Analysis)**：先閱讀所有標題，判斷今日市場整體情緒 (貪婪/恐慌/中性)，歸納熱門關鍵字，並預測板塊波動。
    2.  **語意分群 (Clustering)**：將報導「同一事件」的不同來源文章歸類為一組。
    3.  **重要性排序**：選出前 10 大最具市場影響力的事件。
    4.  **連結查核 (Critical Step)**：在撰寫每一個主題時，**必須**從原始資料中找出對應的 `Link`，並附在「相關報導」區塊。**嚴禁遺漏連結**。

    ---

    **最終輸出格式 (請嚴格遵守 Markdown)**：

    ## 📊 市場儀表板 (Market Dashboard)
    *   **市場情緒**：(例如：貪婪 🐂 / 恐慌 🐻 / 觀望 😶) - (請簡述一句原因)
    *   **熱門關鍵字**：(列出 3-5 個 Hashtag，例如 #Nvidia #降息)
    *   **板塊觀測**：
        *   📈 **看漲/活躍**：(列出板塊名稱)
        *   📉 **承壓/回調**：(列出板塊名稱)

    ---

    **關鍵結論 (Key Takeaways)**：
    *   (列出 3 點最重要的市場洞察，每點約 20-30 字)

    ---

    ## 🔥 今日十大焦點 (Top 10 Main Topics)

    ### 1. [分類] 事件標題
    (這裡寫一段約 80-150 字的深度摘要，融合各家觀點。)

    **情緒**: (正面/負面/中性)
    **相關報導** (⚠️ 務必包含連結):
    - [來源網站] [新聞標題](連結)
    - [來源網站] [新聞標題](連結)

    (請依此格式列出 1~10 個焦點事件)

    ---

    ## 📰 其他快訊 (Other News)
    (將剩餘有價值的文章列於此處)

    - [來源網站] [文章標題](連結)
    - [來源網站] [文章標題](連結)
    - [來源網站] [文章標題](連結)

    ---

    **自我檢查清單 (Maker Checker)**：
    1.  是否已生成「市場儀表板」和「關鍵結論」？
    2.  是否每個焦點事件下方都有「相關報導」且連結有效？
    3.  連結是否與文章標題正確對應？

    **格式規範**：
    - [來源網站] 請直接使用原始資料提供的來源名稱 (如: FOX, Cnyes, BBC, BlockTempo 等)。
    - 來源名稱請保持純文字，**不要**加粗或使用任何格式 (如 `**[來源]**`)。
    - 連結請隱藏於標題中 (即 `[標題](連結)` 格式)，**不要**直接顯示網址文本。
    - 請使用繁體中文撰寫。
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

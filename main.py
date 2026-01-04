import google.generativeai as genai
import datetime
import time
import os
import streamlit as st
from dotenv import load_dotenv
from scrapers import fetch_anduril_tw, fetch_blocktempo, fetch_cnyes_stock

# ================= 配置區域 =================
# 載入 .env 檔案中的環境變數
load_dotenv()

# 優先從環境變數讀取 Key，若無則使用預設值 (建議在 .env 中設定)
API_KEY = os.getenv("GEMINI_API_KEY")

# ================= AI 摘要功能 =================

def summarize_news(all_articles_text, api_key):
    """使用 Gemini AI 進行摘要"""
    if not api_key or "YOUR_GEMINI_API_KEY" in api_key:
        return "錯誤：請先設定 API Key。"

    print("\n正在呼叫 AI 進行摘要整理...")

    genai.configure(api_key=api_key)
    
    # 根據您的要求設定為 gemini-2.5-flash
    model = genai.GenerativeModel('gemini-2.5-flash')

    prompt = f"""
    你是一個專業的新聞編輯。請根據以下抓取到的新聞標題和連結，
    整理出一份「每日新聞熱點摘要」。

    原始資料 (包含標題、連結與部分內文)：
    {all_articles_text}

    要求：
    1. 請將新聞分類（例如：加密貨幣、股市金融、科技趨勢）。
    2. 對每個主題進行重點摘要。請基於提供的內文進行總結，確保資訊準確，不要編造數據。
    3. **必須**在每一條新聞摘要下方附上原始連結，格式為：[閱讀全文](連結)。
    4. 語氣專業且易讀，使用繁體中文。
    5. 輸出格式請使用 Markdown，並在開頭加上一個整體的「今日重點速覽」區塊。
    6. 文末請列出「原始新聞列表」，每一行格式為：- [出處] [標題](連結)
    """

    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"AI 摘要生成失敗: {e}"

# ================= 主程式 =================

def main():
    st.set_page_config(page_title="每日新聞 AI 摘要", page_icon="📰", layout="centered")
    st.title("📰 每日新聞 AI 摘要服務")
    st.write("點擊下方按鈕，自動抓取 **Anduril**, **BlockTempo**, **鉅亨網** 的最新新聞並生成重點摘要。")

    if st.button("🚀 開始抓取並生成摘要", type="primary"):
        all_data = []
        status_text = st.empty() # 建立一個空區塊用來顯示狀態
        progress_bar = st.progress(0)

        # 1. 執行爬蟲
        status_text.info("正在抓取 Anduril.tw ...")
        data_anduril = fetch_anduril_tw()
        if data_anduril:
            all_data.append("--- Anduril.tw ---")
            all_data.extend(data_anduril)
        progress_bar.progress(30)

        status_text.info("正在抓取 BlockTempo ...")
        data_blocktempo = fetch_blocktempo()
        if data_blocktempo:
            all_data.append("\n--- BlockTempo ---")
            all_data.extend(data_blocktempo)
        progress_bar.progress(60)

        status_text.info("正在抓取 鉅亨網 ...")
        data_cnyes = fetch_cnyes_stock()
        if data_cnyes:
            all_data.append("\n--- 鉅亨網 ---")
            all_data.extend(data_cnyes)
        progress_bar.progress(90)

        if not all_data:
            status_text.error("❌ 最終結果：沒有抓取到任何有效的新聞資料。請檢查終端機日誌確認是否被網站阻擋。")
            return

        # 2. AI 摘要
        status_text.info("🤖 正在呼叫 Gemini AI 進行摘要整理 (請稍候)...")
        full_text = "\n".join(all_data)
        
        # 直接將 Key 傳入函式，避免使用 global 造成 SyntaxError
        summary = summarize_news(full_text, API_KEY)
        progress_bar.progress(100)
        status_text.success("✅ 處理完成！")

        # 3. 顯示結果
        st.divider()
        st.markdown(summary)

        # 4. 提供下載按鈕
        today = datetime.date.today().strftime("%Y-%m-%d")
        st.download_button(
            label="📥 下載 Markdown 報告",
            data=summary,
            file_name=f"Daily_News_{today}.md",
            mime="text/markdown"
        )

if __name__ == "__main__":
    main()
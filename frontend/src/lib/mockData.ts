import type { MacroSignal } from './api';

export const MOCK_MACRO_SIGNAL: MacroSignal = {
  date: '2026-03-08',
  sofr: 4.31,
  tga_billion: 723.4,
  vix: 18.7,
  usdjpy: 148.32,
  us10y: 4.28,
  net_liq_billion: 5847.2,
  net_liq_weekly_change_pct: -1.3,
  macro_score: -15,
  macro_stance: 'CAUTIOUS',
  crypto_action: '謹慎，偏空操作',
  triggers: [
    { type: 'WARNING', indicator: 'net_liquidity', msg: '淨流動性週降 1.3%', action: '謹慎持倉' },
    { type: 'WARNING', indicator: 'sofr', msg: 'SOFR 4.31%（偏高）', action: '注意融資成本' },
  ],
  source: 'mock',
};

export const MOCK_SUMMARY = `## 📊 市場儀表板 (Market Dashboard)
*   **市場情緒**：觀望 😶 - 市場在關稅不確定性中觀望，VIX 維持在 18 附近，美元指數微升
*   **熱門關鍵字**：#關稅 #AI晶片 #降息預期 #比特幣ETF #地緣政治
*   **板塊觀測**：
    *   📈 **看漲/活躍**：AI 半導體、黃金、防禦型股票
    *   📉 **承壓/回調**：中小型科技股、新興市場、加密貨幣

---

## 💡 關鍵結論 (Key Takeaways)
*   美中關稅戰升級，半導體供應鏈面臨重新洗牌，台積電與三星成主要受惠者
*   Fed 維持利率不變預期攀升至 83%，市場轉向關注 2026 下半年降息路徑
*   比特幣 ETF 連續第三週淨流出，機構資金觀望態度明顯

---

## 🔥 今日十大焦點 (Top 10 Main Topics)

### 1. [宏觀] 美中關稅戰再升級：半導體成新戰場
美國宣布對中國晶片出口管制進一步收緊，限制先進 AI 晶片出口至中國及中間國。中國回應將對美國農產品加徵 25% 報復性關稅。市場分析師認為此舉將加速全球供應鏈去中國化趨勢。

**情緒**: (負面)
**相關報導** (⚠️ 務必包含連結):
- [Reuters] [美國擴大對華晶片出口管制](https://reuters.com/example1)
- [Cnyes] [台積電受惠轉單效應 股價創新高](https://cnyes.com/example1)

### 2. [加密] 比特幣 ETF 連續流出，市場信心動搖
三大比特幣現貨 ETF 本週合計淨流出 $420M，為今年最大單週流出。分析指出機構投資者在宏觀不確定性下選擇減持風險資產，但長期持有者持倉量仍維持穩定。

**情緒**: (負面)
**相關報導**:
- [動區] [BTC ETF 單週流出創新高](https://blocktempo.com/example1)
- [CNBC] [機構資金撤離加密市場](https://cnbc.com/example1)

### 3. [科技] OpenAI 發布 GPT-5 企業版，AI 軍備競賽白熱化
OpenAI 正式推出 GPT-5 Enterprise，主打多模態理解與 Code Agent 功能。同日 Google DeepMind 也宣布 Gemini Ultra 2.0 進入測試。兩大巨頭的競爭推動企業 AI 支出預計在 2026 年突破 $200B。

**情緒**: (正面)
**相關報導**:
- [TechCrunch] [OpenAI launches GPT-5 Enterprise](https://techcrunch.com/example1)
- [Forbes] [AI 軍備競賽推動企業支出創紀錄](https://forbes.com/example1)

### 4. [宏觀] Fed 會議紀要釋放鴿派訊號
聯準會最新會議紀要顯示多數委員認為「2026 年內啟動降息是適當的」，但強調需要更多通膨趨緩數據。CME FedWatch 顯示 9 月降息概率從 65% 升至 78%。

**情緒**: (正面)
**相關報導**:
- [CNBC] [Fed minutes signal rate cuts on horizon](https://cnbc.com/example2)
- [Cnyes] [聯準會會議紀要偏鴿 美股反彈](https://cnyes.com/example2)

### 5. [地緣] 伊朗核談判陷僵局，中東緊張升溫
伊朗與六國核談判在維也納破裂，雙方在鈾濃縮上限問題上無法達成共識。以色列總理發表強硬聲明，區域緊張局勢升溫推動油價突破 $85。

**情緒**: (負面)
**相關報導**:
- [BBC] [Iran nuclear talks collapse in Vienna](https://bbc.com/example1)
- [Reuters] [Oil prices surge on Middle East tensions](https://reuters.com/example2)

### 6. [科技] Nvidia 財報超預期，數據中心營收翻倍
Nvidia Q1 財報顯示數據中心營收年增 122%，AI GPU 需求持續爆發。CEO 黃仁勳預告下一代 Rubin 架構將於 2026 Q4 量產，推動盤後股價上漲 8%。

**情緒**: (正面)
**相關報導**:
- [SeekingAlpha] [Nvidia beats estimates on AI demand](https://seekingalpha.com/example1)
- [FOX] [Nvidia 財報亮眼 AI 晶片需求無上限](https://anduril.tw/example1)

### 7. [加密] Ethereum Pectra 升級成功，Gas 費用降 40%
以太坊 Pectra 硬分叉於昨日成功激活，引入 EIP-7702 帳戶抽象與 blob 擴容。鏈上 Gas 費用平均下降 40%，L2 交易成本更降至接近零。

**情緒**: (正面)
**相關報導**:
- [動區] [以太坊 Pectra 升級完成 Gas 大降](https://blocktempo.com/example2)
- [Axios] [Ethereum upgrade promises cheaper transactions](https://axios.com/example1)

### 8. [宏觀] 日本央行暗示進一步升息，日圓走強
日本央行總裁植田和男在國會證詞中暗示若通膨持續高於目標，將考慮進一步升息。USDJPY 聞訊跌至 148 附近，引發套利交易平倉擔憂。

**情緒**: (負面)
**相關報導**:
- [Reuters] [BOJ hints at more rate hikes](https://reuters.com/example3)
- [Cnyes] [日圓急升 套利交易面臨平倉壓力](https://cnyes.com/example3)

### 9. [科技] 蘋果 WWDC 預告：iOS 20 將深度整合 AI
蘋果發出 WWDC 2026 邀請函，暗示 iOS 20 將大幅強化 AI 功能，包括 Siri 完全重構與裝置端 LLM。分析師預估此舉將帶動新一波 iPhone 換機潮。

**情緒**: (正面)
**相關報導**:
- [TechCrunch] [Apple teases AI-first iOS 20](https://techcrunch.com/example2)
- [Forbes] [蘋果 AI 策略將改變行動裝置市場](https://forbes.com/example2)

### 10. [宏觀] 歐洲經濟數據疲軟，ECB 降息預期升溫
歐元區 Q1 GDP 初值僅增 0.1%，遠低於預期的 0.3%。德國工業產出連續第四個月下滑，市場預期 ECB 將在 6 月會議上降息 25bp。

**情緒**: (負面)
**相關報導**:
- [BBC] [Eurozone growth stalls amid German slump](https://bbc.com/example2)
- [NYT] [歐洲經濟困境加深 降息壓力增大](https://nyt.com/example1)

---

## 📰 其他快訊 (Other News)
- [Axios] [SpaceX Starship 第五次試飛成功回收](https://axios.com/example2)
- [BusinessInsider] [全球最大主權基金減持美股增持新興市場](https://businessinsider.com/example1)
- [CNN] [美國 3 月非農預覽：市場預期新增 18 萬人](https://cnn.com/example1)
- [動區] [Solana DEX 交易量超越以太坊](https://blocktempo.com/example3)
- [FOX] [台灣半導體出口創歷史新高](https://anduril.tw/example2)
`;

export const MOCK_DATES = ['2026-03-08', '2026-03-07', '2026-03-06', '2026-03-05', '2026-03-04'];

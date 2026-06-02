# DailyNews - AI-Powered Global Financial News Digest

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![CI](https://github.com/jasonch1u/dailynews/actions/workflows/ci.yml/badge.svg)](https://github.com/jasonch1u/dailynews/actions/workflows/ci.yml)
[![Codex review](https://img.shields.io/badge/PR%20review-Codex-black)](https://developers.openai.com/codex/)
[![Made with Python](https://img.shields.io/badge/Made%20with-Python-3776AB.svg?logo=python&logoColor=white)](https://www.python.org/)
[![Deployed on Vercel](https://img.shields.io/badge/Deployed%20on-Vercel-000000.svg?logo=vercel)](https://vercel.com/)

每日自動抓取全球財經新聞，透過 Gemini AI 生成繁體中文市場摘要報告，並提供宏觀經濟指標監控。

> **🚀 Self-hostable** — deploy your own instance to Vercel in minutes (see
> [Quick Start](#quick-start)). All you need is a free Supabase project and
> Gemini / FRED API keys.

[![Deploy with Vercel](https://vercel.com/button)](https://vercel.com/new/clone?repository-url=https%3A%2F%2Fgithub.com%2Fjasonch1u%2Fdailynews&env=SUPABASE_URL,SUPABASE_KEY,GEMINI_API_KEY,FRED_API_KEY)

## Features

- **多來源新聞聚合** — 自動爬取 13+ 國際財經來源（BlockTempo、鉅亨網、CNBC、BBC、Reuters、CNN、Forbes 等）
- **AI 每日摘要** — 使用 Gemini API 生成結構化市場報告（情緒分析、關鍵結論、深度主題）
- **經濟指標追蹤** — VIX、M2、美元指數（DXY）、殖利率曲線等，資料來自 FRED API
- **宏觀流動性監控** — Fed 淨流動性 = 總資產 - TGA - RRP，搭配 SOFR / VIX / USDJPY 信號
- **Cron 自動排程** — Vercel Cron Jobs 定時觸發新聞抓取與宏觀信號更新
- **歷史報告瀏覽** — 所有摘要存入 Supabase，支援歷史日期查閱

## Tech Stack

| Layer | Tech |
|-------|------|
| Backend | Python (FastAPI) on Vercel Serverless Functions |
| AI | Google Gemini API |
| Database | Supabase (PostgreSQL) |
| Economic Data | FRED API, NY Fed API, Yahoo Finance, Fiscal Data API |
| Frontend | Server-rendered HTML (SSR via FastAPI) |
| Hosting | Vercel |

## Quick Start

### Prerequisites

- Python 3.9+
- [Vercel CLI](https://vercel.com/docs/cli) (`npm i -g vercel`)
- Supabase 帳號（免費方案即可）
- API Keys：Gemini、FRED

### 1. Clone & Install

```bash
git clone https://github.com/jasonch1u/dailynews.git
cd dailynews
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Setup Database

在 Supabase Dashboard 的 SQL Editor 中執行 `supabase_schema.sql`，建立所需 tables：

- `news_summaries` — 每日 AI 摘要
- `articles` — 各來源原始文章快取
- `error_logs` — 系統錯誤紀錄
- `market_liquidity` — Fed 流動性數據
- `economic_indicators` — VIX、M2 等經濟指標
- `macro_snapshots` — 宏觀信號快照

### 3. Environment Variables

建立 `.env` 檔案（不要 commit）：

```env
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-anon-or-service-role-key
GEMINI_API_KEY=your-gemini-api-key
FRED_API_KEY=your-fred-api-key
```

| Variable | Description | Where to Get |
|----------|-------------|--------------|
| `SUPABASE_URL` | Supabase 專案 URL | [Supabase Dashboard](https://supabase.com/dashboard) → Settings → API |
| `SUPABASE_KEY` | Supabase API Key（建議用 `service_role` key） | 同上 |
| `GEMINI_API_KEY` | Google Gemini API Key | [Google AI Studio](https://aistudio.google.com/apikey) |
| `FRED_API_KEY` | FRED 經濟數據 API Key | [FRED API Keys](https://fred.stlouisfed.org/docs/api/api_key.html) |

### 4. Local Development

```bash
vercel dev
```

瀏覽器開啟 `http://localhost:3000` 即可看到前端。

### 5. Deploy to Vercel

```bash
vercel --prod
```

在 Vercel Dashboard 設定上述環境變數（Settings → Environment Variables）。

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/` | 前端頁面 |
| `GET` | `/api/summarize` | 取得今日摘要（有快取時回傳快取） |
| `GET` | `/api/summarize?refresh=true` | 強制重新抓取 + AI 生成（SSE streaming） |
| `GET` | `/api/summarize?date=2025-03-20` | 查詢歷史摘要 |
| `GET` | `/api/history` | 取得所有可用日期列表 |
| `GET` | `/api/articles?date=2025-03-20` | 取得特定日期的原始文章列表 |
| `GET` | `/api/liquidity` | 取得 Fed 流動性數據 |
| `GET` | `/api/economics` | 取得經濟指標（VIX, M2, DXY 等） |
| `GET` | `/api/macro-signal` | 取得宏觀交易信號（含快取） |
| `GET` | `/api/macro-signal/refresh` | 強制刷新宏觀信號 |

## Cron Jobs

在 `vercel.json` 中設定，自動排程：

| Schedule (UTC) | Endpoint | Purpose |
|----------------|----------|---------|
| `0 1 * * *` (每天 09:00 台灣) | `/api/summarize?refresh=true` | 早報 |
| `0 7 * * *` (每天 15:00 台灣) | `/api/summarize?refresh=true` | 午報 |
| `0 14 * * *` (每天 22:00 台灣) | `/api/macro-signal/refresh` | 宏觀信號更新（美股盤中） |
| `0 22 * * *` (每天 06:00 台灣) | `/api/macro-signal/refresh` | 宏觀信號更新（美股收盤後） |

## News Sources

| Source | Language | Category |
|--------|----------|----------|
| BlockTempo 動區 | 中文 | Crypto |
| 鉅亨網 (Cnyes) | 中文 | Finance |
| CNBC | English | Finance |
| Seeking Alpha | English | Finance |
| BBC | English | World |
| CNN | English | World |
| Reuters | English | World |
| NYT | English | World |
| TechCrunch | English | Tech |
| Forbes | English | Business |
| Business Insider | English | Business |
| Axios | English | News |
| Anduril | English | Defense/Tech |

英文來源的標題會自動翻譯為繁體中文。

## Project Structure

```
dailynews/
├── api/
│   ├── index.py          # FastAPI app, all route handlers
│   ├── db.py             # Supabase client wrapper
│   ├── llm_utils.py      # Gemini API calls, summarization prompt
│   ├── fred_utils.py     # FRED API client (economic indicators)
│   ├── macro_utils.py    # Macro liquidity monitor (SOFR, TGA, VIX)
│   └── templates.py      # HTML frontend template
├── scrapers.py           # News scrapers for all sources
├── supabase_schema.sql   # Database schema
├── requirements.txt      # Python dependencies
├── vercel.json           # Vercel config (rewrites + cron jobs)
└── public/
    └── favicon.ico
```

## Development with Codex

This project is built for AI-assisted maintenance:

- [`AGENTS.md`](AGENTS.md) documents the architectural rules that coding agents
  (including [OpenAI Codex](https://developers.openai.com/codex/)) must follow when
  changing the summarization pipeline.
- Every pull request is automatically reviewed by Codex via
  [`.github/workflows/codex-review.yml`](.github/workflows/codex-review.yml) (powered
  by [`openai/codex-action`](https://github.com/openai/codex-action)), which checks
  correctness, scraper resilience, secret leakage, and Vercel timeout constraints.
  Review criteria live in [`.github/codex/prompts/review.md`](.github/codex/prompts/review.md).

To enable Codex review on a fork, add an `OPENAI_API_KEY` repository secret.

## Contributing

Contributions are welcome — see [`CONTRIBUTING.md`](CONTRIBUTING.md) and our
[Code of Conduct](CODE_OF_CONDUCT.md). For security issues, see
[`SECURITY.md`](SECURITY.md).

## License

Released under the [MIT License](LICENSE).

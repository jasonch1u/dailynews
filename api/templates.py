# This file contains the HTML template for the frontend.
HTML_CONTENT = r"""<!DOCTYPE html>
<html lang="zh-TW">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>每日新聞 AI 摘要</title>
    <link rel="icon" href="data:image/svg+xml,<svg xmlns=%22http://www.w3.org/2000/svg%22 viewBox=%220 0 100 100%22><text y=%22.9em%22 font-size=%2290%22>📰</text></svg>">
    <script src="https://cdn.jsdelivr.net/npm/marked/marked.min.js"></script>
    <style>
        :root {
            --primary-color: #0d6efd;
            --bg-color: #f8f9fa;
            --card-bg: #ffffff;
            --text-color: #333;
        }
        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
            max-width: 900px;
            margin: 0 auto;
            padding: 20px;
            background-color: var(--bg-color);
            color: var(--text-color);
        }
        header {
            text-align: center;
            margin-bottom: 30px;
            padding-bottom: 20px;
            border-bottom: 1px solid #dee2e6;
        }
        h1 { color: #2c3e50; margin-bottom: 10px; }

        /* Controls Section */
        .controls-container {
            background: var(--card-bg);
            padding: 20px;
            border-radius: 12px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.05);
            margin-bottom: 20px;
        }

        .control-group {
            margin-bottom: 15px;
            display: flex;
            align-items: center;
            justify-content: center;
            flex-wrap: wrap;
            gap: 15px;
        }

        .source-checkboxes {
            display: flex;
            gap: 15px;
            align-items: center;
            background: #f1f3f5;
            padding: 8px 15px;
            border-radius: 20px;
        }
        .source-checkboxes label {
            cursor: pointer;
            user-select: none;
            display: flex;
            align-items: center;
            gap: 5px;
        }

        select {
            padding: 8px 12px;
            border-radius: 6px;
            border: 1px solid #ced4da;
        }

        button.primary-btn {
            background-color: var(--primary-color);
            color: white;
            border: none;
            padding: 12px 28px;
            font-size: 16px;
            font-weight: 600;
            border-radius: 8px;
            cursor: pointer;
            transition: all 0.2s;
            box-shadow: 0 2px 4px rgba(13, 110, 253, 0.2);
        }
        button.primary-btn:hover {
            background-color: #0b5ed7;
            transform: translateY(-1px);
        }
        button.primary-btn:disabled {
            background-color: #6c757d;
            cursor: not-allowed;
            transform: none;
        }

        /* Status */
        #status {
            text-align: center;
            margin: 15px 0;
            font-weight: 500;
            color: #666;
            min-height: 24px;
        }

        /* Layout Grid for Results */
        .results-container {
            display: grid;
            grid-template-columns: 2fr 1fr; /* Summary takes more space, List takes less */
            gap: 20px;
            align-items: start;
        }
        @media (max-width: 768px) {
            .results-container { grid-template-columns: 1fr; }
        }

        /* Summary Content */
        #content {
            background: var(--card-bg);
            padding: 40px;
            border-radius: 12px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.08);
            line-height: 1.7;
            min-height: 200px;
        }
        #content h2 { border-bottom: 2px solid #f1f3f5; padding-bottom: 10px; margin-top: 30px; }
        #content h3 { color: #495057; margin-top: 20px; }
        #content ul { padding-left: 20px; }
        #content li { margin-bottom: 8px; }
        #content a { color: var(--primary-color); text-decoration: none; }
        #content a:hover { text-decoration: underline; }
        #content blockquote {
            border-left: 4px solid #ced4da;
            margin: 0;
            padding-left: 15px;
            color: #6c757d;
        }

        /* Article List Sidebar */
        #articleList {
            background: var(--card-bg);
            padding: 20px;
            border-radius: 12px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.08);
        }
        #articleList h3 { margin-top: 0; color: #495057; font-size: 1.1em; border-bottom: 1px solid #dee2e6; padding-bottom: 10px; }
        .article-item {
            padding: 10px 0;
            border-bottom: 1px solid #f1f3f5;
            font-size: 0.95em;
        }
        .article-item:last-child { border-bottom: none; }
        .article-source {
            font-size: 0.75em;
            color: #fff;
            background: #6c757d;
            padding: 2px 6px;
            border-radius: 4px;
            margin-right: 5px;
            vertical-align: middle;
        }
        .article-link {
            color: #333;
            text-decoration: none;
            font-weight: 500;
        }
        .article-link:hover { color: var(--primary-color); }

        .loader {
            border: 3px solid #f3f3f3;
            border-top: 3px solid var(--primary-color);
            border-radius: 50%;
            width: 18px;
            height: 18px;
            animation: spin 1s linear infinite;
            display: inline-block;
            vertical-align: middle;
            margin-right: 8px;
        }
        @keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }
    </style>
</head>
<body>
    <header>
        <h1>📰 每日新聞 AI 摘要</h1>
        <p>即時聚合 Anduril, BlockTempo, 鉅亨網 | 智慧分析與情緒判讀</p>
    </header>

    <div class="controls-container">
        <!-- Sources -->
        <div class="control-group">
            <span>📡 來源選擇：</span>
            <div class="source-checkboxes">
                <label><input type="checkbox" value="anduril" checked> Anduril</label>
                <label><input type="checkbox" value="blocktempo" checked> BlockTempo</label>
                <label><input type="checkbox" value="cnyes" checked> 鉅亨網</label>
            </div>
        </div>

        <!-- History -->
        <div class="control-group">
            <span>📅 日期：</span>
            <select id="historySelect" onchange="handleDateChange()">
                <option value="">今日最新 (Live)</option>
            </select>
        </div>

        <!-- Action -->
        <div class="control-group">
             <button id="generateBtn" class="primary-btn" onclick="fetchSummary()">🚀 開始分析與摘要</button>
        </div>

        <div id="status"></div>
    </div>

    <div class="results-container">
        <!-- AI Summary -->
        <div id="content">
            <div style="text-align: center; color: #adb5bd; margin-top: 50px;">
                <h3>👋 歡迎使用</h3>
                <p>請選擇新聞來源並點擊上方按鈕開始生成報告。</p>
            </div>
        </div>

        <!-- Raw Article List -->
        <div id="articleList">
            <h3>📑 原始文章列表</h3>
            <div id="articleListContent" style="color: #999; font-size: 0.9em; text-align: center;">
                (尚無資料)
            </div>
        </div>
    </div>

    <script>
        // Open all links in new tab
        const renderer = new marked.Renderer();
        renderer.link = function(href, title, text) {
            return `<a href="${href}" title="${title || ''}" target="_blank" rel="noopener noreferrer">${text}</a>`;
        };
        marked.setOptions({ renderer: renderer });

        window.addEventListener('DOMContentLoaded', async () => {
            await loadHistoryDates();
            // Optional: Auto load today's article list on start?
            // loadArticlesList("");
        });

        async function loadHistoryDates() {
            const select = document.getElementById('historySelect');
            try {
                const res = await fetch('/api/history');
                if (res.ok) {
                    const data = await res.json();
                    if (data.dates) {
                        data.dates.forEach(date => {
                            const opt = document.createElement('option');
                            opt.value = date;
                            opt.text = date;
                            select.appendChild(opt);
                        });
                    }
                }
            } catch (e) { console.error(e); }
        }

        async function handleDateChange() {
            const date = document.getElementById('historySelect').value;

            // 1. Manage Checkboxes
            if (date) {
                document.querySelectorAll('input[type=checkbox]').forEach(el => el.disabled = true);
            } else {
                document.querySelectorAll('input[type=checkbox]').forEach(el => el.disabled = false);
            }

            // 2. Fetch Article List immediately for the selected date
            await loadArticlesList(date);
        }

        async function loadArticlesList(date) {
            const listContainer = document.getElementById('articleListContent');
            listContainer.innerHTML = '<span class="loader"></span> 載入中...';

            try {
                // If date is empty, use today's date
                const targetDate = date || new Date().toISOString().split('T')[0];
                const res = await fetch(`/api/articles?date=${targetDate}`);

                if (res.ok) {
                    const data = await res.json();
                    if (data.articles && data.articles.length > 0) {
                        let html = '';
                        data.articles.forEach(art => {
                            let sourceColor = '#6c757d'; // default gray
                            if(art.source.toLowerCase() === 'cnyes') sourceColor = '#dc3545'; // red
                            if(art.source.toLowerCase() === 'blocktempo') sourceColor = '#fd7e14'; // orange
                            if(art.source.toLowerCase() === 'anduril') sourceColor = '#0d6efd'; // blue

                            html += `
                            <div class="article-item">
                                <span class="article-source" style="background:${sourceColor}">${art.source}</span>
                                <a href="${art.url}" class="article-link" target="_blank">${art.title}</a>
                            </div>`;
                        });
                        listContainer.innerHTML = html;
                    } else {
                        listContainer.innerHTML = '此日期尚無已存檔的文章。';
                    }
                } else {
                    listContainer.innerHTML = '載入失敗。';
                }
            } catch (e) {
                console.error(e);
                listContainer.innerHTML = '載入錯誤。';
            }
        }

        async function fetchSummary() {
            const btn = document.getElementById('generateBtn');
            const status = document.getElementById('status');
            const content = document.getElementById('content');
            const historyDate = document.getElementById('historySelect').value;

            const checkboxes = document.querySelectorAll('.source-checkboxes input:checked');
            const sources = Array.from(checkboxes).map(cb => cb.value).join(',');

            if (!historyDate && sources.length === 0) {
                alert("請至少選擇一個新聞來源！");
                return;
            }

            btn.disabled = true;
            status.innerHTML = `<span class="loader"></span> ${historyDate ? '正在載入歷史檔案...' : '正在掃描最新文章並檢查快取...'}`;
            content.style.opacity = '0.5';

            // Also reload article list to catch any newly scraped ones (if Live)
            // But we do it *after* scraping potentially?
            // Better flow:
            // 1. Trigger Summarize (which scrapes)
            // 2. Then reload List

            try {
                let url = '/api/summarize';
                const params = new URLSearchParams();
                if (historyDate) params.append('date', historyDate);
                if (!historyDate && sources) params.append('sources', sources);

                const res = await fetch(`${url}?${params.toString()}`);

                if (res.status === 404) {
                    content.innerHTML = '<p style="text-align:center; color: #888;">查無資料。</p>';
                    status.innerHTML = '';
                    return;
                }

                const data = await res.json();

                if (data.markdown) {
                    content.innerHTML = marked.parse(data.markdown);
                    status.innerHTML = `✅ 完成！ (來源: ${data.source === 'cache' ? '資料庫快取' : '即時生成'})`;
                    status.style.color = 'green';
                } else {
                    status.innerHTML = '❌ 發生錯誤';
                }

                // If live update, reload the list to show newly scraped items
                if (!historyDate) {
                    await loadArticlesList("");
                }

            } catch (error) {
                console.error(error);
                status.innerHTML = `❌ 錯誤: ${error.message}`;
            } finally {
                btn.disabled = false;
                content.style.opacity = '1';
            }
        }
    </script>
</body>
</html>"""

# This file contains the HTML template for the frontend.
HTML_CONTENT = r"""<!DOCTYPE html>
<html lang="zh-TW">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>每日新聞 AI 摘要</title>
    <link rel="icon" href="data:image/svg+xml,<svg xmlns=%22http://www.w3.org/2000/svg%22 viewBox=%220 0 100 100%22><text y=%22.9em%22 font-size=%2290%22>📰</text></svg>">
    <!-- Pin marked.js version to 4.3.0 to ensure renderer.link(href, title, text) signature works as expected -->
    <script src="https://cdn.jsdelivr.net/npm/marked@4.3.0/marked.min.js"></script>
    <style>
        :root {
            --primary-color: #0d6efd;
            --bg-color: #f8f9fa;
            --card-bg: #ffffff;
            --text-color: #333;
            --header-height: 70px;
        }
        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
            margin: 0;
            padding: 0;
            background-color: var(--bg-color);
            color: var(--text-color);
            padding-top: calc(var(--header-height) + 20px); /* Space for sticky header */
        }

        /* Sticky Header */
        header {
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            height: var(--header-height);
            background: rgba(255, 255, 255, 0.95);
            backdrop-filter: blur(10px);
            border-bottom: 1px solid #dee2e6;
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 0 20px;
            z-index: 1000;
            box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        }

        .header-left {
            display: flex;
            align-items: center;
            gap: 15px;
        }

        h1 {
            font-size: 1.25rem;
            margin: 0;
            color: #2c3e50;
            white-space: nowrap;
        }

        .header-controls {
            display: flex;
            align-items: center;
            gap: 15px;
        }

        /* Source Dropdown (Compact) */
        .source-dropdown {
            position: relative;
            display: inline-block;
        }
        .source-btn {
            background: #f8f9fa;
            border: 1px solid #dee2e6;
            padding: 8px 12px;
            border-radius: 6px;
            cursor: pointer;
            font-size: 0.9rem;
            display: flex;
            align-items: center;
            gap: 5px;
        }
        .source-btn:hover { background: #e9ecef; }
        .source-content {
            display: none;
            position: absolute;
            top: 100%;
            right: 0; /* Align right */
            background-color: white;
            min-width: 200px;
            box-shadow: 0 8px 16px rgba(0,0,0,0.1);
            padding: 12px;
            border-radius: 8px;
            border: 1px solid #dee2e6;
            z-index: 1001;
            margin-top: 5px;
        }
        .source-dropdown:hover .source-content {
            display: block;
        }
        .source-content label {
            display: block;
            padding: 5px 0;
            cursor: pointer;
        }

        select {
            padding: 8px 12px;
            border-radius: 6px;
            border: 1px solid #ced4da;
            font-size: 0.9rem;
        }

        button.primary-btn {
            background-color: var(--primary-color);
            color: white;
            border: none;
            padding: 8px 16px;
            font-size: 0.9rem;
            font-weight: 600;
            border-radius: 6px;
            cursor: pointer;
            transition: all 0.2s;
            white-space: nowrap;
        }
        button.primary-btn:hover {
            background-color: #0b5ed7;
        }
        button.primary-btn:disabled {
            background-color: #6c757d;
            cursor: not-allowed;
        }

        /* Layout Grid */
        .main-container {
            max-width: 1200px;
            margin: 0 auto;
            padding: 0 20px;
            display: grid;
            grid-template-columns: 3fr 1fr;
            gap: 20px;
            align-items: start;
        }

        @media (max-width: 900px) {
            .main-container { grid-template-columns: 1fr; }
            header {
                height: auto;
                flex-direction: column;
                padding: 10px 20px;
                gap: 10px;
            }
            body { padding-top: 140px; } /* Adjust for taller header */
            .header-controls { flex-wrap: wrap; justify-content: center; }
        }

        /* Status Bar */
        #status {
            text-align: center;
            margin: 10px 0 20px 0;
            font-weight: 500;
            color: #666;
            min-height: 24px;
        }

        /* Content Styles */
        #content {
            background: var(--card-bg);
            padding: 30px;
            border-radius: 12px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.05);
            line-height: 1.7;
            min-height: 300px;
        }
        #content h2 { border-bottom: 2px solid #f1f3f5; padding-bottom: 10px; margin-top: 30px; }
        #content h3 { color: #495057; margin-top: 20px; }
        #content p { margin-bottom: 15px; }
        #content a { color: var(--primary-color); text-decoration: none; }
        #content a:hover { text-decoration: underline; }

        /* Article List Sidebar */
        #articleList {
            background: var(--card-bg);
            padding: 20px;
            border-radius: 12px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.05);
            position: sticky;
            top: calc(var(--header-height) + 20px);
            max-height: calc(100vh - 100px);
            overflow-y: auto;
        }
        #articleList h3 { margin-top: 0; font-size: 1.1em; border-bottom: 1px solid #dee2e6; padding-bottom: 10px; color: #495057; }
        #articleListContent { text-align: left; }

        .article-item {
            padding: 10px 0;
            border-bottom: 1px solid #f1f3f5;
            font-size: 0.9rem;
            display: flex;
            align-items: baseline;
            gap: 8px;
        }
        .article-item:last-child { border-bottom: none; }
        .article-source {
            font-size: 0.75rem;
            color: #fff;
            padding: 2px 6px;
            border-radius: 4px;
            white-space: nowrap;
            flex-shrink: 0;
        }
        .article-link {
            color: #333;
            text-decoration: none;
            line-height: 1.4;
        }
        .article-link:hover { color: var(--primary-color); }

        .loader {
            border: 2px solid #f3f3f3;
            border-top: 2px solid var(--primary-color);
            border-radius: 50%;
            width: 14px;
            height: 14px;
            animation: spin 1s linear infinite;
            display: inline-block;
            vertical-align: middle;
            margin-right: 5px;
        }
        @keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }
    </style>
</head>
<body>
    <header>
        <div class="header-left">
            <div style="font-size: 1.5rem;">📰</div>
            <h1>每日新聞 AI 摘要</h1>
        </div>

        <div class="header-controls">
            <!-- Source Selector -->
            <div class="source-dropdown">
                <div class="source-btn">📡 來源篩選 ▼</div>
                <div class="source-content source-checkboxes">
                    <label><input type="checkbox" value="anduril" checked> Anduril</label>
                    <label><input type="checkbox" value="blocktempo" checked> BlockTempo</label>
                    <label><input type="checkbox" value="cnyes" checked> 鉅亨網</label>
                </div>
            </div>

            <!-- Date Selector -->
            <select id="historySelect" onchange="handleDateChange()">
                <option value="">-- 載入中 --</option>
            </select>

            <!-- Generate Button -->
            <button id="generateBtn" class="primary-btn" onclick="fetchSummary()">🚀 生成摘要</button>
        </div>
    </header>

    <div id="status"></div>

    <div class="main-container">
        <!-- AI Summary Area -->
        <div id="content">
            <div style="text-align: center; color: #adb5bd; margin-top: 50px;">
                <h3>👋 歡迎使用</h3>
                <p>正在連線資料庫取得最新內容...</p>
            </div>
        </div>

        <!-- Raw Article List Sidebar -->
        <div id="articleList">
            <h3>📑 原始文章列表</h3>
            <div id="articleListContent" style="color: #999; font-size: 0.9em;">
                (尚無資料)
            </div>
        </div>
    </div>

    <script>
        const renderer = new marked.Renderer();
        renderer.link = function(href, title, text) {
            return `<a href="${href}" title="${title || ''}" target="_blank" rel="noopener noreferrer">${text}</a>`;
        };
        marked.setOptions({ renderer: renderer });

        window.addEventListener('DOMContentLoaded', async () => {
            await loadHistoryDates();
        });

        async function loadHistoryDates() {
            const select = document.getElementById('historySelect');
            try {
                const res = await fetch('/api/history');
                if (res.ok) {
                    const data = await res.json();
                    select.innerHTML = '';

                    let hasHistory = data.dates && data.dates.length > 0;

                    if (hasHistory) {
                        data.dates.forEach(date => {
                            const opt = document.createElement('option');
                            opt.value = date;
                            opt.text = date;
                            select.appendChild(opt);
                        });
                        select.value = data.dates[0];
                        handleDateChange();
                    } else {
                        const opt = document.createElement('option');
                        opt.value = "";
                        opt.text = "今日最新 (Live)";
                        select.appendChild(opt);
                        handleDateChange();
                    }
                }
            } catch (e) {
                console.error(e);
                select.innerHTML = '<option value="">無法載入日期</option>';
            }
        }

        async function handleDateChange() {
            const date = document.getElementById('historySelect').value;

            if (date) {
                document.querySelectorAll('input[type=checkbox]').forEach(el => el.disabled = true);
            } else {
                document.querySelectorAll('input[type=checkbox]').forEach(el => el.disabled = false);
            }

            await loadArticlesList(date);

            if (date) {
               fetchSummary(true);
            }
        }

        async function loadArticlesList(date) {
            const listContainer = document.getElementById('articleListContent');
            listContainer.innerHTML = '<span class="loader"></span> 載入中...';

            try {
                const targetDate = date || new Date().toISOString().split('T')[0];
                const res = await fetch(`/api/articles?date=${targetDate}`);

                if (res.ok) {
                    const data = await res.json();
                    if (data.articles && data.articles.length > 0) {
                        let html = '';
                        data.articles.forEach(art => {
                            let sourceColor = '#6c757d';
                            let displaySource = art.source;

                            if(art.source.toLowerCase().includes('cnyes')) {
                                sourceColor = '#dc3545';
                            }
                            if(art.source.toLowerCase().includes('blocktempo')) {
                                sourceColor = '#fd7e14';
                                displaySource = '動區';
                            }
                            if(art.source.toLowerCase().includes('anduril')) {
                                sourceColor = '#0d6efd';
                            }

                            html += `
                            <div class="article-item">
                                <span class="article-source" style="background:${sourceColor}">${displaySource}</span>
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

        async function fetchSummary(isAutoLoad = false) {
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
            status.innerHTML = `<span class="loader"></span> ${historyDate ? '正在載入摘要...' : '正在掃描與分析...'}`;
            content.style.opacity = '0.5';

            try {
                let url = '/api/summarize';
                const params = new URLSearchParams();
                if (historyDate) params.append('date', historyDate);
                if (!historyDate && sources) params.append('sources', sources);

                const res = await fetch(`${url}?${params.toString()}`);

                if (res.status === 404) {
                    content.innerHTML = '<div style="text-align: center; margin-top: 50px;"><h3>⚠️ 尚無摘要</h3><p>請點擊上方按鈕生成。</p></div>';
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

                if (!historyDate && !isAutoLoad) {
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

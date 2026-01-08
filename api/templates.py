# This file contains the HTML template for the frontend.
HTML_CONTENT = r"""<!DOCTYPE html>
<html lang="zh-TW">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>每日新聞 AI 摘要</title>
    <link rel="icon" href="data:image/svg+xml,<svg xmlns=%22http://www.w3.org/2000/svg%22 viewBox=%220 0 100 100%22><text y=%22.9em%22 font-size=%2290%22>📰</text></svg>">
    <!-- Pin marked.js version to 4.3.0 -->
    <script src="https://cdn.jsdelivr.net/npm/marked@4.3.0/marked.min.js"></script>
    <!-- Lightweight Charts for Fed Liquidity -->
    <script src="https://unpkg.com/lightweight-charts/dist/lightweight-charts.standalone.production.js"></script>
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

        /* Liquidity Badge */
        #liquidity-badge {
            background: #e7f5ff;
            color: #0d6efd;
            border: 1px solid #0d6efd;
            border-radius: 6px;
            padding: 8px 12px;
            font-size: 0.9rem;
            font-weight: 600;
            cursor: pointer;
            margin-left: 15px;
            white-space: nowrap;
            transition: all 0.2s;
        }
        #liquidity-badge:hover {
            background: #d0e8ff;
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

        /* Status Bar and Progress */
        #status-container {
            max-width: 600px;
            margin: 10px auto 20px auto;
            text-align: center;
        }
        #status-text {
            font-weight: 500;
            color: #666;
            min-height: 24px;
            margin-bottom: 8px;
        }
        #progress-bar-container {
            width: 100%;
            height: 4px;
            background-color: #e9ecef;
            border-radius: 4px;
            overflow: hidden;
            display: none; /* Hidden by default */
        }
        #progress-bar {
            width: 0%;
            height: 100%;
            background-color: var(--primary-color);
            transition: width 0.5s ease-in-out;
        }

        /* Content Styles */
        #content {
            background: var(--card-bg);
            padding: 30px;
            border-radius: 12px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.05);
            line-height: 1.7;
            min-height: 300px;
            overflow-x: hidden; /* Prevent horizontal scroll causing layout break */
        }
        #content h2 { border-bottom: 2px solid #f1f3f5; padding-bottom: 10px; margin-top: 30px; }
        #content h3 { color: #495057; margin-top: 25px; margin-bottom: 15px; }
        #content p { margin-bottom: 15px; }
        #content ul { padding-left: 20px; }
        #content li { margin-bottom: 8px; }
        #content a { color: var(--primary-color); text-decoration: none; }
        #content a:hover { text-decoration: underline; }

        /* Styles for Dynamic Source Tags (Generated by Regex) */
        #content .article-source {
            font-size: 0.8rem;
            color: #fff;
            padding: 2px 8px;
            border-radius: 4px;
            margin-right: 8px;
            vertical-align: middle;
            font-weight: normal;
            background: #6c757d; /* Default */
            display: inline-block; /* Ensure proper spacing */
            margin-bottom: 2px;
            text-decoration: none !important; /* Remove underline from link badges */
        }

        /* Specific Source Colors */
        #content .source-cnyes { background: #dc3545; }
        #content .source-blocktempo { background: #fd7e14; }
        #content .source-anduril { background: #0d6efd; }
        #content .source-cnbc { background: #20c997; }
        #content .source-seekingalpha { background: #ffc107; color: #333 !important; }
        #content .source-marketwatch { background: #6610f2; }
        #content .source-fox { background: #0d6efd; }
        #content .source-bbc { background: #b80000; }
        #content .source-cnn { background: #cc0000; }
        #content .source-techcrunch { background: #00a562; }
        #content .source-forbes { background: #333333; }
        #content .source-businessinsider { background: #1c1c1c; }
        #content .source-axios { background: #2251ff; }
        #content .source-nyt { background: #000000; }
        #content .source-reuters { background: #ff8000; }

        /* Compact Related Reports Container */
        .related-reports-container {
            display: flex;
            flex-wrap: wrap;
            gap: 8px;
            margin-top: 10px;
            align-items: center;
        }
        .related-label {
            font-weight: 600;
            color: #666;
            font-size: 0.9em;
            margin-right: 5px;
        }

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
            /* Ensure sidebar doesn't get squashed */
            min-width: 250px;
        }
        #articleList h3 { margin-top: 0; font-size: 1.1em; border-bottom: 1px solid #dee2e6; padding-bottom: 10px; color: #495057; }
        #articleListContent { text-align: left; }

        .article-item {
            padding: 10px 0;
            border-bottom: 1px solid #f1f3f5;
            font-size: 0.9rem;
            display: flex;
            flex-direction: column;
            align-items: flex-start;
            gap: 5px;
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

        /* Toast Notification */
        #toast-container {
            position: fixed;
            top: 20px;
            right: 20px;
            z-index: 2000;
        }
        .toast {
            background-color: #333;
            color: white;
            padding: 12px 20px;
            border-radius: 8px;
            margin-bottom: 10px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
            display: flex;
            align-items: center;
            gap: 10px;
            opacity: 0;
            transform: translateY(-20px);
            transition: all 0.3s ease;
        }
        .toast.show {
            opacity: 1;
            transform: translateY(0);
        }
        .toast.success { background-color: #198754; }
        .toast.error { background-color: #dc3545; }
        .toast.info { background-color: #0d6efd; }

        /* Modal Styles */
        .modal-overlay {
            display: none;
            position: fixed;
            top: 0; left: 0; width: 100%; height: 100%;
            background: rgba(0,0,0,0.5);
            z-index: 2000;
            justify-content: center;
            align-items: center;
        }
        .modal-content {
            background: white;
            padding: 20px;
            border-radius: 12px;
            width: 90%;
            max-width: 900px;
            box-shadow: 0 4px 20px rgba(0,0,0,0.2);
            position: relative;
        }
        .modal-close {
            position: absolute;
            top: 15px;
            right: 15px;
            background: none;
            border: none;
            font-size: 1.5rem;
            cursor: pointer;
            color: #666;
        }
        #chart-container {
            width: 100%;
            height: 400px;
            margin-top: 10px;
        }
    </style>
</head>
<body>
    <header>
        <div class="header-left">
            <div style="font-size: 1.5rem;">📰</div>
            <h1>每日新聞 AI 摘要</h1>
            <!-- Moved Date Selector Here -->
            <select id="historySelect" onchange="handleDateChange()" style="margin-left: 10px;">
                <option value="">-- 載入中 --</option>
            </select>
            <!-- Liquidity Badge -->
            <div id="liquidity-badge" onclick="openLiquidityModal()" title="點擊查看 Fed 流動性圖表">
                Net Liquidity: <span id="liquidity-val">...</span>
            </div>
        </div>

        <div class="header-controls">
            <!-- Source Selector -->
            <div class="source-dropdown">
                <div class="source-btn">📡 來源篩選 ▼</div>
                <div class="source-content source-checkboxes">
                    <label><input type="checkbox" value="anduril" checked> FOX</label>
                    <label><input type="checkbox" value="blocktempo" checked> 動區</label>
                    <label><input type="checkbox" value="cnyes" checked> 鉅亨網</label>
                    <hr style="margin: 5px 0; border: 0; border-top: 1px solid #eee;">
                    <label><input type="checkbox" value="cnbc" checked> CNBC (World)</label>
                    <label><input type="checkbox" value="seekingalpha" checked> Seeking Alpha</label>
                    <label><input type="checkbox" value="marketwatch"> MarketWatch</label>
                    <hr style="margin: 5px 0; border: 0; border-top: 1px solid #eee;">
                    <label><input type="checkbox" value="bbc" checked> BBC</label>
                    <label><input type="checkbox" value="cnn" checked> CNN</label>
                    <label><input type="checkbox" value="reuters" checked> Reuters</label>
                    <label><input type="checkbox" value="nyt" checked> NYT</label>
                    <label><input type="checkbox" value="techcrunch" checked> TechCrunch</label>
                    <label><input type="checkbox" value="forbes" checked> Forbes</label>
                    <label><input type="checkbox" value="axios" checked> Axios</label>
                    <label><input type="checkbox" value="businessinsider" checked> Business Insider</label>
                </div>
            </div>

            <!-- Generate Button (Now specifically for Live Update) -->
            <button id="generateBtn" class="primary-btn" onclick="fetchSummary(true)">🚀 更新今日摘要</button>
        </div>
    </header>

    <div id="status-container">
        <div id="status-text"></div>
        <div id="progress-bar-container">
            <div id="progress-bar"></div>
        </div>
    </div>

    <div id="toast-container"></div>

    <!-- Liquidity Modal -->
    <div id="liquidityModal" class="modal-overlay" onclick="if(event.target === this) closeLiquidityModal()">
        <div class="modal-content">
            <button class="modal-close" onclick="closeLiquidityModal()">&times;</button>
            <div style="display:flex; justify-content:space-between; align-items:center;">
                <h2 style="margin:0;">🏦 Fed Net Liquidity 趨勢圖</h2>
                <button class="primary-btn" onclick="fetchLiquidity(true)" style="padding: 4px 10px; font-size: 0.8rem;">🔄 更新數據</button>
            </div>
            <p style="color:#666; font-size:0.9rem; margin: 10px 0;">
                Net Liquidity = Fed Assets - TGA - RRP (每週三更新)<br>
                單位: Trillion USD (兆美元)
            </p>
            <div id="chart-container"></div>
        </div>
    </div>

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
        marked.setOptions({
            renderer: renderer,
            breaks: true,
            gfm: true
        });

        // Toast Function
        function showToast(message, type = 'info') {
            const container = document.getElementById('toast-container');
            const toast = document.createElement('div');
            toast.className = `toast ${type}`;
            toast.innerText = message;

            container.appendChild(toast);

            // Trigger animation
            setTimeout(() => toast.classList.add('show'), 10);

            // Remove after 3s
            setTimeout(() => {
                toast.classList.remove('show');
                setTimeout(() => toast.remove(), 300);
            }, 3000);
        }

        function updateProgress(step, text) {
            const barContainer = document.getElementById('progress-bar-container');
            const bar = document.getElementById('progress-bar');
            const statusText = document.getElementById('status-text');

            statusText.innerHTML = `<span class="loader"></span> ${text}`;
            barContainer.style.display = 'block';

            // Map steps to percentage
            let pct = 0;
            if (step === 1) pct = 30; // Scrapers
            else if (step === 2) pct = 60; // DB
            else if (step === 3) pct = 90; // AI
            else if (step === 4) pct = 100; // Done

            bar.style.width = `${pct}%`;
        }

        function hideProgress() {
            document.getElementById('progress-bar-container').style.display = 'none';
            document.getElementById('status-text').innerText = '';
        }

        window.addEventListener('DOMContentLoaded', async () => {
            await loadHistoryDates();
            fetchLiquidity(false); // Fetch on load
        });

        // --- Liquidity Logic ---
        let chart;
        let lineSeries;

        function openLiquidityModal() {
            document.getElementById('liquidityModal').style.display = 'flex';
            if (!chart) initChart(); // Init if not exists
        }

        function closeLiquidityModal() {
            document.getElementById('liquidityModal').style.display = 'none';
        }

        async function fetchLiquidity(refresh = false) {
            const valSpan = document.getElementById('liquidity-val');
            try {
                if (refresh) valSpan.innerText = "更新中...";
                const res = await fetch(`/api/liquidity${refresh ? '?refresh=true' : ''}`);
                if (res.ok) {
                    const json = await res.json();
                    const data = json.data;

                    if (data && data.length > 0) {
                        // Update Badge (Latest value)
                        const latest = data[data.length - 1];
                        const valTrillion = (latest.net_liquidity / 1000000).toFixed(2);
                        valSpan.innerText = `$${valTrillion}T`;

                        // Prepare Chart Data
                        // Lightweight Charts expects { time: 'yyyy-mm-dd', value: 123 }
                        const chartData = data.map(d => ({
                            time: d.date,
                            value: d.net_liquidity / 1000000 // Convert Millions to Trillions
                        }));

                        if (chart && lineSeries) {
                            lineSeries.setData(chartData);
                            chart.timeScale().fitContent();
                        } else {
                            // Store for later init
                            window.liquidityData = chartData;
                        }
                    } else {
                         valSpan.innerText = "N/A";
                    }
                }
            } catch (e) {
                console.error("Liquidity fetch error", e);
                valSpan.innerText = "Error";
            }
        }

        function initChart() {
             if (!window.liquidityData) return;

             const container = document.getElementById('chart-container');
             container.innerHTML = ''; // Clear

             chart = LightweightCharts.createChart(container, {
                width: container.clientWidth,
                height: 400,
                layout: {
                    background: { color: '#ffffff' },
                    textColor: '#333',
                },
                grid: {
                    vertLines: { color: '#f0f3fa' },
                    horzLines: { color: '#f0f3fa' },
                },
                rightPriceScale: {
                    scaleMargins: {
                        top: 0.1,
                        bottom: 0.1,
                    },
                },
                timeScale: {
                    borderColor: '#D1D4DC',
                },
            });

            lineSeries = chart.addLineSeries({
                color: '#0d6efd',
                lineWidth: 2,
            });

            lineSeries.setData(window.liquidityData);
            chart.timeScale().fitContent();

            // Handle resize
            new ResizeObserver(entries => {
                if (entries.length === 0 || entries[0].target !== container) { return; }
                const newRect = entries[0].contentRect;
                chart.applyOptions({ width: newRect.width, height: newRect.height });
            }).observe(container);
        }

        async function loadHistoryDates() {
            const select = document.getElementById('historySelect');
            try {
                const res = await fetch('/api/history');
                if (res.ok) {
                    const data = await res.json();
                    select.innerHTML = '';

                    // Add "Today (Live)" option
                    const liveOpt = document.createElement('option');
                    liveOpt.value = "";
                    liveOpt.text = "⚡ 今日 (即時)";
                    select.appendChild(liveOpt);

                    if (data.dates && data.dates.length > 0) {
                        data.dates.forEach(date => {
                            const opt = document.createElement('option');
                            opt.value = date;
                            opt.text = date;
                            select.appendChild(opt);
                        });

                        // Default to latest history date
                        select.value = data.dates[0];
                        handleDateChange();
                    } else {
                        // If no history, select the Live option
                        select.value = "";
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

            // Always ensure checkboxes are enabled
            document.querySelectorAll('input[type=checkbox]').forEach(el => el.disabled = false);
            document.getElementById('generateBtn').style.display = 'inline-block';

            await loadArticlesList(date);

            // Important: Use false to prevent triggering live generation logic
            fetchSummary(false);
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

                            // Map source names for display and color
                            const s = art.source.toLowerCase();
                            if(s.includes('cnyes')) sourceColor = '#dc3545';
                            else if(s.includes('blocktempo')) { sourceColor = '#fd7e14'; displaySource = '動區'; }
                            else if(s.includes('anduril')) { sourceColor = '#0d6efd'; displaySource = 'FOX'; }
                            else if(s.includes('fox')) { sourceColor = '#0d6efd'; displaySource = 'FOX'; }
                            else if(s.includes('cnbc')) sourceColor = '#20c997';
                            else if(s.includes('seekingalpha')) sourceColor = '#ffc107';
                            else if(s.includes('marketwatch')) sourceColor = '#6610f2';
                            else if(s.includes('bbc')) sourceColor = '#b80000';
                            else if(s.includes('cnn')) sourceColor = '#cc0000';
                            else if(s.includes('reuters')) sourceColor = '#ff8000';
                            else if(s.includes('nyt')) sourceColor = '#000000';
                            else if(s.includes('techcrunch')) sourceColor = '#00a562';
                            else if(s.includes('forbes')) sourceColor = '#333333';
                            else if(s.includes('axios')) sourceColor = '#2251ff';
                            else if(s.includes('businessinsider')) sourceColor = '#1c1c1c';

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

        function formatMarkdownWithBadges(markdown) {
            // Function to replace [Source] with <span class="badge">Source</span>
            // Matches [Source] at the start of ### or lines
            // e.g., ### [鉅亨網] -> ### <span class="article-source source-cnyes">鉅亨網</span>

            if (!markdown) return "";

            // --- Remove "Maker Checker" Self-Check List ---
            // Finds the self-check section and truncates everything after it.
            const makerCheckerRegex = /\*\*自我檢查清單/;
            const splitIndex = markdown.search(makerCheckerRegex);
            if (splitIndex !== -1) {
                markdown = markdown.substring(0, splitIndex);
            }
            // ----------------------------------------------

            // Mapping for classes
            const getSourceClass = (src) => {
                const s = src.toLowerCase();
                if(s.includes('cnyes') || s.includes('鉅亨')) return 'source-cnyes';
                if(s.includes('blocktempo') || s.includes('動區')) return 'source-blocktempo';
                if(s.includes('anduril') || s.includes('fox')) return 'source-anduril'; // Re-use blue style
                if(s.includes('cnbc')) return 'source-cnbc';
                if(s.includes('seeking') || s.includes('alpha')) return 'source-seekingalpha';
                if(s.includes('marketwatch')) return 'source-marketwatch';
                if(s.includes('bbc')) return 'source-bbc';
                if(s.includes('cnn')) return 'source-cnn';
                if(s.includes('reuters')) return 'source-reuters';
                if(s.includes('nyt')) return 'source-nyt';
                if(s.includes('techcrunch')) return 'source-techcrunch';
                if(s.includes('forbes')) return 'source-forbes';
                if(s.includes('axios')) return 'source-axios';
                if(s.includes('businessinsider')) return 'source-businessinsider';
                return 'source-default';
            };

            // --- Removed "Related Reports" custom chip layout to fix ### 2. rendering issue and restore standard list format ---
            // The standard markdown parser will handle "- [Source] [Title](Link)" correctly as a list item with a link.
            // This also solves the user's request to keep [Source] plain text and have clickable titles.
            // ---

            // Use simple regex to find [Any Text] inside headers ### ...
            // We assume AI follows "### [Source] Title"
            markdown = markdown.replace(/###\s*\[(.*?)\]/g, (match, sourceName) => {
                const cls = getSourceClass(sourceName);
                return `### <span class="article-source ${cls}">${sourceName}</span>`;
            });

            // Also replace bold sources in lists: - **[Source]** Title
            markdown = markdown.replace(/-\s*\*\*\[(.*?)\]\*\*/g, (match, sourceName) => {
                const cls = getSourceClass(sourceName);
                return `- <span class="article-source ${cls}">${sourceName}</span>`;
            });

            return markdown;
        }

        async function fetchSummary(forceLive = false) {
            const btn = document.getElementById('generateBtn');
            const statusText = document.getElementById('status-text');
            const content = document.getElementById('content');
            let historyDate = document.getElementById('historySelect').value;

            // If user clicked "Update", we force reset to today and trigger refresh
            if (forceLive) {
                document.getElementById('historySelect').value = "";
                historyDate = "";
                document.querySelectorAll('input[type=checkbox]').forEach(el => el.disabled = false);
                document.getElementById('generateBtn').style.display = 'inline-block';
            }

            const checkboxes = document.querySelectorAll('.source-checkboxes input:checked');
            const sources = Array.from(checkboxes).map(cb => cb.value).join(',');

            if (!historyDate && sources.length === 0) {
                showToast("請至少選擇一個新聞來源！", "error");
                return;
            }

            btn.disabled = true;
            content.style.opacity = '0.5';

            // Initial Status
            if (forceLive) {
                updateProgress(0, "準備開始...");
            } else {
                statusText.innerHTML = `<span class="loader"></span> 正在讀取摘要...`;
            }

            try {
                let url = '/api/summarize';
                const params = new URLSearchParams();

                if (historyDate) {
                    params.append('date', historyDate);
                } else {
                    if (sources) params.append('sources', sources);
                    if (forceLive) params.append('refresh', 'true');
                }

                const res = await fetch(`${url}?${params.toString()}`);

                if (res.status === 404) {
                    if (historyDate) {
                         content.innerHTML = '<div style="text-align: center; margin-top: 50px;"><h3>⚠️ 尚無存檔</h3><p>此日期沒有歷史摘要紀錄。</p></div>';
                    } else {
                         content.innerHTML = '<div style="text-align: center; margin-top: 50px;"><h3>⚠️ 尚無摘要</h3><p>今日尚未生成摘要，請點擊右上方「更新今日摘要」按鈕。</p></div>';
                    }
                    hideProgress();
                    return;
                }

                // If content-type is text/event-stream, handle streaming
                const contentType = res.headers.get("content-type");
                if (contentType && contentType.includes("text/event-stream")) {
                    const reader = res.body.getReader();
                    const decoder = new TextDecoder();
                    let buffer = "";

                    while (true) {
                        const { done, value } = await reader.read();
                        if (done) break;
                        const chunk = decoder.decode(value, { stream: true });
                        buffer += chunk;

                        // Split by double newline to get events
                        const parts = buffer.split("\n\n");
                        buffer = parts.pop(); // Keep last incomplete part

                        for (const part of parts) {
                            if (part.startsWith("data: ")) {
                                const jsonStr = part.substring(6);
                                try {
                                    const data = JSON.parse(jsonStr);
                                    if (data.status) {
                                        // Update Progress Bar
                                        updateProgress(data.step, data.status);
                                    } else if (data.markdown) {
                                        // Final Result
                                        updateProgress(4, "完成！");
                                        const processedMarkdown = formatMarkdownWithBadges(data.markdown);
                                        content.innerHTML = marked.parse(processedMarkdown);

                                        showToast(`✅ 更新成功 (來源: ${data.source === 'cache' ? '資料庫' : '即時'})`, "success");
                                        setTimeout(hideProgress, 2000);
                                    } else if (data.error) {
                                        showToast(`❌ ${data.error}`, "error");
                                        content.innerHTML = `<p style="color:red">錯誤: ${data.details}</p>`;
                                        hideProgress();
                                    }
                                } catch (e) {
                                    console.error("Parse error", e);
                                }
                            }
                        }
                    }

                } else {
                    // Standard JSON response (cached)
                    const data = await res.json();
                    if (data.markdown) {
                        const processedMarkdown = formatMarkdownWithBadges(data.markdown);
                        content.innerHTML = marked.parse(processedMarkdown);
                        statusText.innerHTML = ""; // Clear loader
                        showToast(`✅ 讀取成功`, "success");
                    } else {
                        showToast('❌ 發生錯誤', "error");
                    }
                }

                if (forceLive) {
                    await loadArticlesList("");
                }

            } catch (error) {
                console.error(error);
                showToast(`❌ 連線錯誤: ${error.message}`, "error");
                hideProgress();
            } finally {
                btn.disabled = false;
                content.style.opacity = '1';
            }
        }
    </script>
</body>
</html>"""

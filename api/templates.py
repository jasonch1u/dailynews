# This file contains the HTML template for the frontend.
# It is separated from the main logic for better maintainability.

HTML_CONTENT = r"""<!DOCTYPE html>
<html lang="zh-TW">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>每日新聞 AI 摘要</title>
    <link rel="icon" href="data:image/svg+xml,<svg xmlns=%22http://www.w3.org/2000/svg%22 viewBox=%220 0 100 100%22><text y=%22.9em%22 font-size=%2290%22>📰</text></svg>">
    <!-- Use marked.js for Markdown rendering -->
    <script src="https://cdn.jsdelivr.net/npm/marked/marked.min.js"></script>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f8f9fa;
            color: #333;
        }
        header {
            text-align: center;
            margin-bottom: 30px;
        }
        h1 {
            color: #2c3e50;
            margin-bottom: 10px;
        }
        .controls {
            display: flex;
            flex-direction: column;
            align-items: center;
            gap: 15px;
            margin-bottom: 20px;
        }
        .action-row {
            display: flex;
            gap: 10px;
            flex-wrap: wrap;
            justify-content: center;
            align-items: center;
        }
        select {
            padding: 10px;
            font-size: 16px;
            border-radius: 4px;
            border: 1px solid #ced4da;
            background-color: white;
            min-width: 150px;
        }
        button {
            background-color: #0d6efd;
            color: white;
            border: none;
            padding: 12px 24px;
            font-size: 16px;
            border-radius: 4px;
            cursor: pointer;
            transition: background-color 0.2s;
        }
        button:hover {
            background-color: #0b5ed7;
        }
        button:disabled {
            background-color: #6c757d;
            cursor: not-allowed;
        }
        #status {
            text-align: center;
            margin: 10px 0;
            font-weight: bold;
            color: #666;
            min-height: 24px;
        }
        #content {
            background: white;
            padding: 30px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            line-height: 1.6;
        }
        #content a {
            color: #0d6efd;
            text-decoration: none;
        }
        #content a:hover {
            text-decoration: underline;
        }
        .download-btn {
            display: none; /* Hidden by default */
            margin-top: 20px;
            background-color: #198754;
        }
        .download-btn:hover {
            background-color: #157347;
        }
        .loader {
            border: 4px solid #f3f3f3;
            border-top: 4px solid #0d6efd;
            border-radius: 50%;
            width: 20px;
            height: 20px;
            animation: spin 1s linear infinite;
            display: inline-block;
            vertical-align: middle;
            margin-right: 10px;
        }
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
        .date-badge {
            display: inline-block;
            background: #e9ecef;
            padding: 4px 8px;
            border-radius: 12px;
            font-size: 0.85em;
            color: #495057;
            margin-top: 5px;
        }
    </style>
</head>
<body>
    <header>
        <h1>📰 每日新聞 AI 摘要服務</h1>
        <p>自動抓取 Anduril, BlockTempo, 鉅亨網 的最新新聞並生成重點摘要。</p>
    </header>

    <div class="controls">
        <div class="action-row">
             <button id="generateBtn" onclick="fetchSummary()">🚀 生成/查看今日摘要</button>
        </div>

        <div class="action-row">
            <label for="historySelect">📅 歷史回顧：</label>
            <select id="historySelect" onchange="loadHistory()">
                <option value="">-- 載入中 --</option>
            </select>
        </div>

        <div id="status"></div>
    </div>

    <div id="content">
        <p style="text-align: center; color: #888;">點擊按鈕查看摘要...</p>
    </div>

    <div style="text-align: center;">
        <button id="downloadBtn" class="download-btn" onclick="downloadMarkdown()">📥 下載 Markdown 報告</button>
    </div>

    <script>
        let currentMarkdown = "";
        let currentDate = "";

        // Load history dates on page load
        window.addEventListener('DOMContentLoaded', async () => {
            const select = document.getElementById('historySelect');
            try {
                const response = await fetch('/api/history');
                if (response.ok) {
                    const data = await response.json();
                    select.innerHTML = '<option value="">-- 選擇日期 --</option>';
                    if (data.dates && data.dates.length > 0) {
                        data.dates.forEach(date => {
                            const option = document.createElement('option');
                            option.value = date;
                            option.text = date;
                            select.appendChild(option);
                        });
                    } else {
                        select.innerHTML = '<option value="">-- 尚無歷史資料 --</option>';
                    }
                }
            } catch (e) {
                console.error("Failed to load history", e);
                select.innerHTML = '<option value="">-- 無法載入歷史 --</option>';
            }
        });

        async function loadHistory() {
            const select = document.getElementById('historySelect');
            const date = select.value;
            if (date) {
                fetchSummary(date);
            }
        }

        async function fetchSummary(targetDate = null) {
            const btn = document.getElementById('generateBtn');
            const status = document.getElementById('status');
            const content = document.getElementById('content');
            const downloadBtn = document.getElementById('downloadBtn');

            btn.disabled = true;
            downloadBtn.style.display = 'none';

            let statusMsg = targetDate ? `正在載入 ${targetDate} 的摘要...` : '正在抓取新聞並進行 AI 摘要，這可能需要幾秒鐘...';
            status.innerHTML = `<span class="loader"></span> ${statusMsg}`;
            content.innerHTML = '';

            try {
                let url = '/api/summarize';
                if (targetDate) {
                    url += `?date=${targetDate}`;
                }

                const response = await fetch(url);

                // Handle 404 specially
                if (response.status === 404) {
                     status.innerHTML = '⚠️ 查無資料';
                     content.innerHTML = '<p style="text-align:center; color: #888;">找不到該日期的摘要資料。</p>';
                     return;
                }

                if (!response.ok) {
                    throw new Error(`HTTP error! status: ${response.status}`);
                }

                const data = await response.json();

                if (data.markdown) {
                    currentMarkdown = data.markdown;
                    currentDate = data.date || new Date().toISOString().split('T')[0];
                    content.innerHTML = marked.parse(data.markdown);
                    status.innerHTML = `✅ ${currentDate} 摘要載入完成！`;
                    status.style.color = 'green';
                    downloadBtn.style.display = 'inline-block';
                } else {
                    status.innerHTML = '❌ 未能生成摘要。';
                    status.style.color = 'red';
                }

            } catch (error) {
                console.error('Error:', error);
                status.innerHTML = `❌ 發生錯誤: ${error.message}`;
                status.style.color = 'red';
                content.innerHTML = `<p style="color: red;">請求失敗，請稍後再試。<br>錯誤訊息: ${error.message}</p>`;
            } finally {
                btn.disabled = false;
            }
        }

        function downloadMarkdown() {
            if (!currentMarkdown) return;

            const filename = `Daily_News_${currentDate}.md`;

            const blob = new Blob([currentMarkdown], { type: 'text/markdown' });
            const url = URL.createObjectURL(blob);

            const a = document.createElement('a');
            a.href = url;
            a.download = filename;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            URL.revokeObjectURL(url);
        }
    </script>
</body>
</html>"""

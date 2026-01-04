import requests
from bs4 import BeautifulSoup
import time
from datetime import datetime

# 設定更完整的偽裝 Headers
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "zh-TW,zh;q=0.9,en-US;q=0.8,en;q=0.7",
    "Referer": "https://www.google.com/"
}

# ================= 輔助偵錯函式 =================
def check_response(site_name, response, articles, skipped_count=0):
    """檢查回應狀態並印出診斷訊息"""
    status = response.status_code
    print(f"   [{site_name}] 狀態碼: {status}")

    if status == 403:
        print(f"   ❌ {site_name} 拒絕訪問 (403 Forbidden)。通常是因為網站擋住了程式爬蟲。")
    elif status != 200:
        print(f"   ⚠️ {site_name} 回傳異常狀態碼: {status}")
    elif len(articles) == 0:
        if skipped_count > 0:
            print(f"   ⚠️ {site_name} 連線成功，但有 {skipped_count} 篇文章因日期不符而被過濾。")
        else:
            print(f"   ⚠️ {site_name} 連線成功 (200 OK) 但找不到文章。")
            # 檢查是否遇到 Cloudflare 驗證頁面
            if "Just a moment" in response.text or "Cloudflare" in response.text:
                print("      偵測到 Cloudflare 驗證頁面，爬蟲被攔截。")
            else:
                print("      可能是網站改版導致抓取規則失效，或內容由 JavaScript 動態載入。")
    else:
        print(f"   ✅ {site_name} 成功抓取 {len(articles)} 篇" + (f" (另過濾掉 {skipped_count} 篇非今日新聞)" if skipped_count > 0 else ""))

def get_article_content(url, check_date=False):
    """進入文章連結抓取內文，可選擇是否檢查日期"""
    try:
        # 稍微延遲避免被網站擋 (Rate Limiting)
        time.sleep(0.5)
        response = requests.get(url, headers=HEADERS, timeout=5)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 如果需要檢查日期 (針對無法在列表頁取得日期的網站)
            if check_date:
                today_str = datetime.now().strftime("%Y-%m-%d")
                # 嘗試尋找常見的發布時間 meta tag
                meta_date = soup.find('meta', property='article:published_time') or \
                            soup.find('meta', property='og:updated_time') or \
                            soup.find('meta', itemprop='datePublished')
                
                # 如果有找到日期標籤，且日期不是今天，則跳過 (回傳 None)
                # 若 content 屬性包含今天的日期字串 (例如 "2026-01-04T...") 則視為通過
                if meta_date and meta_date.get('content') and not meta_date.get('content').startswith(today_str):
                    return None

            # 抓取所有段落文字，並過濾掉太短的雜訊
            paragraphs = soup.find_all('p')
            content = "\n".join([p.text.strip() for p in paragraphs if len(p.text.strip()) > 20])
            return content[:1000] + "..." if len(content) > 1000 else content
    except Exception:
        pass
    return "(無法抓取內文，僅提供標題)"

# ================= 爬蟲功能函式 =================

def fetch_anduril_tw():
    """爬取 Anduril.tw"""
    url = "https://www.anduril.tw"
    articles = []
    today_str = datetime.now().strftime("%Y-%m-%d")
    skipped_count = 0

    try:
        print(f"正在連線: {url} ...")
        response = requests.get(url, headers=HEADERS, timeout=10)

        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            # 使用新的結構抓取：卡片連結與日期
            cards = soup.find_all('article', class_='gh-card')
            
            for card in cards:
                # 1. 日期過濾 (Anduril 列表頁有日期，直接檢查效率較高)
                time_tag = card.find('time')
                if time_tag and time_tag.get('datetime') != today_str:
                    skipped_count += 1
                    continue # 非今日新聞，跳過

                link_tag = card.find('a', class_='gh-card-link')
                title_tag = card.find('h3', class_='gh-card-title')

                if link_tag and title_tag:
                    title = title_tag.text.strip()
                    link = link_tag.get('href')
                    
                    if len(title) > 0:
                        if not link.startswith('http'):
                            link = url + link if link.startswith('/') else url + '/' + link
                        if not any(d in link for d in ["tag", "category", "author"]):
                             content = get_article_content(link, check_date=False) # 列表頁已檢查過日期
                             articles.append(f"標題: {title}\n連結: {link}\n內文: {content}\n出處: FOX")
                if len(articles) >= 5: break

        check_response("Anduril", response, articles, skipped_count)

    except Exception as e:
        print(f"Anduril 連線失敗: {e}")
    return articles

def fetch_blocktempo():
    """爬取 BlockTempo (動區動趨)"""
    url = "https://www.blocktempo.com/2026/"
    articles = []
    skipped_count = 0
    try:
        print(f"正在連線: {url} ...")
        response = requests.get(url, headers=HEADERS, timeout=10)

        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            candidates = soup.find_all('h3')
            for item in candidates:
                link_tag = item.find('a')
                if link_tag and link_tag.get('href'):
                    title = link_tag.get('title') or link_tag.text.strip()
                    link = link_tag.get('href')
                    if title and len(title) > 5:
                        # BlockTempo 列表頁日期較難解析，進入內文檢查
                        content = get_article_content(link, check_date=True)
                        if content: # 如果 content 不為 None，代表是今天的新聞
                            articles.append(f"標題: {title}\n連結: {link}\n內文: {content}\n出處: 動區")
                        else:
                            skipped_count += 1
                if len(articles) >= 5: break

        check_response("BlockTempo", response, articles, skipped_count)

    except Exception as e:
        print(f"BlockTempo 連線失敗: {e}")
    return articles

def fetch_cnyes_stock():
    """爬取鉅亨網"""
    url = "https://m.cnyes.com/news/cat/wd_stock"
    articles = []
    skipped_count = 0
    try:
        print(f"正在連線: {url} ...")
        response = requests.get(url, headers=HEADERS, timeout=10)

        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            links = soup.find_all('a', href=True)
            seen_links = set()
            for a in links:
                href = a['href']
                title = a.text.strip()
                if "/news/id/" in href and len(title) > 5:
                    if not href.startswith('http'):
                        href = "https://m.cnyes.com" + href
                    if href not in seen_links:
                        # 鉅亨網進入內文檢查日期
                        content = get_article_content(href, check_date=True)
                        if content:
                            articles.append(f"標題: {title}\n連結: {href}\n內文: {content}\n出處: 鉅亨網")
                            seen_links.add(href)
                        else:
                            skipped_count += 1
                if len(articles) >= 5: break

        check_response("鉅亨網", response, articles, skipped_count)

    except Exception as e:
        print(f"鉅亨網連線失敗: {e}")
    return articles
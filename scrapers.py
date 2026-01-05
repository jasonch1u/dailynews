import aiohttp
import asyncio
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

async def fetch_url(session, url):
    """Async fetch url"""
    try:
        async with session.get(url, headers=HEADERS, timeout=10) as response:
            if response.status == 200:
                return await response.text()
    except Exception as e:
        print(f"Error fetching {url}: {e}")
    return None

async def get_article_content_async(session, url, check_date=False):
    """進入文章連結抓取內文，可選擇是否檢查日期 (Async version)"""
    try:
        # 稍微延遲避免被網站擋 (Rate Limiting) - In async we might not need explicit sleep, but keep it small if needed
        # await asyncio.sleep(0.1)
        html = await fetch_url(session, url)
        if html:
            soup = BeautifulSoup(html, 'html.parser')
            
            # 如果需要檢查日期
            if check_date:
                today_str = datetime.now().strftime("%Y-%m-%d")
                meta_date = soup.find('meta', property='article:published_time') or \
                            soup.find('meta', property='og:updated_time') or \
                            soup.find('meta', itemprop='datePublished')
                
                if meta_date and meta_date.get('content') and not meta_date.get('content').startswith(today_str):
                    return None

            paragraphs = soup.find_all('p')
            content = "\n".join([p.text.strip() for p in paragraphs if len(p.text.strip()) > 20])
            return content[:1000] + "..." if len(content) > 1000 else content
    except Exception:
        pass
    return "(無法抓取內文，僅提供標題)"

async def fetch_anduril_tw(session):
    """爬取 Anduril.tw"""
    url = "https://www.anduril.tw"
    articles = []
    today_str = datetime.now().strftime("%Y-%m-%d")

    try:
        print(f"正在連線: {url} ...")
        html = await fetch_url(session, url)
        if html:
            soup = BeautifulSoup(html, 'html.parser')
            cards = soup.find_all('article', class_='gh-card')
            
            tasks = []
            valid_cards = []

            for card in cards:
                time_tag = card.find('time')
                if time_tag and time_tag.get('datetime') != today_str:
                    continue

                link_tag = card.find('a', class_='gh-card-link')
                title_tag = card.find('h3', class_='gh-card-title')

                if link_tag and title_tag:
                    title = title_tag.text.strip()
                    link = link_tag.get('href')
                    
                    if len(title) > 0:
                        if not link.startswith('http'):
                            link = url + link if link.startswith('/') else url + '/' + link
                        if not any(d in link for d in ["tag", "category", "author"]):
                            valid_cards.append((title, link))

                if len(valid_cards) >= 5: break

            # Concurrent fetch for content
            for title, link in valid_cards:
                 tasks.append(get_article_content_async(session, link, check_date=False))

            contents = await asyncio.gather(*tasks)

            for i, content in enumerate(contents):
                title, link = valid_cards[i]
                articles.append(f"標題: {title}\n連結: {link}\n內文: {content}\n出處: FOX")

    except Exception as e:
        print(f"Anduril 連線失敗: {e}")
    return articles

async def fetch_blocktempo(session):
    """爬取 BlockTempo (動區動趨)"""
    url = "https://www.blocktempo.com/2026/"
    articles = []
    try:
        print(f"正在連線: {url} ...")
        html = await fetch_url(session, url)

        if html:
            soup = BeautifulSoup(html, 'html.parser')
            candidates = soup.find_all('h3')

            tasks = []
            potential_articles = [] # List of (title, link)

            for item in candidates:
                link_tag = item.find('a')
                if link_tag and link_tag.get('href'):
                    title = link_tag.get('title') or link_tag.text.strip()
                    link = link_tag.get('href')
                    if title and len(title) > 5:
                        potential_articles.append((title, link))
                if len(potential_articles) >= 5: break

            # Concurrent fetch for content
            for title, link in potential_articles:
                tasks.append(get_article_content_async(session, link, check_date=True))

            contents = await asyncio.gather(*tasks)

            for i, content in enumerate(contents):
                if content: # Check date passes
                    title, link = potential_articles[i]
                    articles.append(f"標題: {title}\n連結: {link}\n內文: {content}\n出處: 動區")

    except Exception as e:
        print(f"BlockTempo 連線失敗: {e}")
    return articles

async def fetch_cnyes_stock(session):
    """爬取鉅亨網"""
    url = "https://m.cnyes.com/news/cat/wd_stock"
    articles = []
    try:
        print(f"正在連線: {url} ...")
        html = await fetch_url(session, url)

        if html:
            soup = BeautifulSoup(html, 'html.parser')
            links = soup.find_all('a', href=True)

            tasks = []
            potential_articles = []
            seen_links = set()

            for a in links:
                href = a['href']
                title = a.text.strip()
                if "/news/id/" in href and len(title) > 5:
                    if not href.startswith('http'):
                        href = "https://m.cnyes.com" + href
                    if href not in seen_links:
                        seen_links.add(href)
                        potential_articles.append((title, href))
                if len(potential_articles) >= 5: break

            for title, href in potential_articles:
                tasks.append(get_article_content_async(session, href, check_date=True))

            contents = await asyncio.gather(*tasks)

            for i, content in enumerate(contents):
                if content:
                    title, href = potential_articles[i]
                    articles.append(f"標題: {title}\n連結: {href}\n內文: {content}\n出處: 鉅亨網")

    except Exception as e:
        print(f"鉅亨網連線失敗: {e}")
    return articles

async def run_all_scrapers():
    async with aiohttp.ClientSession() as session:
        results = await asyncio.gather(
            fetch_anduril_tw(session),
            fetch_blocktempo(session),
            fetch_cnyes_stock(session)
        )
        # Flatten the list of lists
        return [item for sublist in results for item in sublist]

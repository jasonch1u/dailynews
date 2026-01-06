import aiohttp
import asyncio
from bs4 import BeautifulSoup
import time
from datetime import datetime, timezone, timedelta

# 設定更完整的偽裝 Headers
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "zh-TW,zh;q=0.9,en-US;q=0.8,en;q=0.7",
    "Referer": "https://www.google.com/"
}

TZ_TW = timezone(timedelta(hours=8))

def get_tw_now():
    """Get current time in Taiwan Timezone"""
    return datetime.now(TZ_TW)

def is_today_tw(date_iso_str):
    """Check if an ISO date string corresponds to Today in Taiwan"""
    if not date_iso_str:
        return False
    try:
        # Handle Z for UTC
        if date_iso_str.endswith('Z'):
            date_iso_str = date_iso_str.replace('Z', '+00:00')

        # Parse ISO format
        dt = datetime.fromisoformat(date_iso_str)

        # Convert to TW time
        dt_tw = dt.astimezone(TZ_TW)
        now_tw = get_tw_now()

        return dt_tw.date() == now_tw.date()
    except Exception as e:
        # Fallback to simple string check if parsing fails (though risky)
        # print(f"Date parse error: {e} for {date_iso_str}")
        return False

async def fetch_url(session, url):
    """Async fetch url"""
    try:
        async with session.get(url, headers=HEADERS, timeout=aiohttp.ClientTimeout(total=15)) as response:
            if response.status == 200:
                return await response.text()
    except Exception as e:
        print(f"Error fetching {url}: {e}")
    return None

async def get_article_content_async(session, url, content_selector=None, check_date=False):
    """
    Fetch article content with configurable selector logic.
    content_selector: specific CSS selector for the main content (e.g., 'div.post-content').
    If None, falls back to heuristics.
    """
    try:
        html = await fetch_url(session, url)
        if html:
            soup = BeautifulSoup(html, 'html.parser')
            
            # Date Check Logic
            if check_date:
                is_valid_date = False
                # 1. Try <time> tag
                time_tag = soup.find('time')
                if time_tag and time_tag.get('datetime'):
                    if is_today_tw(time_tag.get('datetime')):
                        is_valid_date = True
                
                # 2. Try Meta tags
                if not is_valid_date:
                    meta_date = soup.find('meta', property='article:published_time') or \
                                soup.find('meta', property='og:updated_time') or \
                                soup.find('meta', itemprop='datePublished')

                    if meta_date and meta_date.get('content'):
                        content_date = meta_date.get('content')
                        if "T" in content_date:
                             if is_today_tw(content_date):
                                 is_valid_date = True
                        else:
                             today_str = get_tw_now().strftime("%Y-%m-%d")
                             if content_date.startswith(today_str):
                                 is_valid_date = True

                if not is_valid_date:
                    return None

            # Content Extraction Logic
            target_container = None
            if content_selector:
                target_container = soup.select_one(content_selector)

            # Fallback heuristics if selector failed or not provided
            if not target_container:
                target_container = soup.find('main') or soup

            paragraphs = target_container.find_all('p')
            content = "\n".join([p.text.strip() for p in paragraphs if len(p.text.strip()) > 10])

            return content[:1500] + "..." if len(content) > 1500 else content
    except Exception:
        pass
    return None

async def fetch_anduril_tw(session, db_logger=None):
    """爬取 Anduril.tw (Selector: .post-content or similar)"""
    url = "https://www.anduril.tw"
    articles = []
    today_str = get_tw_now().strftime("%Y-%m-%d")

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

            # For Anduril (Ghost blog), content is usually in section.gh-content
            for title, link in valid_cards:
                 tasks.append(get_article_content_async(session, link, content_selector='section.gh-content', check_date=False))

            contents = await asyncio.gather(*tasks)

            for i, content in enumerate(contents):
                if content:
                    title, link = valid_cards[i]
                    articles.append(f"標題: {title}\n連結: {link}\n內文: {content}\n出處: FOX")
    except Exception as e:
        print(f"Anduril 連線失敗: {e}")
        if db_logger: await db_logger("scraper:anduril", str(e))
    return articles

async def fetch_blocktempo(session, db_logger=None):
    """爬取 BlockTempo (Selector: .entry-content)"""
    url = "https://www.blocktempo.com/2026/"
    articles = []
    try:
        print(f"正在連線: {url} ...")
        html = await fetch_url(session, url)

        if html:
            soup = BeautifulSoup(html, 'html.parser')
            candidates = soup.find_all('h3')

            tasks = []
            potential_articles = []

            for item in candidates:
                link_tag = item.find('a')
                if link_tag and link_tag.get('href'):
                    title = link_tag.get('title') or link_tag.text.strip()
                    link = link_tag.get('href')
                    if title and len(title) > 5:
                        potential_articles.append((title, link))
                if len(potential_articles) >= 5: break

            for title, link in potential_articles:
                # BlockTempo usually puts content in .entry-content
                tasks.append(get_article_content_async(session, link, content_selector='.entry-content', check_date=True))

            contents = await asyncio.gather(*tasks)

            for i, content in enumerate(contents):
                if content:
                    title, link = potential_articles[i]
                    articles.append(f"標題: {title}\n連結: {link}\n內文: {content}\n出處: 動區")
    except Exception as e:
        print(f"BlockTempo 連線失敗: {e}")
        if db_logger: await db_logger("scraper:blocktempo", str(e))
    return articles

async def fetch_cnyes_stock(session, db_logger=None):
    """爬取鉅亨網 (Selector: main)"""
    url = "https://news.cnyes.com/news/cat/wd_stock_all"
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
                title = a.get('title') or a.text.strip()

                if not title:
                    title_div = a.find('div', title=True)
                    if title_div: title = title_div.get('title')
                if not title:
                    title_p = a.find('p', class_='news-title')
                    if title_p: title = title_p.text.strip()

                if "/news/id/" in href and title and len(title) > 5:
                    if not href.startswith('http'):
                        href = "https://news.cnyes.com" + href
                    if href not in seen_links:
                        seen_links.add(href)
                        potential_articles.append((title, href))
                if len(potential_articles) >= 5: break

            for title, href in potential_articles:
                # Cnyes puts content in <main>
                tasks.append(get_article_content_async(session, href, content_selector='main', check_date=True))

            contents = await asyncio.gather(*tasks)

            for i, content in enumerate(contents):
                if content:
                    title, href = potential_articles[i]
                    articles.append(f"標題: {title}\n連結: {href}\n內文: {content}\n出處: 鉅亨網")
    except Exception as e:
        print(f"鉅亨網連線失敗: {e}")
        if db_logger: await db_logger("scraper:cnyes", str(e))
    return articles

async def run_all_scrapers(db_logger=None):
    """
    Run all scrapers concurrently and return combined list.
    Order matches the gather order: Anduril -> BlockTempo -> Cnyes.
    """
    async with aiohttp.ClientSession() as session:
        # Results is a list of lists: [[anduril_items], [blocktempo_items], [cnyes_items]]
        results = await asyncio.gather(
            fetch_anduril_tw(session, db_logger),
            fetch_blocktempo(session, db_logger),
            fetch_cnyes_stock(session, db_logger)
        )
        # Flatten the list while preserving order
        return [item for sublist in results for item in sublist]

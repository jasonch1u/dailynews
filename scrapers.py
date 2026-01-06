import aiohttp
import asyncio
from bs4 import BeautifulSoup
import time
from datetime import datetime, timezone, timedelta

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "zh-TW,zh;q=0.9,en-US;q=0.8,en;q=0.7",
    "Referer": "https://www.google.com/"
}

TZ_TW = timezone(timedelta(hours=8))

def get_tw_now():
    return datetime.now(TZ_TW)

def get_today_str():
    return get_tw_now().strftime("%Y-%m-%d")

def is_today_tw(date_iso_str):
    if not date_iso_str: return False
    try:
        if date_iso_str.endswith('Z'): date_iso_str = date_iso_str.replace('Z', '+00:00')
        dt = datetime.fromisoformat(date_iso_str).astimezone(TZ_TW)
        return dt.date() == get_tw_now().date()
    except:
        return False

async def fetch_url_with_retry(session, url, retries=2):
    """Fetch URL with retry mechanism."""
    for i in range(retries + 1):
        try:
            async with session.get(url, headers=HEADERS, timeout=aiohttp.ClientTimeout(total=15)) as response:
                if response.status == 200:
                    return await response.text()
                elif response.status == 404:
                    return None # Don't retry 404
        except Exception as e:
            if i == retries:
                print(f"Failed to fetch {url} after {retries} retries: {e}")
            else:
                await asyncio.sleep(1) # Wait 1s before retry
    return None

async def process_article_link(session, db, title, link, source, content_selector, check_date=False):
    """
    Process a single article link:
    1. Check DB for content.
    2. If miss, scrape.
    3. Save to DB.
    4. Return formatted string.
    """
    # 1. Check DB
    if db:
        cached = await db.get_article(link)
        if cached:
            return f"標題: {title}\n連結: {link}\n內文: {cached['content']}\n出處: {source} (Cached)"

    # 2. Scrape
    try:
        html = await fetch_url_with_retry(session, link)
        if html:
            soup = BeautifulSoup(html, 'html.parser')
            
            # Date Check (Strict)
            if check_date:
                is_valid = False
                time_tag = soup.find('time')
                if time_tag and time_tag.get('datetime') and is_today_tw(time_tag.get('datetime')):
                     is_valid = True
                
                if not is_valid:
                    # Meta tags fallback
                    for meta_prop in ['article:published_time', 'og:updated_time', 'datePublished']:
                        meta = soup.find('meta', property=meta_prop) or soup.find('meta', itemprop=meta_prop)
                        if meta and meta.get('content'):
                            c = meta.get('content')
                            if ("T" in c and is_today_tw(c)) or c.startswith(get_today_str()):
                                is_valid = True; break

                if not is_valid: return None

            # Content Extraction
            container = soup.select_one(content_selector) if content_selector else soup.find('main')
            if not container: container = soup

            text = "\n".join([p.text.strip() for p in container.find_all('p') if len(p.text.strip()) > 10])
            content = text[:2000] + "..." if len(text) > 2000 else text

            if content:
                # 3. Save to DB
                if db:
                    await db.save_article(link, title, content, source, get_today_str())

                return f"標題: {title}\n連結: {link}\n內文: {content}\n出處: {source}"
    except Exception as e:
        if db: await db.log_error(f"scraper:{source}", f"Error processing {link}: {e}")

    return None

async def fetch_anduril_tw(session, db=None):
    url = "https://www.anduril.tw"
    tasks = []

    html = await fetch_url_with_retry(session, url)
    if html:
        soup = BeautifulSoup(html, 'html.parser')
        cards = soup.find_all('article', class_='gh-card')
        for card in cards:
            if len(tasks) >= 5: break
            time_tag = card.find('time')
            if time_tag and time_tag.get('datetime') != get_today_str(): continue
            
            link_tag = card.find('a', class_='gh-card-link')
            title_tag = card.find('h3', class_='gh-card-title')

            if link_tag and title_tag:
                title = title_tag.text.strip()
                link = link_tag.get('href')
                if not link.startswith('http'): link = url + link if link.startswith('/') else url + '/' + link

                if not any(x in link for x in ["tag", "category", "author"]):
                    tasks.append(process_article_link(session, db, title, link, "Anduril", "section.gh-content", False))

    return [x for x in await asyncio.gather(*tasks) if x]

async def fetch_blocktempo(session, db=None):
    url = "https://www.blocktempo.com/2026/"
    tasks = []

    html = await fetch_url_with_retry(session, url)
    if html:
        soup = BeautifulSoup(html, 'html.parser')
        for h3 in soup.find_all('h3'):
            if len(tasks) >= 5: break
            a = h3.find('a')
            if a and a.get('href'):
                title = a.get('title') or a.text.strip()
                link = a.get('href')
                if len(title) > 5:
                    tasks.append(process_article_link(session, db, title, link, "BlockTempo", ".entry-content", True))

    return [x for x in await asyncio.gather(*tasks) if x]

async def fetch_cnyes_stock(session, db=None):
    url = "https://news.cnyes.com/news/cat/wd_stock_all"
    tasks = []

    html = await fetch_url_with_retry(session, url)
    if html:
        soup = BeautifulSoup(html, 'html.parser')
        seen = set()
        for a in soup.find_all('a', href=True):
            if len(tasks) >= 5: break
            href = a['href']
            if "/news/id/" not in href: continue

            title = a.get('title') or a.text.strip()
            if not title:
                t_div = a.find('div', title=True)
                if t_div: title = t_div.get('title')

            if title and len(title) > 5:
                if not href.startswith('http'): href = "https://news.cnyes.com" + href
                if href not in seen:
                    seen.add(href)
                    tasks.append(process_article_link(session, db, title, href, "Cnyes", "main", True))

    return [x for x in await asyncio.gather(*tasks) if x]

async def run_all_scrapers(db_client=None, sources=None):
    """
    Run scrapers based on sources list.
    sources: list of strings ['anduril', 'blocktempo', 'cnyes']
    """
    tasks = []

    # Default to all if None or empty
    if not sources:
        sources = ['anduril', 'blocktempo', 'cnyes']

    async with aiohttp.ClientSession() as session:
        if 'anduril' in sources:
            tasks.append(fetch_anduril_tw(session, db_client))
        if 'blocktempo' in sources:
            tasks.append(fetch_blocktempo(session, db_client))
        if 'cnyes' in sources:
            tasks.append(fetch_cnyes_stock(session, db_client))

        results = await asyncio.gather(*tasks)
        return [item for sublist in results for item in sublist]

import aiohttp
import asyncio
from bs4 import BeautifulSoup
import time
import os
from datetime import datetime, timezone, timedelta
from api.llm_utils import translate_text

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
                    return None
        except Exception as e:
            if i == retries:
                print(f"Failed to fetch {url}: {e}")
            else:
                await asyncio.sleep(1)
    return None

async def process_article_link(session, db, title, link, source, content_selector, check_date=False):
    """
    Process a single article link:
    1. Check DB for content.
    2. If miss, scrape.
    3. Save to DB.
    """
    if db:
        cached = await db.get_article(link)
        if cached:
            # Return DB content
            return f"### {cached['title']}\n{cached['content']}\n出處: {source}\nLink: {link}"

    try:
        html = await fetch_url_with_retry(session, link)
        if html:
            soup = BeautifulSoup(html, 'html.parser')
            
            if check_date:
                # Basic check for meta tags
                is_valid = False
                for meta_prop in ['article:published_time', 'og:updated_time', 'datePublished']:
                    meta = soup.find('meta', property=meta_prop) or soup.find('meta', itemprop=meta_prop)
                    if meta and meta.get('content'):
                        c = meta.get('content')
                        if ("T" in c and is_today_tw(c)) or c.startswith(get_today_str()):
                            is_valid = True; break
                if not is_valid: return None

            container = soup.select_one(content_selector) if content_selector else soup.find('main')
            if not container: container = soup

            text = "\n".join([p.text.strip() for p in container.find_all('p') if len(p.text.strip()) > 10])
            content = text[:2000] + "..." if len(text) > 2000 else text

            if content:
                if db:
                    await db.save_article(link, title, content, source, get_today_str())
                return f"### {title}\n{content}\n出處: {source}\nLink: {link}"
    except Exception as e:
        if db: await db.log_error(f"scraper:{source}", f"Error processing {link}: {e}")

    return None

async def fetch_rss_feed(session, db, url, source_name, translate=False):
    """
    Generic RSS Fetcher.
    Fetches RSS XML, parses items, checks DB, returns formatted string.
    translate: If True, translates titles to Traditional Chinese.
    """
    articles = []
    new_items = [] # (title, link, content) to be saved

    try:
        xml = await fetch_url_with_retry(session, url)
        if xml:
            try:
                soup = BeautifulSoup(xml, 'xml')
            except Exception:
                soup = BeautifulSoup(xml, 'html.parser')

            if not soup.find('item'):
                soup = BeautifulSoup(xml, 'html.parser')

            items = soup.find_all('item')
            for item in items[:5]: # Top 5
                title = item.title.text.strip() if item.title else "No Title"
                link = item.link.text.strip() if item.link else ""
                if not link and item.guid: link = item.guid.text.strip()

                # Check DB first
                if db:
                    cached = await db.get_article(link)
                    if cached:
                        articles.append(f"### {cached['title']}\n{cached['content']}\n出處: {source_name}\nLink: {link}")
                        continue

                description = item.description.text.strip() if item.description else ""
                desc_soup = BeautifulSoup(description, 'html.parser')
                content = desc_soup.get_text().strip()

                if content and link:
                    new_items.append({"title": title, "link": link, "content": content})

            # Batch Translate Titles if needed
            if translate and new_items:
                titles = [x['title'] for x in new_items]
                api_key = os.getenv("GEMINI_API_KEY")
                translated_titles = await translate_text(titles, api_key)

                # Update titles
                for i, t_title in enumerate(translated_titles):
                    if i < len(new_items):
                        new_items[i]['title'] = t_title

            # Save and Format
            for item in new_items:
                if db:
                    await db.save_article(item['link'], item['title'], item['content'], source_name, get_today_str())
                articles.append(f"### {item['title']}\n{item['content']}\n出處: {source_name}\nLink: {item['link']}")

    except Exception as e:
        print(f"{source_name} RSS Error: {e}")
        if db: await db.log_error(f"scraper:{source_name}", str(e))
    return articles

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

async def fetch_cnbc(session, db=None):
    # Enable Translation
    return await fetch_rss_feed(session, db, "https://search.cnbc.com/rs/search/combinedcms/view.xml?partnerId=wrss01&id=100003114", "CNBC", translate=True)

async def fetch_seeking_alpha(session, db=None):
    return await fetch_rss_feed(session, db, "https://seekingalpha.com/market_currents.xml", "SeekingAlpha", translate=True)

async def fetch_marketwatch(session, db=None):
    return await fetch_rss_feed(session, db, "https://feeds.content.dowjones.io/public/rss/mw_topstories", "MarketWatch", translate=True)

async def run_all_scrapers(db_client=None, sources=None):
    """
    Run scrapers based on sources list.
    sources: list of strings
    """
    tasks = []
    if not sources:
        sources = ['anduril', 'blocktempo', 'cnyes', 'cnbc', 'seekingalpha', 'marketwatch']

    async with aiohttp.ClientSession() as session:
        if 'anduril' in sources: tasks.append(fetch_anduril_tw(session, db_client))
        if 'blocktempo' in sources: tasks.append(fetch_blocktempo(session, db_client))
        if 'cnyes' in sources: tasks.append(fetch_cnyes_stock(session, db_client))

        # New sources
        if 'cnbc' in sources: tasks.append(fetch_cnbc(session, db_client))
        if 'seekingalpha' in sources: tasks.append(fetch_seeking_alpha(session, db_client))
        if 'marketwatch' in sources: tasks.append(fetch_marketwatch(session, db_client))

        # Use return_exceptions=True so one failure doesn't crash the whole batch
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Flatten and filter out exceptions
        valid_results = []
        for res in results:
            if isinstance(res, Exception):
                print(f"Scraper Error: {res}")
                if db_client: await db_client.log_error("scraper:aggregator", str(res))
            elif isinstance(res, list):
                valid_results.extend(res)

        return valid_results
